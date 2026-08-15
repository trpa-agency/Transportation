"""
Generate the data dictionary from the live feature service.

Reads the actual field list off each layer on maps.trpa.org and joins it to the
descriptions in metadata/field_descriptions.yaml. Any live field without a
description is reported, so the dictionary cannot drift away from what is
actually published -- which is how the previous hand-maintained
Data_Dictionary_sample.csv ended up documenting a different data model entirely.

Usage:
    python build_data_dictionary.py
    python build_data_dictionary.py --output ../Documentation/Data_Dictionary.csv
    python build_data_dictionary.py --strict     # exit 1 on any gap
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import requests
import yaml

from smart_config import DOCS_DIR, METADATA_DIR, load_settings

logger = logging.getLogger(__name__)

DESCRIPTIONS_PATH = METADATA_DIR / "field_descriptions.yaml"
DEFAULT_OUTPUT = DOCS_DIR / "Data_Dictionary.csv"

# ArcGIS field types mapped to the plain-language types the published
# dictionary uses (matching the format of the original Data_Dictionary sample).
TYPE_MAP = {
    "esriFieldTypeOID": "int",
    "esriFieldTypeInteger": "int",
    "esriFieldTypeSmallInteger": "int",
    "esriFieldTypeDouble": "float",
    "esriFieldTypeSingle": "float",
    "esriFieldTypeString": "string",
    "esriFieldTypeDate": "date",
    "esriFieldTypeGlobalID": "string",
    "esriFieldTypeGUID": "string",
    "esriFieldTypeGeometry": "geometry",
}


def fetch_layer(service_url: str, layer_id: int) -> dict:
    response = requests.get(
        f"{service_url}/{layer_id}", params={"f": "json"}, timeout=30
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"layer {layer_id}: {data['error']}")
    return data


def resolve_description(entry) -> tuple[str, bool]:
    """A field entry is either a plain string or {definition, needs_review}."""
    if isinstance(entry, dict):
        return str(entry.get("definition", "")).strip(), bool(entry.get("needs_review"))
    return str(entry or "").strip(), False


def build(settings, descriptions: dict) -> tuple[pd.DataFrame, list[str], list[str]]:
    common = descriptions.get("common", {})
    layers = descriptions.get("layers", {})

    rows: list[dict] = []
    undocumented: list[str] = []
    unconfirmed: list[str] = []

    for layer_id in sorted(layers):
        layer_meta = layers[layer_id] or {}
        overrides = layer_meta.get("fields") or {}
        live = fetch_layer(settings.service_url, layer_id)
        table = layer_meta.get("table") or live.get("name", f"layer_{layer_id}")

        for field in live.get("fields", []):
            name = field["name"]
            # A layer-specific definition wins over the shared one.
            entry = overrides.get(name, common.get(name))
            definition, needs_review = resolve_description(entry)

            if not definition:
                undocumented.append(f"{table}.{name}")
            if needs_review:
                unconfirmed.append(f"{table}.{name}")

            rows.append(
                {
                    "Table": table,
                    "Variable": name,
                    "DType": TYPE_MAP.get(field["type"], field["type"]),
                    "Definition": definition,
                    "NeedsReview": "yes" if needs_review else "",
                }
            )

        # Geometry is a real column of the layer but is not in `fields`.
        if live.get("geometryType"):
            rows.append(
                {
                    "Table": table,
                    "Variable": "SHAPE",
                    "DType": "geometry",
                    "Definition": (
                        f"Feature geometry ({live['geometryType']}), "
                        f"{live.get('extent', {}).get('spatialReference', {}).get('wkid', 'unknown')} spatial reference."
                    ),
                    "NeedsReview": "",
                }
            )

    return pd.DataFrame(rows), undocumented, unconfirmed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit non-zero if any live field lacks a description.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)-8s %(message)s", stream=sys.stdout
    )

    settings = load_settings()
    if not DESCRIPTIONS_PATH.exists():
        logger.error("Missing %s", DESCRIPTIONS_PATH)
        return 1
    descriptions = yaml.safe_load(DESCRIPTIONS_PATH.read_text(encoding="utf-8"))

    table, undocumented, unconfirmed = build(settings, descriptions)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False, encoding="utf-8-sig")
    logger.info("Wrote %s rows to %s", len(table), args.output)

    if unconfirmed:
        logger.warning(
            "%s definition(s) marked needs_review -- confirm before publishing:",
            len(unconfirmed),
        )
        for name in unconfirmed:
            logger.warning("    %s", name)

    if undocumented:
        logger.warning(
            "%s live field(s) have no description in %s:",
            len(undocumented), DESCRIPTIONS_PATH.name,
        )
        for name in undocumented:
            logger.warning("    %s", name)
        if args.strict:
            return 1
    else:
        logger.info("Every live field is documented.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
