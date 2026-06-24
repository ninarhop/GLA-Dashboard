# Get Loud Arkansas Public Dashboard

This repository is for the public, aggregate-only Get Loud Arkansas dashboard.

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

## Refreshing The Public Dashboard

Refresh the public dashboard from the internal Google Drive working folder, then review the output before pushing:

```powershell
& "C:\Users\nina\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\build_public_dashboard.py
```

Before pushing, confirm that `github-pages/` contains no names, voter IDs, birth dates, addresses, phone numbers, emails, or person-level rows.
