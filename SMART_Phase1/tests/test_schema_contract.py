"""
Contract tests against the live feature service.

These catch schema drift -- someone adding, renaming, or removing a field on
maps.trpa.org -- before a scheduled run discovers it at push time.

Run with:   pytest tests -m network
Skip with:  pytest tests -m "not network"
"""

import pytest

import transforms as T

pytestmark = pytest.mark.network


@pytest.fixture(scope="module")
def client(settings):
    from arcgis_client import ArcGISClient

    return ArcGISClient(settings)


@pytest.fixture(scope="module")
def live_fields(client, settings):
    return {
        name: client.get_layer_fields(cfg["layer_id"])
        for name, cfg in settings.datasets.items()
    }


def test_every_field_map_target_exists(settings, live_fields):
    problems = []
    for name, cfg in settings.datasets.items():
        if cfg.get("derived_from"):
            continue
        problems += T.validate_field_map(name, cfg, live_fields[name])
    assert problems == [], "\n".join(problems)


def test_derived_dataset_targets_exist(settings, live_fields):
    for name, cfg in settings.datasets.items():
        if not cfg.get("derived_from"):
            continue
        for field in list(cfg["group_by"]) + [cfg["sum_field"]]:
            assert field in live_fields[name], (
                f"{name}: '{field}' missing from layer {cfg['layer_id']}"
            )


def test_daily_counts_layer_has_no_location_id(settings, live_fields):
    """
    Layer 5 genuinely lacks LocationId -- daily totals group by name only.
    If this ever fails, someone added the field and group_by should be revisited.
    """
    assert "LocationId" not in live_fields["daily_counts"]


def test_speed_layer_has_no_date_field(settings, live_fields):
    """
    Speed is a whole-of-record aggregate loaded by truncate-and-replace. If a
    date field appears, switch it to day_replace instead.
    """
    assert settings.dataset("speed")["date_field"] is None
    assert not {"Date", "date", "TimeAtSite"} & live_fields["speed"]


def test_enrichment_sources_exist_on_the_locations_layer(client, settings, live_fields):
    """Camera_Status is joined from the locations layer, not fetched from DERQ."""
    locations = client.get_locations()
    for name, cfg in settings.datasets.items():
        for target, source in (cfg.get("enrich_from_locations") or {}).items():
            assert target in live_fields[name], (
                f"{name}: enrichment target '{target}' missing from layer "
                f"{cfg['layer_id']}"
            )
            assert source in locations.columns, (
                f"{name}: locations layer has no '{source}' column"
            )


def test_camera_status_matches_the_locations_layer(client, settings):
    """
    Every distinct Camera_Status already on Safety Insights should be a Status
    the locations layer can produce. If this drifts, the enrichment is writing
    values inconsistent with the 24k published rows.
    """
    import requests

    layer_id = settings.dataset("safety_insights")["layer_id"]
    response = requests.get(
        f"{settings.service_url}/{layer_id}/query",
        params={
            "f": "json",
            "where": "Camera_Status IS NOT NULL",
            "outFields": "Camera_Status",
            "returnDistinctValues": "true",
            "returnGeometry": "false",
        },
        timeout=30,
    )
    response.raise_for_status()
    published = {
        f["attributes"]["Camera_Status"] for f in response.json().get("features", [])
    }
    available = set(client.get_locations()["Status"].dropna())
    assert published <= available, f"unexpected Camera_Status values: {published - available}"


def test_service_allows_delete(client, settings):
    """day_replace and full_replace both depend on the Delete capability."""
    import requests

    response = requests.get(settings.service_url, params={"f": "json"}, timeout=30)
    response.raise_for_status()
    assert "Delete" in response.json().get("capabilities", "")


def test_batch_size_within_server_limit(client, settings):
    import requests

    response = requests.get(settings.service_url, params={"f": "json"}, timeout=30)
    response.raise_for_status()
    assert settings.arcgis["batch_size"] <= response.json()["maxRecordCount"]


def test_locations_layer_is_readable(client):
    locations = client.get_locations()
    assert not locations.empty
    assert {"LocationId", "LocationName", "Status"} <= set(locations.columns)
    assert locations["LocationId"].is_unique
