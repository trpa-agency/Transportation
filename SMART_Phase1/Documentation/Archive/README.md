# Archive

Superseded Phase 1 files, kept for the record. None of these are used by the
current pipeline.

| File | Why it was retired |
|---|---|
| `SMART_ETL_DEPRECATED.py` | Replaced by `scripts/run_etl.py` and its modules. Never ran in production (`DRY_RUN` defaulted to true). Pushed DERQ's `count`/`date` columns at layers whose fields are `counts`/`Date`, so every value would have written null; had no handling for the Speed layer; appended without dedup, so a failed mid-run push left a permanent data gap; and pip-installed missing packages at import time into whatever interpreter ran it. |
| `utils_DEPRECATED.py` | Not importable. Referenced undefined module-level globals (`derq_api_url`, `headers`, `requests`, `FeatureLayer`, `GIS`) and defined `get_derq_veh_counts`, `get_derq_vru_counts` and `get_derq_speeds` twice each, so the second definition silently shadowed the first. Its working logic now lives in `scripts/derq_client.py`. |
| `Data_ETL_DEPRECATED.ipynb` | Exploration notebook with hand-edited date ranges. Read the API key from `derq-api-key` rather than `DERQ_API_KEY`, and one cell passed an ISO date to `strptime(..., "%m/%d/%Y")`, which raises. Superseded by the `run_etl.py` CLI. |
| `Data_Dictionary_sample_DEPRECATED.csv` | Documented `derq_volume_fact_table` / `derq_event_fact_table` -- the Microsoft Fabric model from the Parametrix samples -- not the published TRPA feature service layers. Replaced by `Documentation/Data_Dictionary.csv`, generated from the live schemas by `scripts/build_data_dictionary.py`. |
| `DCAT-US_MetadataTemplate_ORIGINAL.json` | Invalid JSON: missing a comma after `"hasEmail": "mailto:"`. Corrected copy is `templates/dcat_us_template.json`. |
| `README_SMART_ORIGINAL.md` | The blank USDOT README template. Now `templates/README_template.md`, filled in automatically by `scripts/build_data_package.py`. |

`Parametrix_Samples/` is left in place -- it documents the consultant's
Microsoft Fabric lakehouse processing, which is a separate pipeline from this
one and still a useful reference for the field derivations (lane/approach/
movement parsing, class and severity lookups).
