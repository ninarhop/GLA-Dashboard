(() => {
  const DATA_URL = "data/intake-comparison.json";
  const sections = [
    { id: "overview", label: "Executive Overview" },
    { id: "outreach", label: "Outreach" },
    { id: "registration", label: "Registration" },
    { id: "purge", label: "Purge" },
    { id: "geography", label: "Geography" },
    { id: "zodiac", label: "Zodiac" },
    { id: "county", label: "County Explorer" }
  ];

  const formatter = new Intl.NumberFormat("en-US");
  const formatNumber = (value) => formatter.format(Number(value || 0));
  const formatPercent = (value) => `${Number(value || 0).toFixed(1)}%`;
  const byId = (id) => document.getElementById(id);

  const state = {
    data: null,
    activeSection: "overview",
    county: "all"
  };


  function adaptIntakeData(raw) {
    if (raw.overview) return raw;

    const currentRows = raw.geography?.currentByCounty || [];
    const registeredRows = raw.geography?.registeredSinceBaselineByCounty || [];
    const returnedRows = raw.geography?.returnedToCurrentFileByCounty || [];
    const ezRows = raw.geography?.ezAppMatchesByCounty || [];

    const valuesByCounty = new Map();

    function applyRows(rows, field) {
      rows.forEach((row) => {
        const county = row.county || "Unknown";
        const item = valuesByCounty.get(county) || {
          county,
          people: 0,
          contacted: 0,
          addedToCurrentVrvh: 0,
          active: 0,
          inactive: 0,
          returnedToCurrentFile: 0
        };

        item[field] = Number(row.count || 0);
        valuesByCounty.set(county, item);
      });
    }

    applyRows(currentRows, "people");
    applyRows(registeredRows, "addedToCurrentVrvh");
    applyRows(returnedRows, "returnedToCurrentFile");
    applyRows(ezRows, "contacted");

    const counties = [...valuesByCounty.values()]
      .sort((a, b) => b.people - a.people);

    const ez = raw.ezApp || {};
    const purge = raw.purge || {};
    const voterFile = raw.voterFile || {};

    return {
      meta: {
        ...raw.meta,
        title: "GLA Current Voter Dashboard"
      },

      overview: {
        totalPeople: voterFile.currentTotal || 0,
        addedToCurrentVrvh: voterFile.registeredSinceBaseline || 0,
        contacted: ez.matchedToCurrentFile || 0,
        contactRate: ez.matchRate || 0,
        counties: counties.length
      },

      voterFile: {
        summary: {
          totalPeople: voterFile.currentTotal || 0,
          active: voterFile.active || 0,
          inactive: voterFile.inactive || 0
        },
        registrationStatus: [
          { status: "Active", count: voterFile.active || 0 },
          { status: "Inactive", count: voterFile.inactive || 0 },
          {
            status: "Registered since December 2025",
            count: voterFile.registeredSinceBaseline || 0
          }
        ]
      },

      purge: {
        summary: {
          totalPeople: purge.removedSinceBaseline || 0,
          addedToCurrentVrvh: purge.returnedToCurrentFile || 0
        },
        removedTrackingStatus: [
          {
            status: "Removed since December 2025",
            count: purge.removedSinceBaseline || 0
          },
          {
            status: "Returned to current VRVH",
            count: purge.returnedToCurrentFile || 0
          },
          {
            status: "Still missing from current VRVH",
            count: purge.stillMissingFromCurrentFile || 0
          }
        ]
      },

      outreach: {
        summary: {
          totalPeople: ez.usableSubmissions || 0,
          contacted: ez.matchedToCurrentFile || 0,
          notInGlaContactFile: ez.notFound || 0,
          contactRate: ez.matchRate || 0
        },
        contactStatus: [
          { status: "Usable EZ App submissions", count: ez.usableSubmissions || 0 },
          { status: "Matched to current VRVH", count: ez.matchedToCurrentFile || 0 },
          { status: "Not found", count: ez.notFound || 0 },
          { status: "Ambiguous match", count: ez.ambiguous || 0 }
        ]
      },

      registration: {
        summary: {
          totalPeople: ez.usableSubmissions || 0,
          addedToCurrentVrvh: ez.registeredOnOrAfterSubmission || 0,
          active: ez.matchedToCurrentFile || 0,
          inactive: ez.notFound || 0
        },
        changeStatus: [
          {
            status: "Registered on or after EZ App submission",
            count: ez.registeredOnOrAfterSubmission || 0
          },
          {
            status: "Registered before submission or date unavailable",
            count: ez.registeredBeforeSubmissionOrDateUnavailable || 0
          },
          { status: "Not found", count: ez.notFound || 0 }
        ]
      },

      tracking: {
        summary: {
          totalPeople: ez.usableSubmissions || 0,
          addedToCurrentVrvh: ez.registeredOnOrAfterSubmission || 0,
          notInGlaContactFile: ez.notFound || 0,
          counties: counties.length
        },
        sourceTotals: [
          {
            source: "GLA EZ App",
            people: ez.usableSubmissions || 0,
            addedToCurrentVrvh: ez.registeredOnOrAfterSubmission || 0,
            notInGlaContactFile: ez.notFound || 0
          }
        ],
        countyTotals: counties
      },

      geography: {
        counties
      }
    };
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function metricCard(label, value, detail = "") {
    return `
      <article class="metric-card">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
        ${detail ? `<small>${escapeHtml(detail)}</small>` : ""}
      </article>
    `;
  }

  function placeholder(title, detail) {
    return `
      <article class="placeholder-card">
        <span>Planned</span>
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(detail)}</p>
      </article>
    `;
  }

  function rowsToTable(columns, rows, emptyMessage = "No aggregate rows are available.") {
    if (!rows || !rows.length) {
      return `<p class="table-note">${escapeHtml(emptyMessage)}</p>`;
    }

    const head = columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("");
    const body = rows
      .map((row) => {
        const cells = columns
          .map((column) => {
            const raw = column.render ? column.render(row) : row[column.key];
            return `<td>${escapeHtml(raw)}</td>`;
          })
          .join("");
        return `<tr>${cells}</tr>`;
      })
      .join("");

    return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  }

  function selectedCounty() {
    if (state.county === "all") return null;
    return (state.data?.geography?.counties || []).find((row) => row.county === state.county) || null;
  }

  function allCounties() {
    return [...(state.data?.geography?.counties || [])].sort((a, b) => {
      const countyA = String(a.county || "");
      const countyB = String(b.county || "");
      return countyA.localeCompare(countyB);
    });
  }

  function filteredCounties(limit = null) {
    const county = selectedCounty();
    const rows = county ? [county] : state.data?.geography?.counties || [];
    return typeof limit === "number" ? rows.slice(0, limit) : rows;
  }

  function renderNav() {
    const nav = byId("nav");
    if (!nav) return;

    nav.innerHTML = sections
      .map(
        (section) => `
          <button class="nav-button${state.activeSection === section.id ? " active" : ""}" data-section="${section.id}" type="button">
            ${escapeHtml(section.label)}
          </button>
        `
      )
      .join("");

    nav.querySelectorAll(".nav-button").forEach((button) => {
      button.addEventListener("click", () => {
        state.activeSection = button.dataset.section;
        render();
      });
    });
  }

  function renderFilters() {
    const select = byId("countyFilter");
    if (!select) return;

    const options = allCounties()
      .map((row) => `<option value="${escapeHtml(row.county)}">${escapeHtml(row.county)}</option>`)
      .join("");
    select.innerHTML = `<option value="all">All counties</option>${options}`;
    select.value = state.county;
    select.addEventListener("change", (event) => {
      state.county = event.target.value;
      render();
    });
  }

  function renderPrivacyNotice() {
    const notice = byId("privacyNotice");
    if (!notice || !state.data) return;

    const generatedAt = state.data.meta?.generatedAt || "Unknown";
    notice.innerHTML = `
      <strong>Public aggregate data only.</strong>
      This dashboard is generated from current aggregate comparisons in <code>intake-comparison.json</code>.
      Last updated: <time>${escapeHtml(generatedAt)}</time>.
    `;
  }

  function renderOverview() {
    const overview = state.data.overview || {};
    const voterFile = state.data.voterFile?.summary || {};
    const countyCount = overview.counties || allCounties().length;
    const rows = filteredCounties(10);

    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Executive Overview</p>
            <h2>Statewide Public Summary</h2>
          </div>
          <span class="status-pill">${escapeHtml(state.data.meta?.privacy || "aggregate-only")}</span>
        </div>

        <div class="metric-grid hero-kpis">
          ${metricCard("Total People", formatNumber(overview.totalPeople), "Rows included in the aggregate source")}
          ${metricCard("Added to Current VRVH", formatNumber(overview.addedToCurrentVrvh), "Aggregate change status")}
          ${metricCard("Contact Rate", formatPercent(overview.contactRate), `${formatNumber(overview.contacted)} contacted`)}
          ${metricCard("Total Counties", formatNumber(countyCount), "County-level rollups available")}
          ${metricCard("Active Voters", formatNumber(voterFile.active), "Registration status A")}
          ${metricCard("Last Updated", state.data.meta?.generatedAt || "Unknown", "Generated public JSON")}
        </div>

        <div class="two-column">
          <section class="panel">
            <div class="panel-heading">
              <h3>Top Counties by People</h3>
              <span>Aggregate</span>
            </div>
            ${rowsToTable(
              [
                { key: "county", label: "County" },
                { key: "people", label: "People", render: (row) => formatNumber(row.people) },
                { key: "contacted", label: "Contacted", render: (row) => formatNumber(row.contacted) },
                { key: "addedToCurrentVrvh", label: "Added to VRVH", render: (row) => formatNumber(row.addedToCurrentVrvh) }
              ],
              rows
            )}
          </section>
          <section class="panel">
            <div class="panel-heading">
              <h3>Executive Notes</h3>
              <span>Roadmap</span>
            </div>
            <div class="placeholder-grid single">
              ${placeholder("Trend lines", "Future sprint: add historical aggregate snapshots once the build pipeline emits time-series rollups.")}
              ${placeholder("Targets", "Future sprint: add goal tracking after campaign targets are approved for public display.")}
            </div>
          </section>
        </div>
      </section>
    `;
  }

  function renderOutreach() {
    const outreach = state.data.outreach || {};
    const sourceRows = state.data.tracking?.sourceTotals || [];

    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Outreach</p>
            <h2>Contact Coverage</h2>
          </div>
          <span class="status-pill">${formatPercent(outreach.summary?.contactRate)} contact rate</span>
        </div>

        <div class="metric-grid compact">
          ${metricCard("Total People", formatNumber(outreach.summary?.totalPeople))}
          ${metricCard("Contacted", formatNumber(outreach.summary?.contacted))}
          ${metricCard("Not in GLA Contact File", formatNumber(outreach.summary?.notInGlaContactFile))}
          ${metricCard("Contact Rate", formatPercent(outreach.summary?.contactRate))}
        </div>

        <div class="two-column">
          <section class="panel">
            <div class="panel-heading">
              <h3>Contact Status</h3>
              <span>Aggregate counts</span>
            </div>
            ${rowsToTable(
              [
                { key: "status", label: "Status" },
                { key: "count", label: "Count", render: (row) => formatNumber(row.count) }
              ],
              outreach.contactStatus || []
            )}
          </section>
          <section class="panel">
            <div class="panel-heading">
              <h3>Updated GLA Contact Source</h3>
              <span>Aggregate source totals</span>
            </div>
            ${rowsToTable(
              [
                { key: "source", label: "Source" },
                { key: "people", label: "People", render: (row) => formatNumber(row.people) },
                { key: "addedToCurrentVrvh", label: "Added to VRVH", render: (row) => formatNumber(row.addedToCurrentVrvh) }
              ],
              sourceRows
            )}
          </section>
        </div>

        <div class="placeholder-grid">
          ${placeholder("Outreach timeline", "Future sprint: display weekly aggregate activity after scheduled exports are available.")}
          ${placeholder("Channel mix", "Future sprint: compare public-safe text, mail, phone, and canvass totals.")}
        </div>
      </section>
    `;
  }

  function renderRegistration() {
    const registration = state.data.registration || {};
    const rows = filteredCounties(14);

    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Registration</p>
            <h2>VRVH Movement</h2>
          </div>
          <span class="status-pill">${formatNumber(registration.summary?.addedToCurrentVrvh)} added</span>
        </div>

        <div class="metric-grid compact">
          ${metricCard("Total People", formatNumber(registration.summary?.totalPeople))}
          ${metricCard("Added to Current VRVH", formatNumber(registration.summary?.addedToCurrentVrvh))}
          ${metricCard("Active", formatNumber(registration.summary?.active))}
          ${metricCard("Inactive", formatNumber(registration.summary?.inactive))}
        </div>

        <div class="two-column">
          <section class="panel">
            <div class="panel-heading">
              <h3>Change Status</h3>
              <span>Aggregate counts</span>
            </div>
            ${rowsToTable(
              [
                { key: "status", label: "Status" },
                { key: "count", label: "Count", render: (row) => formatNumber(row.count) }
              ],
              registration.changeStatus || []
            )}
          </section>
          <section class="panel">
            <div class="panel-heading">
              <h3>County Registration Rollup</h3>
              <span>${state.county === "all" ? "Top counties" : "Selected county"}</span>
            </div>
            ${rowsToTable(
              [
                { key: "county", label: "County" },
                { key: "active", label: "Active", render: (row) => formatNumber(row.active) },
                { key: "inactive", label: "Inactive", render: (row) => formatNumber(row.inactive) },
                { key: "addedToCurrentVrvh", label: "Added", render: (row) => formatNumber(row.addedToCurrentVrvh) }
              ],
              rows
            )}
          </section>
        </div>

        <div class="placeholder-grid">
          ${placeholder("Attribution model", "Future sprint: add approved aggregate attribution once methodology is finalized.")}
          ${placeholder("Registration funnel", "Future sprint: show public-safe conversion steps without person-level histories.")}
        </div>
      </section>
    `;
  }

  function renderPurge() {
    const purge = state.data.purge || {};

    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Purge</p>
            <h2>Removed Voter Tracking</h2>
          </div>
          <span class="status-pill">Aggregate only</span>
        </div>

        <div class="metric-grid compact">
          ${metricCard("Total People", formatNumber(purge.summary?.totalPeople))}
          ${metricCard("Added to Current VRVH", formatNumber(purge.summary?.addedToCurrentVrvh))}
          ${metricCard("Tracking Statuses", formatNumber((purge.removedTrackingStatus || []).length))}
          ${metricCard("Current View", state.county === "all" ? "Statewide" : state.county)}
        </div>

        <section class="panel">
          <div class="panel-heading">
            <h3>Removed Tracking Status</h3>
            <span>Public counts</span>
          </div>
          ${rowsToTable(
            [
              { key: "status", label: "Status" },
              { key: "count", label: "Count", render: (row) => formatNumber(row.count) }
            ],
            purge.removedTrackingStatus || []
          )}
        </section>

        <div class="placeholder-grid">
          ${placeholder("Purge trend", "Future sprint: compare public aggregate snapshots over time.")}
          ${placeholder("Recovery view", "Future sprint: display returned-to-VRVH aggregate counts after snapshot policy is approved.")}
        </div>
      </section>
    `;
  }

  function renderGeography() {
    const rows = filteredCounties(18);

    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Geography</p>
            <h2>County Rollups</h2>
          </div>
          <span class="status-pill">${formatNumber(allCounties().length)} counties</span>
        </div>

        <div class="county-grid">
          ${rows
            .map((row) => {
              const rate = row.people ? (row.contacted / row.people) * 100 : 0;
              return `
                <article class="county-tile">
                  <div>
                    <strong>${escapeHtml(row.county)}</strong>
                    <span>${formatPercent(rate)} contacted</span>
                  </div>
                  <dl>
                    <div><dt>People</dt><dd>${formatNumber(row.people)}</dd></div>
                    <div><dt>Added</dt><dd>${formatNumber(row.addedToCurrentVrvh)}</dd></div>
                    <div><dt>Active</dt><dd>${formatNumber(row.active)}</dd></div>
                    <div><dt>Inactive</dt><dd>${formatNumber(row.inactive)}</dd></div>
                  </dl>
                </article>
              `;
            })
            .join("")}
        </div>

        <div class="placeholder-grid">
          ${placeholder("Map view", "Future sprint: add a public-safe county map after choosing a mapping library and color scale.")}
        </div>
      </section>
    `;
  }

  function renderZodiac() {
    const zodiac = state.data.zodiac;
    if (!zodiac) {
      return `
        <section class="dashboard-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">Zodiac</p>
              <h2>Aggregate Zodiac Summary</h2>
            </div>
            <span class="status-pill">Not loaded</span>
          </div>
          <section class="panel empty-state">
            <h3>Zodiac aggregate files are not loaded</h3>
            <p>Add the approved aggregate Zodiac workbooks and rebuild the public dashboard. Birth dates and person-level rows must never be published.</p>
          </section>
        </section>
      `;
    }

    const countyRow = state.county === "all"
      ? null
      : (zodiac.countySummary || []).find((row) => row.county === state.county);
    const scope = countyRow || zodiac.summary || {};
    const countyRows = countyRow ? [countyRow] : (zodiac.countySummary || []).slice(0, 15);

    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Zodiac</p>
            <h2>Aggregate Zodiac Summary</h2>
          </div>
          <span class="status-pill">${state.county === "all" ? "Statewide" : escapeHtml(state.county)}</span>
        </div>

        <div class="metric-grid hero-kpis">
          ${metricCard("Active Registered Voters", formatNumber(scope.activeRegisteredVoters))}
          ${metricCard("Recently Voted", formatNumber(scope.recentlyVoted))}
          ${metricCard("Recently Voted Rate", formatPercent(scope.recentlyVotedPct))}
          ${metricCard("Did Not Recently Vote", formatNumber(scope.didNotRecentlyVote))}
          ${metricCard("Zodiac Signs", formatNumber(zodiac.summary?.zodiacSigns))}
          ${metricCard("Counties", formatNumber(zodiac.summary?.countyCount))}
        </div>

        <div class="two-column">
          <section class="panel">
            <div class="panel-heading">
              <h3>Statewide by Zodiac Sign</h3>
              <span>Aggregate counts</span>
            </div>
            ${rowsToTable(
              [
                { key: "zodiacSign", label: "Sign" },
                { key: "activeRegisteredVoters", label: "Active", render: (row) => formatNumber(row.activeRegisteredVoters) },
                { key: "recentlyVoted", label: "Recently voted", render: (row) => formatNumber(row.recentlyVoted) },
                { key: "recentlyVotedPct", label: "Rate", render: (row) => formatPercent(row.recentlyVotedPct) }
              ],
              zodiac.statewideBySign || []
            )}
          </section>
          <section class="panel">
            <div class="panel-heading">
              <h3>Pulaski by Zodiac Sign</h3>
              <span>Aggregate counts</span>
            </div>
            ${rowsToTable(
              [
                { key: "zodiacSign", label: "Sign" },
                { key: "activeRegisteredVoters", label: "Active", render: (row) => formatNumber(row.activeRegisteredVoters) },
                { key: "recentlyVoted", label: "Recently voted", render: (row) => formatNumber(row.recentlyVoted) },
                { key: "recentlyVotedPct", label: "Rate", render: (row) => formatPercent(row.recentlyVotedPct) }
              ],
              zodiac.pulaskiBySign || []
            )}
          </section>
        </div>

        <section class="panel stacked-panel">
          <div class="panel-heading">
            <h3>County Zodiac Rollup</h3>
            <span>${state.county === "all" ? "Top counties by recent voting rate" : "Selected county"}</span>
          </div>
          ${rowsToTable(
            [
              { key: "county", label: "County" },
              { key: "activeRegisteredVoters", label: "Active", render: (row) => formatNumber(row.activeRegisteredVoters) },
              { key: "recentlyVoted", label: "Recently voted", render: (row) => formatNumber(row.recentlyVoted) },
              { key: "recentlyVotedPct", label: "Rate", render: (row) => formatPercent(row.recentlyVotedPct) },
              { key: "topZodiacByRecentlyVotedPct", label: "Top sign" }
            ],
            countyRows
          )}
        </section>
      </section>
    `;
  }

  function renderCountyExplorer() {
    const county = selectedCounty();

    if (!county) {
      return `
        <section class="dashboard-section">
          <div class="section-heading">
            <div>
              <p class="eyebrow">County Explorer</p>
              <h2>Select a County</h2>
            </div>
            <span class="status-pill">All counties selected</span>
          </div>
          <section class="panel empty-state">
            <h3>Choose a county from the filter</h3>
            <p>The explorer will show one county at a time using the aggregate county rollups already present in <code>intake-comparison.json</code>.</p>
          </section>
        </section>
      `;
    }

    const contactRate = county.people ? (county.contacted / county.people) * 100 : 0;
    return `
      <section class="dashboard-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">County Explorer</p>
            <h2>${escapeHtml(county.county)} County</h2>
          </div>
          <span class="status-pill">${formatPercent(contactRate)} contacted</span>
        </div>

        <div class="metric-grid hero-kpis">
          ${metricCard("People", formatNumber(county.people))}
          ${metricCard("Added to Current VRVH", formatNumber(county.addedToCurrentVrvh))}
          ${metricCard("Contacted", formatNumber(county.contacted))}
          ${metricCard("Active", formatNumber(county.active))}
          ${metricCard("Inactive", formatNumber(county.inactive))}
          ${metricCard("Contact Rate", formatPercent(contactRate))}
        </div>

        <div class="placeholder-grid">
          ${placeholder("County history", "Future sprint: add aggregate trend snapshots for the selected county.")}
          ${placeholder("Peer comparison", "Future sprint: compare this county against similar aggregate county cohorts.")}
        </div>
      </section>
    `;
  }

  function renderActiveSection() {
    switch (state.activeSection) {
      case "outreach":
        return renderOutreach();
      case "registration":
        return renderRegistration();
      case "purge":
        return renderPurge();
      case "geography":
        return renderGeography();
      case "zodiac":
        return renderZodiac();
      case "county":
        return renderCountyExplorer();
      case "overview":
      default:
        return renderOverview();
    }
  }

  function render() {
    renderNav();
    renderPrivacyNotice();
    const container = byId("sections");
    if (container) container.innerHTML = renderActiveSection();
  }

  function renderLoading() {
    const container = byId("sections");
    if (container) {
      container.innerHTML = `
        <section class="dashboard-section">
          <div class="loading-panel">
            <strong>Loading public dashboard data...</strong>
            <span>Reading aggregate JSON from ${escapeHtml(DATA_URL)}.</span>
          </div>
        </section>
      `;
    }
  }

  function renderError(error) {
    const container = byId("sections");
    const notice = byId("privacyNotice");
    if (notice) {
      notice.innerHTML = `<strong>Dashboard data did not load.</strong> The public JSON file is still the required source.`;
    }
    if (container) {
      container.innerHTML = `
        <section class="dashboard-section">
          <section class="panel empty-state">
            <h2>Public data unavailable</h2>
            <p>The dashboard could not read <code>${escapeHtml(DATA_URL)}</code>. If this page is open as a local file, run it through a local web server or view the published GitHub Pages site.</p>
            <p class="error-text">${escapeHtml(error.message || error)}</p>
          </section>
        </section>
      `;
    }
  }

  async function loadData() {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} while loading ${DATA_URL}`);
    }
    return response.json();
  }

  async function init() {
    renderNav();
    renderLoading();
    try {
      state.data = adaptIntakeData(await loadData());
      renderFilters();
      render();
    } catch (error) {
      renderError(error);
    }
  }

  init();
})();
