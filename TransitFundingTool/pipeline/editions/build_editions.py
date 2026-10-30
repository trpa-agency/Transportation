"""Build the public and full editions of the Regional Transit Funding Model.

Reads the vetted page in model/ and writes two files to editions/dist/:
  - the public edition: the Existing funding conditions page alone, fixed to the source data,
    with a link to the full model in the header
  - the full edition: the model page, with the same Existing funding conditions heading and note

The main build, the template, and model/ are not changed.
Usage, from pipeline/:  propy editions/build_editions.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


class EditionError(Exception):
    pass


def cut(s: str, start: str, end: str, what: str, keep_end: bool = True) -> str:
    """Remove the text from `start` up to `end`. Both markers must occur exactly once."""
    for m in (start, end):
        if s.count(m) != 1:
            raise EditionError(f"{what}: expected one match for {m[:70]!r}, found {s.count(m)}. The page layout changed; update build_editions.py.")
    a = s.index(start)
    b = s.index(end, a)
    return s[:a] + (s[b:] if keep_end else s[b + len(end):])


def swap(s: str, old: str, new: str, what: str) -> str:
    if s.count(old) != 1:
        raise EditionError(f"{what}: expected one match for {old[:70]!r}, found {s.count(old)}. The page layout changed; update build_editions.py.")
    return s.replace(old, new)


def existing_page_text(s: str, cfg: dict) -> str:
    """Heading and note on Existing funding conditions. Used by both editions."""
    ex = cfg["existing_page"]
    s = swap(s, '<h2>Existing funding conditions, FY 26-27 <span class="upd fixed">Source data</span></h2>',
             f'<h2>{html.escape(ex["heading"], quote=False)}</h2>', "page heading")
    # The script still fills #exAsOf, so keep it as an empty hidden element and show the fixed text beside it.
    s = swap(s, '<p class="today-note" id="exAsOf"></p>',
             f'<p class="today-note">{html.escape(ex["subtext"], quote=False)}</p><p id="exAsOf" hidden></p>', "page subtext")
    return s


def make_full(s: str, cfg: dict) -> str:
    return existing_page_text(s, cfg)


def make_public(s: str, cfg: dict, full_file: str) -> str:
    pub = cfg["public"]

    # Header: replace the year picker with a link to the full model. Drop the scenario bar.
    link = f'<a class="linkbtn hdr-full" href="{html.escape(full_file)}">{html.escape(pub["full_link_text"])}</a>\n'
    s = cut(s, '<span class="year-pick">Fiscal year', "  </div>\n</header>", "year picker")
    s = swap(s, "  </div>\n</header>", "    " + link + "  </div>\n</header>", "header link")
    s = swap(s, '">Beta</span>', f'">{html.escape(pub["status_label"], quote=False)}</span>', "status chip")
    s = cut(s, '<div class="scenario-bar">', '<main class="wrap">', "scenario bar")

    # Keep only Existing funding conditions: no tab bar, no Overview, no other panels, no editing dialogs.
    s = cut(s, '<nav class="tabbar"', "  <!-- ═════════ EXISTING FUNDING CONDITIONS ═════════ -->", "tab bar and overview")
    s = cut(s, "  <!-- ═════════ INPUTS AND ASSUMPTIONS ═════════ -->", "</main>", "other panels")
    s = cut(s, "<!-- Funding source editor -->", "<!-- Source data", "editing dialogs")
    s = swap(s, 'id="panel-existing" data-panel="existing" aria-labelledby="tab-existing" hidden>',
             'id="panel-existing" data-panel="existing" aria-label="Existing funding conditions">', "existing panel")

    s = existing_page_text(s, cfg)

    # Citations point to the Sources and notes tab, which this page does not have. Remove the superscripts.
    s, n = re.subn(r'<sup class="cn">.*?</sup>', "", s)
    if n == 0:
        raise EditionError("citations: no superscripts found. The page layout changed; update build_editions.py.")
    s = swap(s, "const supHtml = ns => ns.length ?", "const supHtml = ns => false ?", "citation helper")

    # Text that refers to editing or to other tabs.
    s = swap(s, " Edit these on Inputs and assumptions.", "", "inventory note")
    s = swap(s, "User edits change the One-year outlook and Five-year outlook tabs. ", "", "existing conditions note")

    s = swap(s, "</head>", "<style>\n  /* public edition */\n"
             "  .hdr-full { display: inline-block; text-decoration: none; }\n"
             "  .beta-chip { font-size: 1.1rem; padding: 0.15rem 0.75rem; color: var(--ct-red-text); border-color: var(--ct-red-text); background: var(--ct-red-light); }\n"
             "</style>\n</head>", "page head")

    # Script: open on Existing funding conditions, controls removed above resolve to a no-op,
    # and nothing is read from or saved to browser storage.
    s = swap(s, "let CURRENT_TAB = 'overview';", "let CURRENT_TAB = 'existing';", "start tab")
    s = swap(s, "  renderTab('overview');\n", "  renderTab('existing');\n", "start tab")
    s = swap(s, "const $ = id => document.getElementById(id);",
             "/* Public edition: controls removed from this page resolve to a no-op object. */\n"
             "const NOOP = new Proxy(function () {}, { get: (t, k) => k === Symbol.toPrimitive ? () => '' : k === Symbol.iterator ? function* () {} : NOOP, set: () => true, apply: () => NOOP });\n"
             "const $ = id => document.getElementById(id) || NOOP;", "element lookup")
    s = swap(s, "  try { const raw = localStorage.getItem(STORE_KEY); if (raw) p = JSON.parse(raw); } catch (e) { p = null; }",
             "  p = null; /* public edition: always the source data */", "load state")
    s = swap(s, "  try { localStorage.setItem(STORE_KEY, JSON.stringify(S)); saveOk = true; } catch (e) { saveOk = false; }",
             "  saveOk = true; /* public edition: nothing is saved */", "save state")

    for gone in ('id="panel-overview"', 'id="panel-inputs"', 'id="panel-assumptions"', 'class="tabbar"', 'id="btnExport"',
                 'id="btnReset"', 'id="dlgLine"', '<sup class="cn">', 'localStorage.setItem'):
        if gone in s:
            raise EditionError(f"public edition still contains {gone}.")
    return s


def main() -> int:
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    src = (HERE / cfg["source_page"]).resolve()
    out = (HERE / cfg["output_folder"]).resolve()
    if not src.is_file():
        print(f"Source page not found: {src}")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    page = src.read_text(encoding="utf-8")
    full_file = cfg["full"]["file"]
    try:
        public = make_public(page, cfg, full_file)
    except EditionError as e:
        print(f"Build stopped: {e}")
        return 1
    (out / cfg["public"]["file"]).write_text(public, encoding="utf-8", newline="\n")
    try:
        full = make_full(page, cfg)
    except EditionError as e:
        print(f"Build stopped: {e}")
        return 1
    (out / full_file).write_text(full, encoding="utf-8", newline="\n")
    print(f"Read {src}")
    print(f"  wrote {out / cfg['public']['file']} (public edition, {len(public):,} bytes)")
    print(f"  wrote {out / full_file} (full edition, model page with the Existing funding conditions wording)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
