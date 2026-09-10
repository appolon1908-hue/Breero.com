# BREERO geography, timezone, and service-zone slice

## Scope

This branch extends the existing FastAPI/PostgreSQL/PostGIS system. It does not
replace the accepted scheduling implementation and does not activate automatic
assignment, confirmation, payments, email, SMS, callbacks, or production
deployment.

## Public APIs

```http
POST /api/v1/booking/address/validate
POST /api/v1/booking/service-area/check
POST /api/v1/booking/timezone/resolve
```

Address validation writes an immutable validation snapshot containing the
normalized address, ZIP and optional ZIP+4, city, county, state, coordinates,
provider evidence, confidence, and the IANA service-address timezone. Validation
does not imply that a requested service is covered.

Service-area checks are service-specific and fail closed. They may return only
the matching BREERO service-zone summary; provider candidates, professionals,
scores, private capacity, and provider locations are not part of the public
contract.

## Administrative APIs

```http
GET    /api/v1/admin/service-zones
POST   /api/v1/admin/service-zones
GET    /api/v1/admin/service-zones/{service_area_id}
PATCH  /api/v1/admin/service-zones/{service_area_id}
DELETE /api/v1/admin/service-zones/{service_area_id}
GET    /api/v1/admin/service-zones/{service_area_id}/coverage

GET    /api/v1/admin/postal-codes
POST   /api/v1/admin/postal-codes
PATCH  /api/v1/admin/postal-codes/{postal_code_id}
DELETE /api/v1/admin/postal-codes/{postal_code_id}
POST   /api/v1/admin/postal-codes/import
GET    /api/v1/admin/postal-codes/imports/{import_id}
```

Administrative writes require effective `admin.access.manage` permission.
Updates and deactivations require `If-Match`. Postal imports require a safe
`Idempotency-Key`; the same key and body replay the original import while the
same key with a changed body returns a conflict.

DELETE is implemented as auditable deactivation so historic booking, routing,
and audit evidence is not destroyed.

## Geographic matching

Migration `021_geography_service_zones` preserves the existing `service_areas`
table and adds normalized service offerings and postal routing.

A zone can use:

- ZIP or ZIP+4;
- city or state coarse coverage;
- PostGIS radius coverage;
- PostGIS polygon or multipolygon coverage.

Configured but inactive postal rows never fall back to city/state coverage.
Overlapping eligible zones are resolved deterministically by descending
priority, then name and identifier. A service-specific coverage result also
requires an active catalog service and an active regular-service offering for
that zone.

## Provider adapters

The application depends on a geography protocol rather than a provider SDK:

```text
REAL      GeocodingAdapter
FAKE      FakeGeocodingAdapter
TEST      dependency override using FakeGeocodingAdapter
DISABLED  GEOCODING_ENABLED=false, returning a controlled 503
```

The real adapter uses the existing Geoapify configuration for forward address
validation and reverse coordinate lookup. Tests use deterministic adapters and
perform no external network calls.

## Safety invariants

```text
SERVICE_ADDRESS_TIMEZONE_IS_AUTHORITATIVE=YES
POSTGRES_POSTGIS_IS_ROUTING_AUTHORITY=YES
PUBLIC_PROVIDER_CANDIDATE_DISCLOSURE=NO
INACTIVE_POSTAL_COVERAGE_MATCHES=NO
AUTOMATIC_ASSIGNMENT=NO
PRODUCTION_SIDE_EFFECTS=0
```
