"""
Regenerate the USDOT SMART data package from the live feature service.

The Phase 1 package was assembled by hand, so it could not be reproduced or
refreshed. This rebuilds it end to end: exports every layer, renders the README
and the DCAT-US MetadataPackage.json with row and column counts read from the
service, copies the attachments, and zips the result.

Usage:
    python build_data_package.py
    python build_data_package.py --name TTD_Phase2_Dataset
    python build_data_package.py --skip-zip --output-dir /some/where
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests
import yaml

from arcgis_client import ArcGISClient
from smart_config import EXPORT_DIR, METADATA_DIR, ROOT, TEMPLATE_DIR, load_settings

logger = logging.getLogger(__name__)

PACKAGE_META_PATH = METADATA_DIR / "data_package.yaml"
README_TEMPLATE = TEMPLATE_DIR / "README_template.md"
DCAT_TEMPLATE = TEMPLATE_DIR / "dcat_us_template.json"

MEDIA_TYPES = {"csv": "text/csv", "geojson": "application/vnd.geo+json"}


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


def export_csv(client: ArcGISClient, layer_id: int, path: Path) -> tuple[int, int]:
    """Export a layer to CSV. Returns (rows, columns)."""
    df = client.query_all(layer_id)
    df.to_csv(path, index=False, encoding="utf-8")
    return len(df), len(df.columns)


def export_geojson(
    service_url: str, layer_id: int, path: Path, timeout: int
) -> tuple[int, int]:
    """
    Export a layer as GeoJSON using the service's own f=geojson renderer, so
    the geometry is authoritative rather than rebuilt from lat/long columns.
    """
    response = requests.get(
        f"{service_url}/{layer_id}/query",
        params={
            "f": "geojson",
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"layer {layer_id} geojson export: {payload['error']}")

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    features = payload.get("features", [])
    columns = len(features[0].get("properties", {})) if features else 0
    return len(features), columns


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------


def render_authors(meta: dict) -> str:
    blocks = []
    for author in meta.get("authors", []):
        blocks.append(
            f">  *{author.get('role', 'Data Creator')} Contact Information*\n"
            f">  Name: {author['name']}\n"
            f">  Institution: {author.get('institution', '')}\n"
            f">  Address: {author.get('address', '')}\n"
            f">  Email: {author.get('email', '')}\n"
        )
    org = meta.get("organizational_contact")
    if org:
        blocks.append(
            f">  *Organizational Contact Information*\n"
            f">  Name: {org['name']}\n"
            f">  Institution: {org.get('institution', '')}\n"
            f">  Address: {org.get('address', '')}\n"
            f">  Email: {org.get('email', '')}\n"
        )
    return "\n".join(blocks)


def render_file_list(entries: list[dict]) -> str:
    lines = []
    for index, entry in enumerate(entries, start=1):
        lines.append(
            f">  {index}. Filename: {entry['filename']}\n"
            f">  Short Description:  {entry['description'].strip()}\n"
        )
    return "\n".join(lines)


def render_data_specific(entries: list[dict]) -> str:
    """Section E -- only the exported data files, with live row/column counts."""
    blocks = []
    index = 0
    for entry in entries:
        if "rows" not in entry:
            continue  # attachments have no tabular shape
        index += 1
        blocks.append(
            f"{index}. {entry['filename']}\n"
            f"- Number of variables (columns): {entry['columns']}\n"
            f"- Number of cases/rows: {entry['rows']}\n"
            f"- Each row represents: {entry.get('row_represents', '').strip()}\n"
            f"- Data Dictionary/Variable List: Data_Dictionary.csv\n"
            f"- Missing data codes: Null values are left blank.\n"
        )
    return "\n".join(blocks)


def render_readme(meta: dict, entries: list[dict], build_date: str) -> str:
    template = README_TEMPLATE.read_text(encoding="utf-8")
    author = meta.get("readme_author", {})
    return template.format(
        title=meta["title"].strip(),
        dataset_title=meta["dataset_title"],
        package_name=meta["package_name"],
        build_date=build_date,
        doi=meta["doi"],
        dmp_doi=meta["dmp_doi"],
        abstract=meta["abstract"].strip(),
        description=meta["description"].strip(),
        methods=meta["methods"].strip(),
        software_notes=meta["software_notes"].strip(),
        collection_period=meta["collection_period"],
        geographic_location=meta["geographic_location"].strip(),
        grant_number=meta["grant_number"],
        citation_authors=meta["citation_authors"],
        citation_year=meta["citation_year"],
        citation_title=meta["citation_title"],
        authors_block=render_authors(meta),
        file_list_block=render_file_list(entries),
        data_specific_block=render_data_specific(entries),
        readme_author_name=author.get("name", ""),
        readme_author_title=author.get("title", ""),
        readme_author_institution=author.get("institution", ""),
        readme_author_email=author.get("email", ""),
    )


# ---------------------------------------------------------------------------
# DCAT-US
# ---------------------------------------------------------------------------


def render_dcat(meta: dict, entries: list[dict], build_date: str) -> dict:
    catalog = json.loads(DCAT_TEMPLATE.read_text(encoding="utf-8"))
    catalog["title"] = meta["title"].strip()

    dataset = catalog["dataset"][0]
    org = meta.get("organizational_contact", {})
    dataset["contactPoint"]["fn"] = org.get("name", "")
    dataset["contactPoint"]["hasEmail"] = f"mailto:{org.get('email', '')}"
    dataset["description"] = meta["abstract"].strip()
    dataset["identifier"] = meta["doi"]
    dataset["landingPage"] = meta["doi"]
    dataset["issued"] = str(meta["issued"])
    dataset["modified"] = build_date
    dataset["keyword"] = list(meta.get("keywords", []))
    dataset["license"] = meta["license"]
    dataset["spatial"] = " ".join(meta["spatial_wkt"].split())

    dataset["distribution"] = [
        {
            "@type": "dcat:Distribution",
            "title": entry["filename"],
            "format": entry.get("format", "").upper(),
            "mediaType": entry.get(
                "media_type", MEDIA_TYPES.get(entry.get("format", ""), "")
            ),
            "description": entry["description"].strip(),
            **({"accessURL": meta["doi"]} if "rows" not in entry else {}),
        }
        for entry in entries
    ]
    return catalog


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build(settings, meta: dict, staging: Path, skip_zip: bool) -> Path | None:
    client = ArcGISClient(settings)
    timeout = settings.arcgis.get("request_timeout", 120)
    build_date = date.today().isoformat()

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    entries: list[dict] = []

    for export in meta["exports"]:
        target = staging / export["filename"]
        logger.info("Exporting layer %s -> %s", export["layer_id"], export["filename"])
        if export["format"] == "geojson":
            rows, columns = export_geojson(
                settings.service_url, export["layer_id"], target, timeout
            )
        else:
            rows, columns = export_csv(client, export["layer_id"], target)
        logger.info("  %s rows, %s columns", rows, columns)
        entries.append({**export, "rows": rows, "columns": columns})

    missing = []
    for attachment in meta.get("attachments", []):
        source = ROOT / attachment["path"]
        filename = Path(attachment["path"]).name
        if source.exists():
            shutil.copy2(source, staging / filename)
            logger.info("Copied attachment %s", filename)
        else:
            missing.append(attachment["path"])
        entries.append({**attachment, "filename": filename})

    if missing:
        logger.warning(
            "%s attachment(s) listed in data_package.yaml were not found on disk "
            "and are described in the metadata but absent from the package:",
            len(missing),
        )
        for path in missing:
            logger.warning("    %s", path)

    dictionary = ROOT / "Documentation" / "Data_Dictionary.csv"
    if dictionary.exists():
        shutil.copy2(dictionary, staging / "Data_Dictionary.csv")
        logger.info("Copied Data_Dictionary.csv")
    else:
        logger.warning(
            "Data_Dictionary.csv not found -- run build_data_dictionary.py first."
        )

    (staging / f"{meta['package_name']}_README.md").write_text(
        render_readme(meta, entries, build_date), encoding="utf-8"
    )
    (staging / "MetadataPackage.json").write_text(
        json.dumps(render_dcat(meta, entries, build_date), indent=2), encoding="utf-8"
    )
    logger.info("Rendered README and MetadataPackage.json")

    if skip_zip:
        logger.info("Staged package at %s (--skip-zip)", staging)
        return None

    archive = staging.parent / f"{meta['package_name']}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(staging.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(staging))
    logger.info(
        "Wrote %s (%.1f MB)", archive, archive.stat().st_size / 1_000_000
    )
    return archive


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", help="Override package_name from data_package.yaml.")
    parser.add_argument("--output-dir", type=Path, default=EXPORT_DIR)
    parser.add_argument("--skip-zip", action="store_true",
                        help="Leave the staged folder without archiving it.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)-8s %(message)s", stream=sys.stdout
    )

    if not PACKAGE_META_PATH.exists():
        logger.error("Missing %s", PACKAGE_META_PATH)
        return 1

    settings = load_settings()
    meta = yaml.safe_load(PACKAGE_META_PATH.read_text(encoding="utf-8"))
    if args.name:
        meta["package_name"] = args.name

    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        build(settings, meta, args.output_dir / meta["package_name"], args.skip_zip)
    except Exception as exc:  # noqa: BLE001
        logger.error("Package build failed: %s", exc, exc_info=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
