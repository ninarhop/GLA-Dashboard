(() => {
const data = window.GLA_DASHBOARD_DATA || {};
const websiteData = window.GLA_WEBSITE_DATA || {};

if (websiteData.primary2026) data.primary2026 = websiteData.primary2026;
if (websiteData.vrLookup) data.vrLookup = websiteData.vrLookup;
if (websiteData.zodiac) data.zodiac = websiteData.zodiac;
if (websiteData.outreachTracking) data.outreachTracking = websiteData.outreachTracking;

const formatNumber = new Intl.NumberFormat("en-US").format;
const formatPercent = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`;
const byId = (id) => document.getElementById(id);

const state = {
  county: "all"
};

function metric(label, value, meta = "") {
  return `
    <article class="metric-card">
      <span>${label}</span>
      <strong>${typeof value === "number" ? formatNumber(value) : value}</strong>
      ${meta ? `<small>${meta}</small>` : ""}
    </article>
  `;
}

function pendingPanel(title, message) {
  return `
    <article class="metric-card">
      <span>${title}</span>
      <strong>Pending</strong>
      <small>${message}</small>
    </article>
  `;
}

function rowsToTable(columns, rows) {
  const header = columns.map((column) => `<th>${column.label}</th>`).join("");
  const body = rows
    .map((row) => {
      const cells = columns.map((column) => `<td>${column.render ? column.render(row) : row[column.key]}</td>`).join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");
  return `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
}

function selectedCountyRow(rows) {
  return state.county === "all" ? null : rows.find((row) => row.county === state.county);
}

function renderFilters() {
  const counties = Array.from(
    new Set([
      ...(data.primary2026?.countyTotals || []).map((row) => row.county),
      ...(data.vrLookup?.counties || []).map((row) => row.county),
      ...(data.zodiac?.countySummary || []).map((row) => row.county),
      ...(data.outreachTracking?.countySummary || []).map((row) => row.county)
    ])
  ).sort();

  const countyFilter = byId("countyFilter");
  if (countyFilter) {
    countyFilter.innerHTML = `<option value="all">All counties</option>${counties
      .map((county) => `<option value="${county}">${county}</option>`)
      .join("")}`;
  }
}

function buildHomeKpis() {
  const summary = data.outreachTracking?.summary;
  if (!summary) {
    return [
      { label: "Current Purge List Size", value: "Pending" },
      { label: "Contacted Voters", value: "Pending" },
      { label: "Untouched Voters", value: "Pending" },
      { label: "Contact Rate %", value: "Pending" },
      { label: "Total Texts", value: "Pending" },
      { label: "Total Mailers", value: "Pending" },
      { label: "Total Registrations Influenced", value: "Pending" },
      { label: "Conversion Rate %", value: "Pending" }
    ];
  }
  return [
    { label: "Current Purge List Size", value: summary.currentPurgeListSize },
    { label: "Contacted Voters", value: summary.contactedVoters },
    { label: "Untouched Voters", value: summary.untouchedVoters },
    { label: "Contact Rate %", value: formatPercent(summary.contactRate / 100) },
    { label: "Total Texts", value: summary.totalTexts },
    { label: "Total Mailers", value: summary.totalMailers },
    { label: "Total Registrations Influenced", value: summary.registrationsInfluenced },
    { label: "Conversion Rate %", value: formatPercent(summary.conversionRate / 100) }
  ];
}

function renderOverview() {
  byId("sampleDate").textContent = data.outreachTracking
    ? "Public aggregate dashboard"
    : "Waiting for aggregate data";
  byId("metricGrid").innerHTML = buildHomeKpis()
    .map((item) => metric(item.label, item.value))
    .join("");
}

function renderTracking() {
  const tracking = data.outreachTracking;
  if (!tracking) {
    byId("trackingSource").textContent = "No tracking file loaded";
    byId("trackingMetrics").innerHTML = pendingPanel("Tracking source", "Waiting for aggregate tracking data");
    byId("trackingSourceTable").innerHTML = "";
    byId("trackingCountyTable").innerHTML = "";
    return;
  }

  const countyRow = selectedCountyRow(tracking.countySummary || []);
  const summary = tracking.summary;
  const influencedCount = countyRow ? countyRow.registrationsInfluenced : summary.registrationsInfluenced;
  const countyRows = countyRow ? [countyRow] : (tracking.countySummary || []).slice(0, 20);

  byId("trackingSource").textContent = `${formatNumber(tracking.source.rowCount)} aggregate source rows`;
  byId("trackingMetrics").innerHTML = [
    metric("Added to current VRVH", countyRow ? countyRow.addedToCurrentVrvh : summary.addedToCurrentVrvh),
    metric("Added after GLA touch", influencedCount),
    metric("GLA touches", summary.glaTouches || summary.purgeListContacts || summary.contactedVoters),
    metric("Current purge GLA touches", summary.currentPurgeGlaTouches || summary.contactedVoters)
  ].join("");

  byId("trackingSourceTable").innerHTML = `
    <h3>GLA List Type</h3>
    ${rowsToTable(
      [
        { key: "listType", label: "List Type" },
        { key: "count", label: "Rows", render: (row) => formatNumber(row.count) }
      ],
      tracking.listTypeCounts || []
    )}
    <h3>GLA Touch Source</h3>
    ${rowsToTable(
      [
        { key: "source", label: "Source" },
        { key: "count", label: "Touches", render: (row) => formatNumber(row.count) }
      ],
      tracking.glaTouchSourceCounts || tracking.sourceCounts || []
    )}
  `;

  byId("trackingCountyTable").innerHTML = rowsToTable(
    [
      { key: "county", label: "County" },
      { key: "glaTouches", label: "GLA touches", render: (row) => formatNumber(row.glaTouches || 0) },
      { key: "currentPurgeGlaTouches", label: "Current purge touches", render: (row) => formatNumber(row.currentPurgeGlaTouches || 0) },
      { key: "addedToCurrentVrvh", label: "Added to VRVH", render: (row) => formatNumber(row.addedToCurrentVrvh) },
      { key: "registrationsInfluenced", label: "Added after GLA touch", render: (row) => formatNumber(row.registrationsInfluenced) },
      { key: "influencedRate", label: "Conversion", render: (row) => formatPercent(row.influencedRate / 100) }
    ],
    countyRows
  );
}

function renderVoterFile() {
  const vr = data.vrLookup;
  if (!vr) {
    byId("voterFileSource").textContent = "No aggregate voter file data";
    byId("voterFileMetrics").innerHTML = pendingPanel("Voter records", "Waiting for county-level data");
    byId("voterFileCountyTable").innerHTML = "";
    byId("lookupActivityTable").innerHTML = "";
    return;
  }

  const countyRow = selectedCountyRow(vr.counties || []);
  byId("voterFileSource").textContent = "Aggregate voter file summary";
  byId("voterFileMetrics").innerHTML = [
    metric("Voter records", countyRow ? countyRow.voters : vr.summary.voterRecords),
    metric("Counties", vr.summary.countyCount),
    metric("Lookup submissions", vr.summary.lookupSubmissions),
    metric("Easy App clicks", vr.summary.easyAppClicks)
  ].join("");

  byId("voterFileCountyTable").innerHTML = rowsToTable(
    [
      { key: "county", label: "County" },
      { key: "voters", label: "Voter records", render: (row) => formatNumber(row.voters) }
    ],
    countyRow ? [countyRow] : (vr.counties || []).slice(0, 20)
  );

  byId("lookupActivityTable").innerHTML = rowsToTable(
    [
      { key: "matchResult", label: "Match result" },
      { key: "count", label: "Submissions", render: (row) => formatNumber(row.count) }
    ],
    vr.lookupSummary?.length ? vr.lookupSummary : [{ matchResult: "No submissions loaded", count: 0 }]
  );
}

function renderPurge() {
  byId("purgeMetrics").innerHTML = [
    pendingPanel("Purge additions", "Needs scheduled aggregate snapshots"),
    pendingPanel("Repeat appearances", "Needs at least two aggregate snapshots"),
    pendingPanel("Removed from purge", "Needs comparison snapshots"),
    pendingPanel("Returned to VRVH", "Needs aggregate VRVH history")
  ].join("");
  byId("purgeTimeline").innerHTML = `<p class="brand-subtitle">Purge trend snapshots are not loaded in this public copy.</p>`;
}

function renderOutreach() {
  byId("methodMix").innerHTML = [
    pendingPanel("Text messages", "Waiting for aggregate outreach exports"),
    pendingPanel("Mailers", "Waiting for aggregate mailer exports"),
    pendingPanel("Emails", "Waiting for aggregate email exports"),
    pendingPanel("Canvassing", "Waiting for aggregate canvass exports")
  ].join("");
  byId("touchTimeline").innerHTML = `<p class="brand-subtitle">Outreach timeline exports are not loaded in this public copy.</p>`;
}

function renderRegistration() {
  const tracking = data.outreachTracking;
  const easyApp = tracking?.easyApp;
  if (!tracking || !easyApp) {
    byId("demographicTable").innerHTML = `<p class="brand-subtitle">Easy App aggregate data is not loaded in this public copy.</p>`;
    byId("attributionTable").innerHTML = rowsToTable(
      [
        { key: "source", label: "Aggregate source" },
        { key: "status", label: "Status" }
      ],
      [
        { source: "EZ app registrations", status: "Needed" },
        { source: "Future registration systems", status: "Needed" },
        { source: "Matched outreach totals", status: "Needed" }
      ]
    );
    return;
  }

  const countyRow = selectedCountyRow(tracking.countySummary || []);
  const summary = tracking.summary;
  const touches = countyRow ? countyRow.glaTouches : summary.glaTouches;
  const submissions = countyRow ? countyRow.easyAppSubmissions : summary.easyAppSubmissions;
  const currentVrvh = countyRow ? countyRow.easyAppCurrentVrvh : summary.easyAppCurrentVrvh;
  const addedToCurrent = countyRow ? countyRow.registrationsInfluenced : summary.registrationsInfluenced;
  const currentPurge = countyRow ? countyRow.currentPurgeGlaTouches : summary.currentPurgeGlaTouches;
  const submissionRate = countyRow ? countyRow.easyAppSubmissionRate : summary.easyAppSubmissionRate;
  const conversionRate = countyRow ? countyRow.influencedRate : summary.conversionRate;

  byId("demographicTable").innerHTML = `
    <div class="metric-grid compact">
      ${[
        metric("GLA touches", touches),
        metric("Easy App submissions", submissions),
        metric("Easy App current VRVH", currentVrvh),
        metric("Registrations influenced", addedToCurrent),
        metric("Current purge GLA touches", currentPurge),
        metric("Submission rate", formatPercent(submissionRate / 100)),
        metric("Conversion rate", formatPercent(conversionRate / 100))
      ].join("")}
    </div>
    ${rowsToTable(
      [
        { key: "county", label: "County" },
        { key: "glaTouches", label: "GLA touches", render: (row) => formatNumber(row.glaTouches || 0) },
        { key: "registrationsInfluenced", label: "Registrations influenced", render: (row) => formatNumber(row.registrationsInfluenced || 0) },
        { key: "influencedRate", label: "Conversion", render: (row) => formatPercent((row.influencedRate || 0) / 100) },
        { key: "easyAppSubmissions", label: "Easy App submissions", render: (row) => formatNumber(row.easyAppSubmissions || 0) },
        { key: "easyAppCurrentVrvh", label: "Easy App current VRVH", render: (row) => formatNumber(row.easyAppCurrentVrvh || 0) }
      ],
      countyRow ? [countyRow] : (tracking.countySummary || []).slice(0, 20)
    )}
  `;

  byId("attributionTable").innerHTML = rowsToTable(
    [
      { key: "source", label: "Aggregate source" },
      { key: "count", label: "Rows", render: (row) => formatNumber(row.count) }
    ],
    [
      ...(easyApp.currentVrvhStatusCounts || []).map((row) => ({
        source: row.currentVrvhStatus,
        count: row.count
      })),
      ...(easyApp.submissionCounts || []).map((row) => ({
        source: `Submission ${row.submissionStatus}`,
        count: row.count
      }))
    ]
  );
}

function renderPrimary2026() {
  const primary = data.primary2026;
  if (!primary) {
    byId("primarySource").textContent = "No primary data";
    byId("primaryMetrics").innerHTML = pendingPanel("Primary data", "Waiting for aggregate primary data");
    byId("primaryAgeBars").innerHTML = "";
    byId("primaryGenderTable").innerHTML = "";
    byId("primaryCountyTable").innerHTML = "";
    return;
  }

  const countyRow = selectedCountyRow(primary.countyTotals || []);
  const scope = countyRow || primary.summary;
  byId("primarySource").textContent = "2026 primary aggregate data";
  byId("primaryMetrics").innerHTML = [
    metric("Registered in file", scope.totalRegistered),
    metric("2026 primary voters", scope.totalPrimaryVoters),
    metric("Primary turnout", formatPercent((scope.totalTurnoutPct || 0) / 100)),
    metric("Counties", countyRow ? countyRow.county : primary.summary.counties),
    metric("Male turnout", formatPercent((scope.maleTurnoutPct || 0) / 100)),
    metric("Female turnout", formatPercent((scope.femaleTurnoutPct || 0) / 100))
  ].join("");

  const ageRows = countyRow
    ? (primary.rows || []).filter((row) => row.county === countyRow.county)
    : primary.byAge || [];
  const maxAgeTurnout = Math.max(...ageRows.map((row) => row.totalTurnoutPct || 0), 1);
  byId("primaryAgeBars").innerHTML = ageRows
    .map((row) => {
      const width = Math.max(4, Math.round(((row.totalTurnoutPct || 0) / maxAgeTurnout) * 100));
      return `
        <div class="bar-row">
          <div class="bar-label">
            <strong>${row.ageRange}</strong>
            <span>${formatNumber(row.totalPrimaryVoters)} voters</span>
          </div>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <span class="bar-rate">${formatPercent((row.totalTurnoutPct || 0) / 100)}</span>
        </div>
      `;
    })
    .join("");

  byId("primaryGenderTable").innerHTML = rowsToTable(
    [
      { key: "group", label: "Group" },
      { key: "registered", label: "Registered", render: (row) => formatNumber(row.registered) },
      { key: "voters", label: "Primary voters", render: (row) => formatNumber(row.voters) },
      { key: "turnout", label: "Turnout", render: (row) => formatPercent(row.turnout / 100) }
    ],
    [
      { group: "Male", registered: scope.maleRegistered, voters: scope.malePrimaryVoters, turnout: scope.maleTurnoutPct },
      { group: "Female", registered: scope.femaleRegistered, voters: scope.femalePrimaryVoters, turnout: scope.femaleTurnoutPct }
    ]
  );

  byId("primaryCountyTable").innerHTML = rowsToTable(
    [
      { key: "county", label: "County" },
      { key: "totalRegistered", label: "Registered", render: (row) => formatNumber(row.totalRegistered) },
      { key: "totalPrimaryVoters", label: "Primary voters", render: (row) => formatNumber(row.totalPrimaryVoters) },
      { key: "totalTurnoutPct", label: "Turnout", render: (row) => formatPercent(row.totalTurnoutPct / 100) },
      { key: "topAgeRangeByTurnout", label: "Top age range" }
    ],
    countyRow ? [countyRow] : (primary.countyTotals || []).slice(0, 15)
  );
}

function renderZodiac() {
  const zodiac = data.zodiac;
  if (!zodiac) {
    byId("zodiacSource").textContent = "No zodiac data";
    byId("zodiacMetrics").innerHTML = pendingPanel("Zodiac summary", "Waiting for aggregate zodiac data");
    byId("zodiacStatewideBars").innerHTML = "";
    byId("zodiacPulaskiTable").innerHTML = "";
    byId("zodiacCountyTable").innerHTML = "";
    return;
  }

  const countyRow = selectedCountyRow(zodiac.countySummary || []);
  const scope = countyRow || zodiac.summary;
  byId("zodiacSource").textContent = "Aggregate zodiac data";
  byId("zodiacMetrics").innerHTML = [
    metric("Active registered voters", scope.activeRegisteredVoters),
    metric("Recently voted", scope.recentlyVoted),
    metric("Recently voted rate", formatPercent((scope.recentlyVotedPct || 0) / 100)),
    metric("Did not recently vote", scope.didNotRecentlyVote),
    metric("Zodiac signs", zodiac.summary.zodiacSigns),
    metric("Pulaski rows", zodiac.summary.pulaskiRows)
  ].join("");

  const signRows = zodiac.statewideBySign || [];
  const maxRecentPct = Math.max(...signRows.map((row) => row.recentlyVotedPct || 0), 1);
  byId("zodiacStatewideBars").innerHTML = signRows
    .map((row) => {
      const width = Math.max(4, Math.round(((row.recentlyVotedPct || 0) / maxRecentPct) * 100));
      return `
        <div class="bar-row">
          <div class="bar-label">
            <strong>${row.zodiacSign}</strong>
            <span>${formatNumber(row.recentlyVoted)} recently voted</span>
          </div>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <span class="bar-rate">${formatPercent((row.recentlyVotedPct || 0) / 100)}</span>
        </div>
      `;
    })
    .join("");

  byId("zodiacPulaskiTable").innerHTML = rowsToTable(
    [
      { key: "zodiacSign", label: "Sign" },
      { key: "activeRegisteredVoters", label: "Active", render: (row) => formatNumber(row.activeRegisteredVoters) },
      { key: "recentlyVoted", label: "Recently voted", render: (row) => formatNumber(row.recentlyVoted) },
      { key: "recentlyVotedPct", label: "Rate", render: (row) => formatPercent(row.recentlyVotedPct / 100) }
    ],
    (zodiac.pulaskiBySign || []).slice(0, 12)
  );

  byId("zodiacCountyTable").innerHTML = rowsToTable(
    [
      { key: "county", label: "County" },
      { key: "activeRegisteredVoters", label: "Active", render: (row) => formatNumber(row.activeRegisteredVoters) },
      { key: "recentlyVoted", label: "Recently voted", render: (row) => formatNumber(row.recentlyVoted) },
      { key: "recentlyVotedPct", label: "Rate", render: (row) => formatPercent(row.recentlyVotedPct / 100) },
      { key: "topZodiacByRecentlyVotedPct", label: "Top sign" }
    ],
    countyRow ? [countyRow] : (zodiac.countySummary || []).slice(0, 20)
  );
}

function renderGeography() {
  const primary = data.primary2026;
  const vr = data.vrLookup;
  const zodiac = data.zodiac;
  const counties = Array.from(new Set([
    ...(primary?.countyTotals || []).map((row) => row.county),
    ...(vr?.counties || []).map((row) => row.county),
    ...(zodiac?.countySummary || []).map((row) => row.county)
  ]));
  if (!counties.length) {
    byId("countyHeatmap").innerHTML = `<p class="brand-subtitle">No county-level aggregate data has been loaded yet.</p>`;
    return;
  }

  const selected = state.county === "all" ? null : state.county;
  const rows = counties
    .filter((county) => !selected || county === selected)
    .map((county) => {
      const primaryRow = primary?.countyTotals.find((row) => row.county === county);
      const vrRow = vr?.counties.find((row) => row.county === county);
      const zodiacRow = zodiac?.countySummary.find((row) => row.county === county);
      return {
        county,
        primaryVoters: primaryRow?.totalPrimaryVoters || 0,
        primaryTurnoutPct: primaryRow?.totalTurnoutPct || 0,
        vrVoters: vrRow?.voters || 0,
        zodiacRecentlyVotedPct: zodiacRow?.recentlyVotedPct || 0,
        topAgeRangeByTurnout: primaryRow?.topAgeRangeByTurnout || "Not loaded",
        topZodiacByRecentlyVotedPct: zodiacRow?.topZodiacByRecentlyVotedPct || "Not loaded"
      };
    })
    .sort((a, b) => (b.primaryTurnoutPct || b.vrVoters) - (a.primaryTurnoutPct || a.vrVoters));
  const shownRows = selected ? rows : rows.slice(0, 18);
  const maxTurnout = Math.max(...shownRows.map((county) => county.primaryTurnoutPct || 0), 1);
  byId("countyHeatmap").innerHTML = shownRows
    .map((county) => {
      const strength = Math.max(0.18, (county.primaryTurnoutPct || 0) / maxTurnout);
      return `
        <article class="county-tile" style="--strength:${strength}">
          <div>
            <strong>${county.county}</strong>
            <span>Age: ${county.topAgeRangeByTurnout} | Zodiac: ${county.topZodiacByRecentlyVotedPct}</span>
          </div>
          <dl>
            <div><dt>VR records</dt><dd>${county.vrVoters ? formatNumber(county.vrVoters) : "Not loaded"}</dd></div>
            <div><dt>Primary voters</dt><dd>${county.primaryVoters ? formatNumber(county.primaryVoters) : "Not loaded"}</dd></div>
            <div><dt>Primary turnout</dt><dd>${county.primaryTurnoutPct ? formatPercent(county.primaryTurnoutPct / 100) : "Not loaded"}</dd></div>
            <div><dt>Zodiac recent rate</dt><dd>${county.zodiacRecentlyVotedPct ? formatPercent(county.zodiacRecentlyVotedPct / 100) : "Not loaded"}</dd></div>
          </dl>
        </article>
      `;
    })
    .join("");
}

function renderAll() {
  renderOverview();
  renderTracking();
  renderVoterFile();
  renderPurge();
  renderOutreach();
  renderRegistration();
  renderPrimary2026();
  renderZodiac();
  renderGeography();
}

function bindEvents() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-button").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".dashboard-section").forEach((section) => section.classList.remove("active"));
      button.classList.add("active");
      byId(button.dataset.section).classList.add("active");
    });
  });

  const countyFilter = byId("countyFilter");
  if (countyFilter) {
    countyFilter.addEventListener("change", (event) => {
      state.county = event.target.value;
      renderTracking();
      renderVoterFile();
      renderRegistration();
      renderPrimary2026();
      renderZodiac();
      renderGeography();
    });
  }
}

renderFilters();
renderAll();
bindEvents();
})();
