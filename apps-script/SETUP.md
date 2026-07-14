# GLA Employee Dashboard â€” Google Apps Script Setup

## Files created

- Code.gs
- Index.html
- Styles.html
- DashboardLayout.html
- DashboardApp.html
- appsscript.json

## Dashboard files in Google Drive

Required current data:

GLA_AGGREGATE_COMPARISON_CURRENT.json

Usually located in:

G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard\02_Processed_Data

Optional Zodiac data:

public-dashboard.json

The current dashboard can run without the optional file, but the Zodiac page needs it.

## Connect the Drive files once

1. Open each JSON file in Google Drive.
2. Copy the file ID from its Drive URL.
3. Open Code.gs in Apps Script.
4. Temporarily add this function at the bottom:

   function configureDashboard() {
     return configureDashboardFiles(
       "PASTE_CURRENT_AGGREGATE_FILE_ID",
       "PASTE_OPTIONAL_PUBLIC_DASHBOARD_FILE_ID"
     );
   }

5. Leave the second value as an empty string if the Zodiac file is not ready:

   function configureDashboard() {
     return configureDashboardFiles(
       "PASTE_CURRENT_AGGREGATE_FILE_ID",
       ""
     );
   }

6. Save.
7. Select configureDashboard from the function menu.
8. Click Run.
9. Approve Drive read access.
10. Remove the temporary configureDashboard function after it succeeds.

## Deploy for GLA employees

1. Click Deploy.
2. Select New deployment.
3. Choose Web app.
4. Execute as yourself.
5. Choose the Workspace-only or organization-only access option.
6. Deploy.
7. Share the web-app URL with GLA employees.

## Normal updates

1. Replace the private source files in the intake folders.
2. Run the local comparison script.
3. The comparison script overwrites the same aggregate JSON in Shared Drive.
4. Employees reload the Apps Script URL.
5. Apps Script reads the latest safe aggregate JSON.

The file ID remains the same as long as the existing Drive JSON file is overwritten rather than deleted and recreated.
