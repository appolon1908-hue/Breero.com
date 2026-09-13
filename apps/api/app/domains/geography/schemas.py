import re
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .models import PostalCodeImportStatus

ZIP_RE = re.compile(r"^[0-9]{5}(?:-[0-9]{4})?$")
STATE_RE = re.compile(r"^[A-Z]{2,3}$")
IANA_RE = re.compile(r"^(?:UTC|[A-Za-z_+-]+(?:/[A-Za-z0-9_+.-]+)+)$")


def normalize_postal_code(value: str) -> str:
    normalized = value.strip()
    if len(normalized) == 9 and normalized.isdigit():
        normalized = f"{normalized[:5]}-{normalized[5:]}"
    if not ZIP_RE.fullmatch(normalized):
        raise ValueError("postal code must use ZIP or ZIP+4 format")
    return normalized


def base_postal_code(value: str) -> str:
    return normalize_postal_code(value).split("-", 1)[0]


def normalize_state_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if not STATE_RE.fullmatch(normalized):
        raise ValueError("state code must contain two or three letters")
    return normalized


class Coordinates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AddressValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address_line_1: str = Field(min_length=1, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=2, max_length=3)
    postal_code: str = Field(min_length=5, max_length=10)
    country: Literal["US"] = "US"

    @field_validator("state", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> str:
        normalized = normalize_state_code(str(value))
        if normalized is None:
            raise ValueError("state is required")
        return normalized

    @field_validator("postal_code", mode="before")
    @classmethod
    def normalize_zip(cls, value: object) -> str:
        return normalize_postal_code(str(value))


class ValidatedAddressRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address_line_1: str
    address_line_2: str | None
    city: str
    county: str | None
    state: str
    postal_code: str
    postal_code_plus4: str | None
    country: str


class ServiceZoneSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    name: str
    emergency_enabled: bool


class AddressValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address_id: uuid.UUID
    address: ValidatedAddressRead
    coordinates: Coordinates
    timezone: str
    validation_status: Literal["VALID"]
    validation_source: str
    covered: bool
    service_zone: ServiceZoneSummary | None


class ServiceAreaCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    postal_code: str = Field(min_length=5, max_length=10)
    service_id: uuid.UUID
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=3)
    country: Literal["US"] = "US"

    @field_validator("postal_code", mode="before")
    @classmethod
    def normalize_zip(cls, value: object) -> str:
        return normalize_postal_code(str(value))

    @field_validator("state", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> str | None:
        return normalize_state_code(None if value is None else str(value))


class ServiceAreaCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    covered: bool
    service_zone: ServiceZoneSummary | None


class TimezoneResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class TimezoneResolveResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: str

    @field_validator("timezone")
    @classmethod
    def validate_iana_name(cls, value: str) -> str:
        if not IANA_RE.fullmatch(value):
            raise ValueError("timezone must be an IANA timezone identifier")
        return value


class ServiceZoneCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_entity_id: uuid.UUID
    name: str = Field(min_length=1, max_length=160)
    country_code: Literal["US"] = "US"
    state_code: str | None = Field(default=None, min_length=2, max_length=3)
    city: str | None = Field(default=None, max_length=120)
    postal_codes: list[str] = Field(default_factory=list, max_length=5000)
    service_ids: list[uuid.UUID] = Field(default_factory=list, max_length=500)
    center_latitude: float | None = Field(default=None, ge=-90, le=90)
    center_longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_miles: float | None = Field(default=None, gt=0, le=500)
    boundary_geojson: dict[str, Any] | None = None
    priority: int = Field(default=100, ge=0, le=10000)
    regular_service_enabled: bool = True
    emergency_enabled: bool = False
    active: bool = True

    @field_validator("state_code", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> str | None:
        return normalize_state_code(None if value is None else str(value))

    @field_validator("postal_codes", mode="before")
    @classmethod
    def normalize_zips(cls, values: object) -> list[str]:
        if not isinstance(values, list):
            raise ValueError("postal_codes must be a list")
        normalized = [normalize_postal_code(str(value)) for value in values]
        return list(dict.fromkeys(normalized))

    @field_validator("service_ids")
    @classmethod
    def unique_services(cls, values: list[uuid.UUID]) -> list[uuid.UUID]:
        return list(dict.fromkeys(values))

    @model_validator(mode="after")
    def coverage_shape(self) -> "ServiceZoneCreate":
        if (self.center_latitude is None) != (self.center_longitude is None):
            raise ValueError("center latitude and longitude must be supplied together")
        if self.radius_miles is not None and self.center_latitude is None:
            raise ValueError("radius_miles requires a center point")
        if self.center_latitude is not None and self.radius_miles is None:
            raise ValueError("center coverage requires radius_miles")
        if not (
            self.postal_codes
            or self.city
            or self.state_code
            or self.boundary_geojson
            or self.center_latitude is not None
        ):
            raise ValueError("service zone requires a geographic coverage selector")
        return self


class ServiceZoneUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    country_code: Literal["US"] | None = None
    state_code: str | None = Field(default=None, min_length=2, max_length=3)
    city: str | None = Field(default=None, max_length=120)
    postal_codes: list[str] | None = Field(default=None, max_length=5000)
    service_ids: list[uuid.UUID] | None = Field(default=None, max_length=500)
    center_latitude: float | None = Field(default=None, ge=-90, le=90)
    center_longitude: float | None = Field(default=None, ge=-180, le=180)
    clear_center: bool = False
    radius_miles: float | None = Field(default=None, gt=0, le=500)
    clear_radius: bool = False
    boundary_geojson: dict[str, Any] | None = None
    clear_boundary: bool = False
    priority: int | None = Field(default=None, ge=0, le=10000)
    regular_service_enabled: bool | None = None
    emergency_enabled: bool | None = None
    active: bool | None = None

    @field_validator("state_code", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> str | None:
        return normalize_state_code(None if value is None else str(value))

    @field_validator("postal_codes", mode="before")
    @classmethod
    def normalize_zips(cls, values: object) -> list[str] | None:
        if values is None:
            return None
        if not isinstance(values, list):
            raise ValueError("postal_codes must be a list")
        normalized = [normalize_postal_code(str(value)) for value in values]
        return list(dict.fromkeys(normalized))

    @field_validator("service_ids")
    @classmethod
    def unique_services(
        cls,
        values: list[uuid.UUID] | None,
    ) -> list[uuid.UUID] | None:
        return list(dict.fromkeys(values)) if values is not None else None

    @model_validator(mode="after")
    def validate_patch(self) -> "ServiceZoneUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one service-zone field is required")
        coordinates = {"center_latitude", "center_longitude"}
        if coordinates.intersection(self.model_fields_set) and not coordinates.issubset(
            self.model_fields_set
        ):
            raise ValueError("center latitude and longitude must be supplied together")
        if coordinates.issubset(self.model_fields_set) and (
            self.center_latitude is None or self.center_longitude is None
        ):
            raise ValueError("center latitude and longitude cannot be null")
        if self.clear_center and coordinates.intersection(self.model_fields_set):
            raise ValueError("clear_center cannot be combined with center coordinates")
        if self.clear_center and "radius_miles" in self.model_fields_set:
            raise ValueError("clear_center cannot be combined with radius_miles")
        if self.clear_radius and "radius_miles" in self.model_fields_set:
            raise ValueError("clear_radius cannot be combined with radius_miles")
        if self.clear_boundary and "boundary_geojson" in self.model_fields_set:
            raise ValueError("clear_boundary cannot be combined with boundary_geojson")
        return self


class ServiceZoneRead(BaseModel):
    id: uuid.UUID
    legal_entity_id: uuid.UUID
    name: str
    country_code: str | None
    state_code: str | None
    city: str | None
    postal_codes: list[str]
    service_ids: list[uuid.UUID]
    center: Coordinates | None
    radius_miles: float | None
    boundary_configured: bool
    priority: int
    regular_service_enabled: bool
    emergency_enabled: bool
    active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class ServiceZoneList(BaseModel):
    items: list[ServiceZoneRead]
    total: int
    page: int
    page_size: int


class PostalCodeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_area_id: uuid.UUID
    postal_code: str = Field(min_length=5, max_length=10)
    city: str | None = Field(default=None, max_length=120)
    state_code: str | None = Field(default=None, min_length=2, max_length=3)
    active: bool = True
    regular_service_enabled: bool = True
    emergency_service_enabled: bool = False
    priority: int = Field(default=100, ge=0, le=10000)

    @field_validator("postal_code", mode="before")
    @classmethod
    def normalize_zip(cls, value: object) -> str:
        return normalize_postal_code(str(value))

    @field_validator("state_code", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> str | None:
        return normalize_state_code(None if value is None else str(value))


class PostalCodeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str | None = Field(default=None, max_length=120)
    state_code: str | None = Field(default=None, min_length=2, max_length=3)
    active: bool | None = None
    regular_service_enabled: bool | None = None
    emergency_service_enabled: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=10000)

    @field_validator("state_code", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> str | None:
        return normalize_state_code(None if value is None else str(value))

    @model_validator(mode="after")
    def validate_patch(self) -> "PostalCodeUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one postal-code field is required")
        return self


class PostalCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_area_id: uuid.UUID
    postal_code: str
    city: str | None
    state_code: str | None
    active: bool
    regular_service_enabled: bool
    emergency_service_enabled: bool
    priority: int
    version: int
    created_at: datetime
    updated_at: datetime


class PostalCodeList(BaseModel):
    items: list[PostalCodeRead]
    total: int
    page: int
    page_size: int


class ServiceZoneCoverage(BaseModel):
    service_zone: ServiceZoneRead
    postal_codes: list[PostalCodeRead]
    service_ids: list[uuid.UUID]


class PostalCodeImportRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    postal_code: str = Field(min_length=5, max_length=10)
    city: str | None = Field(default=None, max_length=120)
    state_code: str | None = Field(default=None, min_length=2, max_length=3)
    active: bool = True
    regular_service_enabled: bool = True
    emergency_service_enabled: bool = False
    priority: int = Field(default=100, ge=0, le=10000)

    @field_validator("postal_code", mode="before")
    @classmethod
    def normalize_zip(cls, value: object) -> str:
        return normalize_postal_code(str(value))

    @field_validator("state_code", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> str | None:
        return normalize_state_code(None if value is None else str(value))


class PostalCodeImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_area_id: uuid.UUID
    rows: list[PostalCodeImportRow] = Field(min_length=1, max_length=5000)

    @model_validator(mode="after")
    def unique_postal_codes(self) -> "PostalCodeImportRequest":
        codes = [row.postal_code for row in self.rows]
        if len(set(codes)) != len(codes):
            raise ValueError("postal-code import contains duplicate rows")
        return self


class PostalCodeImportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_area_id: uuid.UUID
    idempotency_key: str
    status: PostalCodeImportStatus
    total_rows: int
    imported_rows: int
    rejected_rows: int
    errors: list[dict]
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
