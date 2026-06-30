# Get Loud Arkansas Public Dashboard

This repository is for the public, aggregate-only Get Loud Arkansas dashboard.

## Project Root

The active working project root is:

```text
G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard
```

Do not work from the nested `GLA-Dashboard` folder unless explicitly instructed. Treat the parent folder above as the source of truth for scripts, docs, source data, and public output.

## Privacy Boundary

No personal-level voter data belongs in this repository or on GitHub Pages.

Do not commit or publish:

- voter names
- voter IDs
- birth dates or birthdays
- street addresses
- phone numbers
- email addresses
- person-level outreach history
- row-level voter exports
- raw CSV, XLSX, SQLite, or database files containing voter records

Allowed public data:

- county-level totals
- city-level totals when aggregated
- demographic group totals
- outreach method totals
- conversion counts and rates
- purge-list counts
- registration counts
- zodiac-sign counts
- age-group counts

Zodiac is allowed only as an aggregate grouping. Birth dates are not allowed.

## Public Site

GitHub Pages publishes the contents of:

```text
github-pages/
```

That folder contains only static dashboard files and aggregate data.

## Updating Source CSVs

Use this private local folder for updated CSV exports:

```text
G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard\private-source-data
```

Replace this file when you receive a new export:

```text
private-source-data\GLA_2026_Registration_Outreach_Tracking.csv
```

Keep the filename exactly the same. CSVs in `private-source-data\` are ignored by Git and must not be committed.

For now, `scripts\build_public_dashboard.py` still falls back to the older root-level CSV if the private source folder file is missing.

## Build And Validate Public Output

From the active project root:

```powershell
cd "G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard"
python scripts\build_public_dashboard.py
python scripts\validate_public_output.py --public-dir github-pages
```

`scripts\build_public_dashboard.py` reads:

```text
G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard\private-source-data\GLA_2026_Registration_Outreach_Tracking.csv
```

and writes:

```text
github-pages\data\public-dashboard.json
```

The validation step checks public data artifacts for forbidden private keys and non-empty person-level arrays.

## Publish Workflow

Use one publishing path: push `github-pages/` changes to `main`, then GitHub Actions deploys `github-pages/` to GitHub Pages.

From the active project root:

```powershell
cd "G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard"
.\scripts\publish_dashboard.ps1
```

The publish script:

- builds local website data
- builds public aggregate JSON
- runs unit tests when `tests/` exists
- validates public output
- commits and pushes `github-pages/` changes to `main`

It does not force-push a `gh-pages` branch.

Before pushing, confirm that `github-pages/` contains no names, voter IDs, birth dates, addresses, phone numbers, emails, or person-level rows.

## Stale Or Legacy Files

Do not delete these yet, but do not treat them as the current public dashboard source:

- `github-pages/dashboard/`
- `gla-dashboard-v2/`
- `GLA_Voter_Dashboard.htm`

The active public entrypoint is:

```text
github-pages/index.html
```
