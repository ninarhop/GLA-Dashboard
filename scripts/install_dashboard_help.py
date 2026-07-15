from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "apps-script" / "DashboardApp.html"
STYLES_PATH = ROOT / "apps-script" / "Styles.html"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"Already updated: {label}")
        return text
    if old not in text:
        raise SystemExit(f"Could not find expected dashboard block for: {label}")
    return text.replace(old, new, 1)


HELP_RENDERER = r'''  function renderHelp() {
    return `
      <section class="dashboard-section help-page">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Help & Data Updates</p>
            <h2>How to Update the GLA Dashboard</h2>
          </div>
          <span class="status-pill">Administrator guide</span>
        </div>

        <section class="panel help-intro">
          <h3>Regular update process</h3>
          <p>Upload new source CSV files through the Windows Shared Drive, run the complete local build, wait for Google Drive to sync, and refresh the dashboard. Normal data updates do not require an Apps Script deployment.</p>
          <div class="help-warning"><strong>Privacy:</strong> Never upload raw voter files, names, voter IDs, birth dates, addresses, phone numbers, emails, or person-level records to GitHub.</div>
        </section>

        <section class="panel stacked-panel help-checklist">
          <div class="panel-heading"><h3>Quick update checklist</h3><span>Use every time</span></div>
          <ol>
            <li>Export each source as a CSV and preserve the original column names.</li>
            <li>Move the previous source file into an <code>Archive</code> subfolder.</li>
            <li>Put the new file in the correct <code>01_Data_Intake</code> folder using the required filename pattern.</li>
            <li>Close the CSV files before running the build.</li>
            <li>Open Windows PowerShell.</li>
            <li>Run <code>cd C:\\Users\\nina\\GLA-Dashboard-Code</code>.</li>
            <li>Run <code>git pull origin platform-v1</code>.</li>
            <li>Run <code>python .\\scripts\\build_all_dashboard_data.py</code>.</li>
            <li>Wait for the message that all dashboard aggregates and private EZ App reports are current.</li>
            <li>Wait for Google Drive for Desktop to finish syncing.</li>
            <li>Refresh the dashboard with <code>Ctrl + F5</code>.</li>
            <li>Verify the generated date and totals.</li>
          </ol>
        </section>

        <details class="help-section" open>
          <summary>1. Main folder and upload locations</summary>
          <div class="help-body">
            <p>Main dashboard folder:</p>
            <pre><code>G:\\Shared drives\\Get Loud Arkansas\\Data\\Get Load Arkansas Dashboard</code></pre>
            <div class="help-table-wrap">
              <table>
                <thead><tr><th>Data</th><th>Upload folder</th><th>Required filename</th></tr></thead>
                <tbody>
                  <tr><td>Current VRVH</td><td><code>01_Data_Intake\\01_Current_VRVH</code></td><td><code>VRVH_FULL_YYYY-MM-DD.csv</code></td></tr>
                  <tr><td>Cumulative purge list</td><td><code>01_Data_Intake\\02_Purge_Lists</code></td><td><code>PURGE_CUMULATIVE_YYYY-MM-DD.csv</code></td></tr>
                  <tr><td>EZ App export</td><td><code>01_Data_Intake\\03_EZ_App</code></td><td><code>GLA_EZ_APP_FULL_YYYY-MM-DD.csv</code></td></tr>
                  <tr><td>Outreach</td><td><code>01_Data_Intake\\04_Outreach</code></td><td><code>GLA_OUTREACH_YYYY-MM-DD.csv</code></td></tr>
                  <tr><td>Priority counties</td><td><code>01_Data_Intake\\05_Priority_Counties</code></td><td><code>GLA_PRIORITY_COUNTIES_CURRENT.csv</code></td></tr>
                </tbody>
              </table>
            </div>
            <p>Use the source export date in dated filenames. Keep only the current file in the main intake folder. Move older matching files into an <code>Archive</code> subfolder because the scripts select the most recently modified matching file.</p>
          </div>
        </details>

        <details class="help-section">
          <summary>2. Required CSV format</summary>
          <div class="help-body">
            <ul>
              <li>Use CSV format, not XLSX, Google Sheets, PDF, ZIP, or database files.</li>
              <li>Put column names in the first row with no title or blank rows above them.</li>
              <li>Use one person or record per row.</li>
              <li>Do not use merged cells.</li>
              <li>Save values rather than Excel formulas.</li>
              <li>Do not rename the source columns. Column order may change, but column names must remain exact.</li>
            </ul>
            <p>Supported date examples include <code>2026-07-14</code>, <code>07/14/2026</code>, <code>07/14/26</code>, <code>07-14-2026</code>, and <code>2026/07/14</code>.</p>
          </div>
        </details>

        <details class="help-section">
          <summary>3. Current VRVH file</summary>
          <div class="help-body">
            <p><strong>Folder:</strong> <code>01_Data_Intake\\01_Current_VRVH</code></p>
            <p><strong>Filename:</strong> <code>VRVH_FULL_YYYY-MM-DD.csv</code></p>
            <p>Use the complete VRVH export. Do not remove or rename columns. The dashboard expects these fields:</p>
            <pre><code>VoterID
CDE_REGISTRANT_STATUS
date_of_registration
date_of_birth
TEXT_NAME_FIRST
TEXT_NAME_MIDDLE
TEXT_NAME_LAST
County
TEXT_RES_CITY
TEXT_RES_ZIP5
TEXT_RES_PHYSICAL_ADDRESS
PrecinctName
StateRepresentativeDistrict
StateSenateDistrict
CongressionalDistrict
DateLastVoted
2026 Preferential Primary</code></pre>
            <p>Keep all recent election columns beginning with <code>2024</code> or <code>2026</code>. Those columns power Zodiac election participation.</p>
          </div>
        </details>

        <details class="help-section">
          <summary>4. Cumulative purge file</summary>
          <div class="help-body">
            <p><strong>Folder:</strong> <code>01_Data_Intake\\02_Purge_Lists</code></p>
            <p><strong>Filename:</strong> <code>PURGE_CUMULATIVE_YYYY-MM-DD.csv</code></p>
            <p>Use the full cumulative purge file, not only the newest month. Preserve these fields:</p>
            <pre><code>VR_VH OLD.VoterID
VR_VH OLD.TEXT_NAME_FIRST
VR_VH OLD.TEXT_NAME_MIDDLE
VR_VH OLD.TEXT_NAME_LAST
VR_VH OLD.County
VR_VH OLD.TEXT_RES_CITY
VR_VH OLD.TEXT_RES_ZIP5
VR_VH OLD.Full Address Line 1
VR_VH OLD.Full Address Line 2
VR_VH OLD.date_of_registration
VR_VH OLD.CDE_REGISTRANT_STATUS
VR_VH OLD.DateLastVoted
Ethnic Group
Hispanic Language Preference
Last VRVH</code></pre>
            <div class="help-warning"><strong>New purge period:</strong> When a new value appears in the <code>Last VRVH</code> column, add that exact value and its effective date to <code>C:\\Users\\nina\\GLA-Dashboard-Code\\config\\source_columns.json</code> before rebuilding. Otherwise the new period may be skipped.</div>
          </div>
        </details>

        <details class="help-section">
          <summary>5. EZ App file and matching rules</summary>
          <div class="help-body">
            <p><strong>Folder:</strong> <code>01_Data_Intake\\03_EZ_App</code></p>
            <p><strong>Filename:</strong> <code>GLA_EZ_APP_FULL_YYYY-MM-DD.csv</code></p>
            <p>Use the complete EZ App export. Preserve these fields:</p>
            <pre><code>EasyApp Submission
Date
First Name
Middle Name
Last Name
Date of Birth
Address Where You Live
City
County
State
Zip Code
E-mail Address
Home Phone Number
Work Phone Number</code></pre>
            <p>EZ App records are matched to VRVH using <strong>first name + last name + date of birth</strong>. Capitalization, punctuation, and extra spaces do not matter. County and ZIP are used only to separate multiple possible matches. The system never matches on name alone.</p>
          </div>
        </details>

        <details class="help-section">
          <summary>6. Priority counties and outreach files</summary>
          <div class="help-body">
            <p><strong>Priority counties:</strong> Place <code>GLA_PRIORITY_COUNTIES_CURRENT.csv</code> in <code>01_Data_Intake\\05_Priority_Counties</code>. The filename must remain exactly the same.</p>
            <pre><code>County
Priority_Status
Effective_Date</code></pre>
            <p>A county is treated as priority when <code>Priority_Status</code> is <code>PRIORITY</code>. The file is still required by the build even when the Executive Overview displays all counties.</p>
            <p><strong>Outreach:</strong> Files named <code>GLA_OUTREACH_YYYY-MM-DD.csv</code> belong in <code>01_Data_Intake\\04_Outreach</code>. The current main comparison build does not yet use this file in dashboard calculations.</p>
          </div>
        </details>

        <details class="help-section" open>
          <summary>7. Run the complete dashboard build</summary>
          <div class="help-body">
            <ol>
              <li>Close Excel and any program that has a source CSV open.</li>
              <li>Confirm the new files are visible in the <code>G:</code> Shared Drive.</li>
              <li>Open Windows PowerShell.</li>
              <li>Run:</li>
            </ol>
            <pre><code>cd C:\\Users\\nina\\GLA-Dashboard-Code
git pull origin platform-v1
python .\\scripts\\build_all_dashboard_data.py</code></pre>
            <p>If Windows does not recognize <code>python</code>, use:</p>
            <pre><code>py .\\scripts\\build_all_dashboard_data.py</code></pre>
            <p>The complete build processes the main aggregate comparison, Zodiac and election totals, and the private EZ App Admin report. The VRVH is large, so the build may take several minutes.</p>
            <p>At the beginning, confirm the script lists the new VRVH, purge, and EZ App filenames. At the end, confirm it reports that all dashboard aggregates and private EZ App follow-up reports are current.</p>
          </div>
        </details>

        <details class="help-section">
          <summary>8. Output files and dashboard refresh</summary>
          <div class="help-body">
            <p>The build updates these files:</p>
            <pre><code>02_Processed_Data\\GLA_AGGREGATE_COMPARISON_CURRENT.json
02_Processed_Data\\GLA_EZ_APP_MATCH_DETAIL_CURRENT.csv
02_Processed_Data\\GLA_EZ_APP_MATCH_SUMMARY_CURRENT.json</code></pre>
            <p>After the build:</p>
            <ol>
              <li>Wait for Google Drive for Desktop to finish syncing.</li>
              <li>Open the GLA Employee Dashboard.</li>
              <li>Press <code>Ctrl + F5</code>.</li>
              <li>Check the generated date and Executive Overview totals.</li>
              <li>Check EZ App totals.</li>
              <li>Check Zodiac and the election dropdown.</li>
              <li>Open EZ App Admin and confirm its last-updated date.</li>
            </ol>
            <p><strong>No Apps Script deployment is required for normal data updates.</strong></p>
          </div>
        </details>

        <details class="help-section">
          <summary>9. Never delete the connected processed files</summary>
          <div class="help-body">
            <div class="help-warning"><strong>Important:</strong> Do not delete and recreate <code>GLA_AGGREGATE_COMPARISON_CURRENT.json</code> or <code>GLA_EZ_APP_MATCH_DETAIL_CURRENT.csv</code>. The dashboard is connected to their Google Drive file IDs.</div>
            <p>The build should update the existing files. Do not convert the CSV to Google Sheets, change the JSON format, empty the Trash and upload a new copy, or commit person-level files to GitHub.</p>
          </div>
        </details>

        <details class="help-section">
          <summary>10. Troubleshooting</summary>
          <div class="help-body">
            <h3>Numbers did not change</h3>
            <ul>
              <li>Confirm the file is in the correct intake folder.</li>
              <li>Confirm the filename matches the required pattern.</li>
              <li>Confirm the file is a CSV and is not inside a ZIP file.</li>
              <li>Confirm the build printed the new filename at the beginning.</li>
              <li>Check whether an older matching file was modified more recently.</li>
              <li>Wait for Google Drive to finish syncing and press <code>Ctrl + F5</code>.</li>
            </ul>
            <h3>Missing required source files</h3>
            <p>Confirm the current VRVH, cumulative purge, complete EZ App, and priority-county files are all present.</p>
            <h3>Zodiac cannot find election columns</h3>
            <p>Use the complete VRVH export and keep qualifying election columns beginning with <code>2024</code> or <code>2026</code>.</p>
            <h3>EZ App totals are lower than expected</h3>
            <p>A usable match requires first name, last name, and date of birth.</p>
            <h3>Newest purge period is missing</h3>
            <p>Add the exact new <code>Last VRVH</code> value and effective date to <code>config\\source_columns.json</code>, then rebuild.</p>
            <h3>Dashboard says JSON is not configured</h3>
            <p>The aggregate output file was deleted, recreated, or its Drive setting was lost. Reconnect the existing aggregate JSON file.</p>
            <h3>EZ App Admin says it is not configured</h3>
            <p>The private detail CSV setting or approved-email list was lost. Reconnect the existing private CSV and approved administrators.</p>
          </div>
        </details>
      </section>
    `;
  }

'''


HELP_STYLES = r'''
.help-intro p,
.help-body p,
.help-body li {
  line-height: 1.55;
}

.help-checklist ol,
.help-body ol,
.help-body ul {
  margin: 0;
  padding-left: 1.4rem;
}

.help-checklist li,
.help-body li {
  margin-bottom: 0.5rem;
}

.help-section {
  margin-top: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.help-section summary {
  padding: 16px 18px;
  cursor: pointer;
  color: var(--text);
  font-weight: 850;
}

.help-section[open] summary {
  border-bottom: 1px solid var(--line);
  background: var(--surface-soft);
}

.help-body {
  padding: 18px;
}

.help-body h3 {
  margin: 18px 0 8px;
}

.help-body h3:first-child {
  margin-top: 0;
}

.help-body pre {
  max-width: 100%;
  overflow-x: auto;
  margin: 12px 0 16px;
  padding: 14px;
  border-radius: 8px;
  background: #111827;
  color: #f9fafb;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.help-body pre code {
  padding: 0;
  background: transparent;
  color: inherit;
}

.help-warning {
  margin: 12px 0;
  padding: 12px 14px;
  border-left: 4px solid var(--gold);
  border-radius: 6px;
  background: #fffaf0;
  line-height: 1.5;
}

.help-table-wrap {
  overflow-x: auto;
}
'''


def main() -> None:
    app = APP_PATH.read_text(encoding="utf-8")
    styles = STYLES_PATH.read_text(encoding="utf-8")

    app = replace_once(
        app,
        '    { id: "zodiac", label: "Zodiac" },\n    { id: "county", label: "County Explorer" }',
        '    { id: "zodiac", label: "Zodiac" },\n    { id: "county", label: "County Explorer" },\n    { id: "help", label: "Help & Data Updates" }',
        "Help navigation item",
    )

    if "function renderHelp()" not in app:
        marker = "  function renderActiveSection() {"
        if marker not in app:
            raise SystemExit("Could not find renderActiveSection() insertion point.")
        app = app.replace(marker, HELP_RENDERER + marker, 1)
    else:
        print("Already updated: Help renderer")

    app = replace_once(
        app,
        '      case "county":\n        return renderCountyExplorer();\n      case "overview":',
        '      case "county":\n        return renderCountyExplorer();\n      case "help":\n        return renderHelp();\n      case "overview":',
        "Help section routing",
    )

    if ".help-section {" not in styles:
        if "</style>" not in styles:
            raise SystemExit("Could not find closing style tag.")
        styles = styles.replace("</style>", HELP_STYLES + "\n</style>", 1)
    else:
        print("Already updated: Help styles")

    APP_PATH.write_text(app, encoding="utf-8")
    STYLES_PATH.write_text(styles, encoding="utf-8")

    print("Added Help & Data Updates to the GLA dashboard.")
    print(f"Updated: {APP_PATH}")
    print(f"Updated: {STYLES_PATH}")


if __name__ == "__main__":
    main()
