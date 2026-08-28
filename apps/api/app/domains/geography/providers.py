from typing import Protocol

from app.integrations.geocoding import GeocodedAddress


class GeographyProvider(Protocol):
    """Replaceable address and coordinate-timezone provider boundary."""

    async def geocode(self, address: str) -> GeocodedAddress: ...

    async def resolve_timezone(self, latitude: float, longitude: float) -> str: ...
