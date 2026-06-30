# Private Source Data

Put updated private CSV exports in this folder.

The public dashboard build script looks here first:

```text
private-source-data\GLA_2026_Registration_Outreach_Tracking.csv
```

To refresh the dashboard:

1. Replace the CSV in this folder with the newest export.
2. Keep the exact filename above.
3. From the project root, run:

```powershell
python scripts\build_public_dashboard.py
python scripts\validate_public_output.py --public-dir github-pages
```

Do not commit CSV, XLSX, database, or row-level voter files. This folder is for private local source data only; GitHub Pages must only receive aggregate files generated into `github-pages\`.
