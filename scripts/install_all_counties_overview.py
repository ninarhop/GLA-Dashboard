from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "apps-script" / "DashboardApp.html"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"Already updated: {label}")
        return text
    if old not in text:
        raise SystemExit(f"Could not find expected dashboard block for: {label}")
    print(f"Updated: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    text = APP_PATH.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '    { id: "priority", label: "Priority Counties" },\n',
        '',
        "remove redundant Priority Counties navigation tab",
    )

    marker = '''  function renderOverview() {
'''
    county_function = '''  function allCountyOverviewRows() {
    const registrations = state.intake?.dateSeries?.registrationsByCounty || [];
    const removals = state.intake?.dateSeries?.purgeRemovalsByCounty || [];
    const selectedCounty = selectedCountyName();
    const counties = selectedCounty ? [selectedCounty] : allCountyNames();

    return counties
      .map((county) => ({
        county,
        currentRegistered: currentRegisteredFor(county),
        registeredInRange: sumDatedCounty(registrations, county),
        removedInRange: sumDatedCounty(removals, county),
        returnedSinceBaseline: returnedFor(county),
        ezAppMatches: ezMatchesFor(county)
      }))
      .sort((a, b) => b.currentRegistered - a.currentRegistered || a.county.localeCompare(b.county));
  }

  function renderOverview() {
'''
    text = replace_once(
        text,
        marker,
        county_function,
        "add all-county overview rows",
    )

    old_panel = '''        ${panel(
          "Priority County Registration Activity",
          `Registrations from ${dateLabel()}`,
          rowsToTable(
            [
              { key: "county", label: "Priority County" },
              { key: "currentRegistered", label: "Current Registered", render: (row) => formatNumber(row.currentRegistered) },
              { key: "registeredInRange", label: "Registered in Range", render: (row) => formatNumber(row.registeredInRange) },
              { key: "removedInRange", label: "Removed in Range", render: (row) => formatNumber(row.removedInRange) },
              { key: "returnedSinceBaseline", label: "Returned Since Dec. 2025", render: (row) => formatNumber(row.returnedSinceBaseline) },
              { key: "ezAppMatches", label: "EZ App Found Registered", render: (row) => formatNumber(row.ezAppMatches) }
            ],
            priorityRows()
          )
        )}
'''
    new_panel = '''        ${panel(
          county ? `${county} County Totals` : "All County Totals",
          county ? `Selected county; ${dateLabel()}` : `All Arkansas counties; ${dateLabel()}`,
          rowsToTable(
            [
              { key: "county", label: "County" },
              { key: "currentRegistered", label: "Current Registered", render: (row) => formatNumber(row.currentRegistered) },
              { key: "registeredInRange", label: "Registered in Range", render: (row) => formatNumber(row.registeredInRange) },
              { key: "removedInRange", label: "Removed in Range", render: (row) => formatNumber(row.removedInRange) },
              { key: "returnedSinceBaseline", label: "Returned Since Dec. 2025", render: (row) => formatNumber(row.returnedSinceBaseline) },
              { key: "ezAppMatches", label: "EZ App Found Registered", render: (row) => formatNumber(row.ezAppMatches) }
            ],
            allCountyOverviewRows()
          )
        )}
'''
    text = replace_once(
        text,
        old_panel,
        new_panel,
        "replace priority-county overview with all county totals",
    )

    APP_PATH.write_text(text, encoding="utf-8")
    print(f"Saved {APP_PATH}")


if __name__ == "__main__":
    main()
