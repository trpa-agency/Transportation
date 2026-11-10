# Tahoe Transit Study site

Public project site for the Tahoe Transit Study, built for GitHub Pages. It replaces https://tahoetransitstudy.squarespace.com/.

## Files

| Path | What it is |
|---|---|
| `index.html` | The site. One page with five tabs: Home, Draft recommendations, Existing conditions (governance, historic timeline, and funding), Get involved, and Project partners. |
| `config/site-config.js` | Every link, file path, embed ID, image, contact, and meeting date. Edit this file, not the page, to change them. |
| `data/recommendations-matrix.js` | Recommendations, lead agencies, and partners for the responsibility matrix on the Draft recommendations tab. Service and governance follow the Executive Summary, Tables 3 and 4. |
| `assets/img/` | TRPA logos, favicon, and the governance chart. |

## Tabs and links

Each tab has a URL: `#home`, `#recommendations`, `#existing-conditions`, `#get-involved`, `#partners`. `#governance` and `#funding` jump to those sections of Existing conditions. Any id on the page also works as a link and opens its tab, for example `#survey`, `#reports`, or `#meetings`.

## Brand

The header, tabs, and footer use the TRPA agency shell (Open Sans, TRPA blue and navy). The content uses Connecting Tahoe colors on the EIP system: Lexend Deca, Montserrat for small uppercase labels, pill buttons, and 10px cards. Tokens come from the TRPA design system `trpa-tokens.css` Connecting Tahoe layer, inlined in each page.

## Updating

- **Meetings:** add or edit entries in `meetings` in `config/site-config.js`. The page sorts them into Upcoming and Past by today's date.
- **Reports and funding tables:** edit `reports` and `fundingTables`. The PDFs are hosted on trpa.gov. An optional `accent` sets a card's top color.
- **Images and logos:** edit `images` and `partners`. Every path is a file in `assets/img/`. Partner logos are in `assets/img/partners/`, trimmed and sized to 320 by 160 pixels or smaller.
- **Responsibility matrix:** edit `data/recommendations-matrix.js`. Each recommendation lists `lead` and `partners` as keys from `AG`. Add a new agency to `AG` first.

## Preview

Serve the folder with any static server, for example `python -m http.server` from this folder, then open http://localhost:8000/. The config and matrix data files load best from a server.
