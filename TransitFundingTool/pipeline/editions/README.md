# Public and full editions

Builds two pages from the vetted model page in `model/transit-funding-model.html`:

| File | What it holds |
| --- | --- |
| `dist/transit-funding-public.html` | The Existing funding conditions page alone, fixed to the source data, with an "Open the full model" link in the header. No tabs, inputs, scenarios, export, import, reset, or source superscripts. Nothing is read from or saved to browser storage. |
| `dist/transit-funding-full.html` | The model page, with the same Existing funding conditions heading and note as the public page. Password protection is not set up yet. |

The public page links to the full page by file name, so host the two files in the same folder.

## Run it

1. Run the main build (`build_data.bat`) and copy `dist/transit-funding-model.html` to `model/`.
2. Double-click `build_editions.bat`, or run `propy editions/build_editions.py` from `pipeline/`.

Settings, including the file names, the link text, and the Existing funding conditions heading and note, are in `config.yaml`.

## When it stops

The public page is cut from the model page at fixed markers: section comments, element IDs, the citation superscripts, and a few sentences. If the template changes one of them, the build stops and names it. Update `build_editions.py` to match.

## Limits

- The public page still carries the full source data, because Existing funding conditions is drawn from it. It removes the tools, not the data.
- While the repo is public, both pages and the workbooks can be downloaded from GitHub.
