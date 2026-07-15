from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "apps-script" / "DashboardApp.html"
STYLES_PATH = ROOT / "apps-script" / "Styles.html"


INFO_BLOCK = r'''  const METRIC_INFO = {
    "Current Registered Voters": {
      source: "Current VRVH CSV",
      fields: "All current VRVH rows; County is used when a county filter is selected.",
      calculation: "Counts current voter-file rows statewide or for the selected county."
    },
    "Registered in Date Range": {
      source: "Current VRVH CSV",
      fields: "date_of_registration and County",
      calculation: "Counts registrations whose registration date falls inside the selected start and end dates."
    },
    "Removed in Date Range": {
      source: "Cumulative purge CSV",
      fields: "Last VRVH, voter ID, and County",
      calculation: "Counts purge records assigned to a configured purge-period date inside the selected range."
    },
    "Returned to Current VRVH": {
      source: "Cumulative purge CSV compared with the current VRVH CSV",
      fields: "Purge voter ID matched to current VRVH VoterID",
      calculation: "Counts people from the purge file whose voter ID appears again in the current VRVH. This is cumulative since December 1, 2025."
    },
    "EZ App Found Registered": {
      source: "Complete EZ App CSV compared with the current VRVH CSV",
      fields: "First Name + Last Name + Date of Birth; County or ZIP is used only as a tiebreaker",
      calculation: "Counts exact EZ App-to-VRVH matches. Capitalization, punctuation, and extra spaces do not affect the name comparison."
    },
    "Usable EZ App Submissions": {
      source: "Complete EZ App CSV",
      fields: "First Name, Last Name, and Date of Birth",
      calculation: "Counts EZ App rows that contain all three required matching fields."
    },
    "Submissions in Date Range": {
      source: "Complete EZ App CSV",
      fields: "Date",
      calculation: "Counts usable EZ App submissions whose submission date falls inside the selected range."
    },
    "Submissions Found in VRVH": {
      source: "Complete EZ App CSV compared with the current VRVH CSV",
      fields: "First Name + Last Name + Date of Birth",
      calculation: "Counts exact matches for EZ App submissions in the selected date range."
    },
    "Registered After Submission": {
      source: "EZ App CSV and current VRVH CSV",
      fields: "EZ App submission Date and VRVH date_of_registration",
      calculation: "Counts matched people whose VRVH registration date is on or after their EZ App submission date."
    },
    "Overall Match Rate": {
      source: "EZ App match results",
      fields: "Matched EZ App submissions and usable EZ App submissions",
      calculation: "Matched submissions divided by usable submissions, multiplied by 100."
    },
    "Still Missing Statewide": {
      source: "Cumulative purge CSV compared with the current VRVH CSV",
      fields: "Purge voter IDs and current VRVH VoterID",
      calculation: "Removed since baseline minus people returned to the current VRVH."
    },
    "Statewide Return Rate": {
      source: "Cumulative purge CSV compared with the current VRVH CSV",
      fields: "Removed count and returned count",
      calculation: "Returned to current VRVH divided by removed since baseline, multiplied by 100."
    },
    "Categorized by Zodiac": {
      source: "Current VRVH CSV",
      fields: "date_of_birth",
      calculation: "Counts current VRVH rows with a valid birth date that can be assigned to a Zodiac sign. Birth dates are never displayed."
    },
    "Voted in Selected Election": {
      source: "Current VRVH CSV",
      fields: "The selected 2024 or 2026 election column",
      calculation: "Counts voters with a nonblank value in the selected election column."
    },
    "Voting Rate": {
      source: "Current VRVH CSV",
      fields: "Valid birth date and selected election column",
      calculation: "Voted in the selected election divided by registered voters with a valid birth date, multiplied by 100."
    }
  };

  function metricInfoFor(label) {
    return METRIC_INFO[label] || {
      source: "Current aggregate dashboard data",
      fields: "The source fields depend on the selected dashboard section and filters.",
      calculation: "Displays the aggregate value produced by the current local dashboard build."
    };
  }

'''


OLD_METRIC_CARD = r'''  function metricCard(label, value, detail = "") {
    return `
      <article class="metric-card">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
        ${detail ? `<small>${escapeHtml(detail)}</small>` : ""}
      </article>
    `;
  }
'''


NEW_METRIC_CARD = r'''  function metricCard(label, value, detail = "") {
    const info = metricInfoFor(label);
    return `
      <article class="metric-card">
        <div class="metric-card-heading">
          <span>${escapeHtml(label)}</span>
          <button
            class="metric-info-button"
            type="button"
            aria-label="Show data source for ${escapeHtml(label)}"
            aria-expanded="false"
            title="Show data source"
          >i</button>
        </div>
        <strong>${escapeHtml(value)}</strong>
        ${detail ? `<small>${escapeHtml(detail)}</small>` : ""}
        <div class="metric-info-popover" hidden>
          <div><b>Data source</b><p>${escapeHtml(info.source)}</p></div>
          <div><b>Fields used</b><p>${escapeHtml(info.fields)}</p></div>
          <div><b>How it is calculated</b><p>${escapeHtml(info.calculation)}</p></div>
        </div>
      </article>
    `;
  }
'''


WIRE_FUNCTION = r'''  function wireMetricInfoButtons() {
    document.querySelectorAll(".metric-info-button").forEach((button) => {
      button.onclick = (event) => {
        event.stopPropagation();
        const card = button.closest(".metric-card");
        const popover = card?.querySelector(".metric-info-popover");
        if (!popover) return;

        const willOpen = popover.hidden;
        document.querySelectorAll(".metric-info-popover").forEach((item) => {
          item.hidden = true;
        });
        document.querySelectorAll(".metric-info-button").forEach((item) => {
          item.setAttribute("aria-expanded", "false");
        });

        popover.hidden = !willOpen;
        button.setAttribute("aria-expanded", willOpen ? "true" : "false");
      };
    });
  }

'''


INFO_STYLES = r'''
.metric-card {
  position: relative;
}

.metric-card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.metric-info-button {
  display: inline-grid;
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: var(--surface-soft);
  color: var(--blue);
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 900;
  line-height: 1;
}

.metric-info-button:hover,
.metric-info-button[aria-expanded="true"] {
  border-color: var(--blue);
  background: var(--blue);
  color: #fff;
}

.metric-info-popover {
  position: absolute;
  z-index: 30;
  top: 46px;
  right: 12px;
  width: min(340px, calc(100vw - 48px));
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: 0 18px 42px rgba(20, 33, 61, 0.22);
  color: var(--text);
}

.metric-info-popover[hidden] {
  display: none;
}

.metric-info-popover div + div {
  margin-top: 10px;
}

.metric-info-popover b {
  display: block;
  margin-bottom: 3px;
  color: var(--teal);
  font-size: 0.78rem;
  text-transform: uppercase;
}

.metric-info-popover p {
  margin: 0;
  color: var(--text);
  font-size: 0.84rem;
  line-height: 1.42;
}
'''


def main() -> None:
    app = APP_PATH.read_text(encoding="utf-8")
    styles = STYLES_PATH.read_text(encoding="utf-8")

    if "const METRIC_INFO =" not in app:
        marker = "  function metricCard(label, value, detail = \"\") {"
        if marker not in app:
            raise SystemExit("Could not find metricCard insertion point.")
        app = app.replace(marker, INFO_BLOCK + marker, 1)
    else:
        print("Already updated: metric information map")

    if NEW_METRIC_CARD not in app:
        if OLD_METRIC_CARD not in app:
            raise SystemExit("Could not find the original metricCard function.")
        app = app.replace(OLD_METRIC_CARD, NEW_METRIC_CARD, 1)
    else:
        print("Already updated: metric card information button")

    if "function wireMetricInfoButtons()" not in app:
        marker = "  function render() {"
        if marker not in app:
            raise SystemExit("Could not find render() insertion point.")
        app = app.replace(marker, WIRE_FUNCTION + marker, 1)
    else:
        print("Already updated: metric information wiring")

    old_render = '''    if (container) container.innerHTML = renderActiveSection();\n    wireZodiacElectionFilter();'''
    new_render = '''    if (container) container.innerHTML = renderActiveSection();\n    wireZodiacElectionFilter();\n    wireMetricInfoButtons();'''
    if new_render not in app:
        if old_render not in app:
            raise SystemExit("Could not find render wiring block.")
        app = app.replace(old_render, new_render, 1)
    else:
        print("Already updated: render wiring")

    if ".metric-info-button {" not in styles:
        if "</style>" not in styles:
            raise SystemExit("Could not find the closing style tag.")
        styles = styles.replace("</style>", INFO_STYLES + "\n</style>", 1)
    else:
        print("Already updated: metric information styles")

    APP_PATH.write_text(app, encoding="utf-8")
    STYLES_PATH.write_text(styles, encoding="utf-8")

    print("Added data-source information buttons to all dashboard metric cards.")
    print(f"Updated: {APP_PATH}")
    print(f"Updated: {STYLES_PATH}")


if __name__ == "__main__":
    main()
