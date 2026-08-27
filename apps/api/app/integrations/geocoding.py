import httpx

from app.config import settings
from app.core.errors import DomainError
from app.integrations.contracts import GeocodedAddress, GeocodingGateway

__all__ = [
    "FakeGeocodingAdapter",
    "GeocodedAddress",
    "GeocodingAdapter",
    "GeocodingGateway",
]


class FakeGeocodingAdapter:
    def __init__(self, result: GeocodedAddress) -> None:
        self.result = result

    async def geocode(self, address: str) -> GeocodedAddress:
        return self.result


class GeocodingAdapter:
    async def geocode(self, address: str) -> GeocodedAddress:
        if not settings.geocoding_enabled or not settings.geocoding_api_key:
            raise DomainError(
                "GEOCODING_UNAVAILABLE",
                "Coordinates are required while geocoding is not configured",
                422,
            )
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.get(
                    "https://api.geoapify.com/v1/geocode/search",
                    params={"text": address, "apiKey": settings.geocoding_api_key, "limit": 5},
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.TimeoutException as exc:
                raise DomainError(
                    "GEOCODING_TIMEOUT",
                    "Address validation is temporarily unavailable",
                    503,
                ) from exc
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                code = (
                    "GEOCODING_CREDENTIAL_REJECTED"
                    if status_code in {401, 403}
                    else "GEOCODING_RATE_LIMITED"
                    if status_code == 429
                    else "GEOCODING_PROVIDER_FAILURE"
                )
                raise DomainError(
                    code,
                    "Address validation is temporarily unavailable",
                    503,
                ) from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise DomainError(
                    "GEOCODING_PROVIDER_FAILURE",
                    "Address validation is temporarily unavailable",
                    503,
                ) from exc
        features = payload.get("features", []) if isinstance(payload, dict) else []
        if not features:
            raise DomainError("ADDRESS_NOT_FOUND", "Address could not be resolved", 422)
        try:
            props = features[0]["properties"]
            latitude = float(props["lat"])
            longitude = float(props["lon"])
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise DomainError(
                "GEOCODING_PROVIDER_FAILURE",
                "Address validation is temporarily unavailable",
                503,
            ) from exc
        country_code = str(props.get("country_code") or "").upper()
        if country_code != "US":
            raise DomainError(
                "ADDRESS_OUTSIDE_SERVICE_COUNTRY",
                "Only U.S. service addresses are supported",
                422,
            )
        postal_code = str(props.get("postcode") or "").split("-", 1)[0]
        if len(postal_code) != 5 or not postal_code.isdigit():
            raise DomainError("ADDRESS_ZIP_INVALID", "A five-digit U.S. ZIP code is required", 422)
        confidence = props.get("rank", {}).get("confidence")
        if confidence is None or float(confidence) < 0.7:
            raise DomainError(
                "ADDRESS_AMBIGUOUS",
                "Address requires manual validation",
                422,
            )
        return GeocodedAddress(
            formatted_address=props.get("formatted", address),
            line1=props.get("address_line1", address),
            city=props.get("city", props.get("county", "")),
            state_code=str(props.get("state_code") or props.get("state") or "").upper()
            or None,
            postal_code=postal_code,
            country_code=country_code,
            latitude=latitude,
            longitude=longitude,
            provider="geoapify",
            provider_reference=props.get("place_id"),
            confidence=float(confidence),
            quality=props.get("rank", {}).get("match_type"),
            timezone_name=(props.get("timezone") or {}).get("name"),
        )
