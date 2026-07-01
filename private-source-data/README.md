# Private Source Data

This folder is where updated private CSV exports go before rebuilding the public dashboard.

## Exact Folder

Use this folder:

```text
G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard\private-source-data
```

## Exact File To Replace

The dashboard build looks for this exact CSV filename:

```text
GLA_2026_Registration_Outreach_Tracking.csv
```

The full path should be:

```text
G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard\private-source-data\GLA_2026_Registration_Outreach_Tracking.csv
```

## Optional Zodiac Files

If the Zodiac workbooks are updated, put the newest aggregate workbooks in this same folder with these exact names:

```text
Registered_voters_by_Zodiac.xlsx
Registered_voters_in_Pulaski_by_Zodiac.xlsx
```

The build script looks in `private-source-data\` first. If those files are not there, it falls back to the older local folder:

```text
Zodiac Project 6.17.2026
```

Only use aggregate Zodiac workbooks. Do not place birth dates or row-level voter exports in public folders.

## How To Replace The CSV

### Easiest Way

1. Download or export the newest tracking CSV.
2. Double-click this file in the project root:

```text
UPDATE_DASHBOARD_FROM_CSV.cmd
```

3. In the file picker, select the newest CSV export.
4. Wait for the script to finish.
5. When it says `Dashboard update complete`, open the public site:

```text
https://ninarhop.github.io/GLA-Dashboard/
```

The updater automatically copies the CSV into this private folder with the correct filename, rebuilds aggregate public data, validates privacy, and publishes the public dashboard.

### Manual Way

1. Download or export the newest tracking CSV.
2. Rename the downloaded file to exactly:

```text
GLA_2026_Registration_Outreach_Tracking.csv
```

3. Open this folder:

```text
G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard\private-source-data
```

4. Drag or copy the new CSV into this folder.
5. When Windows asks whether to replace the existing file, choose **Replace the file in the destination**.
6. Confirm the folder contains only the latest file with this exact name:

```text
GLA_2026_Registration_Outreach_Tracking.csv
```

## Important Rules

- Do not put the CSV in the nested `GLA-Dashboard` folder.
- Do not rename the CSV with dates, spaces, or version numbers.
- Do not commit CSV, XLSX, database, or row-level voter files to GitHub.
- Do not copy voter-level exports into `github-pages\`.
- Only generated aggregate files from `github-pages\` are safe for the public website.

## After Replacing The CSV

Replacing the CSV manually does not update the website by itself unless the watcher script is already running.

To manually rebuild the public aggregate dashboard, open PowerShell and run:

```powershell
cd "G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard"
python scripts\build_public_dashboard.py
python scripts\validate_public_output.py --public-dir github-pages
```

The build reads the private CSV from this folder and writes aggregate-only public data here:

```text
github-pages\data\public-dashboard.json
```
