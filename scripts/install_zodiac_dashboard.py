from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_APP = ROOT / "apps-script" / "DashboardApp.html"

NEW_RENDER_ZODIAC = r'''  function renderZodiac() {
    const zodiac = state.intake?.zodiac || state.zodiac;
    if (!zodiac) {
      return `
        <section class="dashboard-section">
          <div class="section-heading"><div><p class="eyebrow">Zodiac</p><h2>Registered Voters and Election Participation</h2></div></div>
          <section class="panel empty-state">
            <h3>Zodiac aggregate data is not loaded</h3>
            <p>Run the Zodiac aggregate builder after the normal intake comparison. Birth dates remain private and are never displayed.</p>
          </section>
        </section>
      `;
    }

    const elections = zodiac.elections || [];
    if (!state.zodiacElection) {
      state.zodiacElection = zodiac.defaultElectionId || elections[0]?.id || "";
    }

    const selectedElection = elections.find((row) => row.id === state.zodiacElection) || elections[0] || {};
    const electionId = selectedElection.id || state.zodiacElection;
    const statewideRows = zodiac.statewideByElection?.[electionId] || [];
    const county = selectedCountyName();
    const countyElectionRows = zodiac.countyByElection?.[electionId] || [];
    const selectedCounty = county
      ? countyElectionRows.find((row) => countyKey(row.county) === countyKey(county))
      : null;

    const registered = statewideRows.reduce((total, row) => total + Number(row.registeredVoters || 0), 0);
    const voted = statewideRows.reduce((total, row) => total + Number(row.voted || 0), 0);
    const votingRate = registered ? (voted / registered) * 100 : 0;

    const sortedStatewide = [...statewideRows].sort(
      (a, b) => Number(b.votingRate || 0) - Number(a.votingRate || 0) || Number(b.voted || 0) - Number(a.voted || 0)
    );

    const countyRows = selectedCounty
      ? selectedCounty.bySign || []
      : [...countyElectionRows]
          .sort((a, b) => Number(b.votingRate || 0) - Number(a.votingRate || 0))
          .slice(0, 20);

    const countyPanel = selectedCounty
      ? panel(
          `${county} County by Zodiac`,
          selectedElection.label || "Selected election",
          rowsToTable(
            [
              { key: "zodiacSign", label: "Zodiac Sign" },
              { key: "registeredVoters", label: "Registered Voters", render: (row) => formatNumber(row.registeredVoters) },
              { key: "voted", label: "Voted", render: (row) => formatNumber(row.voted) },
              { key: "votingRate", label: "Voting Rate", render: (row) => formatPercent(row.votingRate) }
            ],
            countyRows
          )
        )
      : panel(
          "County Election Participation",
          "Top 20 counties by voting rate",
          rowsToTable(
            [
              { key: "county", label: "County" },
              { key: "registeredVoters", label: "Registered Voters", render: (row) => formatNumber(row.registeredVoters) },
              { key: "voted", label: "Voted", render: (row) => formatNumber(row.voted) },
              { key: "votingRate", label: "Voting Rate", render: (row) => formatPercent(row.votingRate) },
              { key: "topZodiacByVotingRate", label: "Highest-Rate Zodiac" }
            ],
            countyRows
          )
        );

    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Zodiac</p>
            <h2>Registered Voters and Election Participation</h2>
          </div>
          <label>
            Election
            <select id="zodiacElectionFilter">
              ${elections.map((election) => `<option value="${escapeHtml(election.id)}"${election.id === electionId ? " selected" : ""}>${escapeHtml(election.label)}</option>`).join("")}
            </select>
          </label>
        </div>

        <div class="metric-grid compact">
          ${metricCard("Current Registered Voters", formatNumber(zodiac.registeredVoters), "All rows in the current VRVH")}
          ${metricCard("Categorized by Zodiac", formatNumber(zodiac.registeredWithBirthDate), "Valid birth date available")}
          ${metricCard("Voted in Selected Election", formatNumber(voted), selectedElection.label || "Selected election")}
          ${metricCard("Voting Rate", formatPercent(votingRate), "Voted divided by registered voters with a valid birth date")}
        </div>

        <div class="two-column">
          ${panel(
            "Statewide by Zodiac Sign",
            selectedElection.label || "Selected election",
            rowsToTable(
              [
                { key: "zodiacSign", label: "Zodiac Sign" },
                { key: "registeredVoters", label: "Registered Voters", render: (row) => formatNumber(row.registeredVoters) },
                { key: "voted", label: "Voted", render: (row) => formatNumber(row.voted) },
                { key: "votingRate", label: "Voting Rate", render: (row) => formatPercent(row.votingRate) }
              ],
              sortedStatewide
            )
          )}
          ${countyPanel}
        </div>
      </section>
    `;
  }
'''

WIRE_FUNCTION = r'''  function wireZodiacElectionFilter() {
    const select = byId("zodiacElectionFilter");
    if (!select) return;
    select.onchange = (event) => {
      state.zodiacElection = event.target.value;
      render();
    };
  }

'''


def main() -> None:
    if not DASHBOARD_APP.exists():
        raise SystemExit(f"Dashboard file not found: {DASHBOARD_APP}")

    text = DASHBOARD_APP.read_text(encoding="utf-8-sig")

    if "zodiacElection:" not in text:
        text = text.replace(
            '    endDate: ""\n',
            '    endDate: "",\n    zodiacElection: ""\n',
            1,
        )

    pattern = re.compile(
        r"  function renderZodiac\(\) \{.*?\n  \}\n\n  function renderCountyExplorer",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit("Could not locate renderZodiac in DashboardApp.html")
    text = pattern.sub(
        NEW_RENDER_ZODIAC + "\n  function renderCountyExplorer",
        text,
        count=1,
    )

    if "function wireZodiacElectionFilter" not in text:
        text = text.replace(
            "  function render() {\n",
            WIRE_FUNCTION + "  function render() {\n",
            1,
        )

    text = text.replace(
        "    if (container) container.innerHTML = renderActiveSection();\n",
        "    if (container) container.innerHTML = renderActiveSection();\n    wireZodiacElectionFilter();\n",
        1,
    )

    text = text.replace(
        "      state.zodiac = legacy?.zodiac || null;\n",
        "      state.zodiac = state.intake?.zodiac || legacy?.zodiac || null;\n      if (!state.zodiacElection) {\n        state.zodiacElection = state.zodiac?.defaultElectionId || state.zodiac?.elections?.[0]?.id || \"\";\n      }\n",
        1,
    )

    DASHBOARD_APP.write_text(text, encoding="utf-8")
    print("Updated Apps Script Zodiac dashboard with election and county filters.")


if __name__ == "__main__":
    main()
