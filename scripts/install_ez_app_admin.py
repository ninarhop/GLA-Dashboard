from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'apps-script' / 'Code.js'
ADMIN = ROOT / 'apps-script' / 'EzAdmin.html'

code = CODE.read_text(encoding='utf-8')

if 'EZ_APP_DETAIL_FILE_PROPERTY' not in code:
    code = code.replace(
        'const LEGACY_FILE_PROPERTY = "LEGACY_JSON_FILE_ID";\n',
        'const LEGACY_FILE_PROPERTY = "LEGACY_JSON_FILE_ID";\n'
        'const EZ_APP_DETAIL_FILE_PROPERTY = "EZ_APP_DETAIL_FILE_ID";\n'
        'const EZ_APP_ADMIN_EMAILS_PROPERTY = "EZ_APP_ADMIN_EMAILS";\n'
    )

old = '''function doGet() {
  return HtmlService.createTemplateFromFile("Index")
    .evaluate()
    .setTitle("GLA Employee Dashboard")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}'''
new = '''function doGet(e) {
  const view = String((e && e.parameter && e.parameter.view) || "").toLowerCase();

  if (view === "ez-admin") {
    assertEzAppAdminAccess_();
    return HtmlService.createTemplateFromFile("EzAdmin")
      .evaluate()
      .setTitle("GLA EZ App Admin")
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }

  return HtmlService.createTemplateFromFile("Index")
    .evaluate()
    .setTitle("GLA Employee Dashboard")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}'''
if old in code:
    code = code.replace(old, new)

marker = '\nfunction configureEzAppAdmin('
if marker not in code:
    code += r'''

function configureEzAppAdmin(detailFileId, adminEmails) {
  const detailId = String(detailFileId || "").trim();
  const emails = normalizeAdminEmails_(adminEmails);

  if (!detailId) throw new Error("The private EZ App detail CSV file ID is required.");
  validateEzAppDetailCsv_(detailId);

  if (!emails.length) {
    const ownerEmail = String(Session.getEffectiveUser().getEmail() || "").trim().toLowerCase();
    if (ownerEmail) emails.push(ownerEmail);
  }
  if (!emails.length) throw new Error("At least one approved administrator email is required.");

  PropertiesService.getScriptProperties().setProperties({
    [EZ_APP_DETAIL_FILE_PROPERTY]: detailId,
    [EZ_APP_ADMIN_EMAILS_PROPERTY]: emails.join(",")
  }, true);

  return getConfiguredEzAppAdmin();
}

function getConfiguredEzAppAdmin() {
  const properties = PropertiesService.getScriptProperties();
  return {
    detail: describeFile_(properties.getProperty(EZ_APP_DETAIL_FILE_PROPERTY)),
    approvedEmails: allowedEzAppAdminEmails_()
  };
}

function getEzAppAdminData(filters) {
  const currentUser = assertEzAppAdminAccess_();
  const fileId = PropertiesService.getScriptProperties().getProperty(EZ_APP_DETAIL_FILE_PROPERTY);
  if (!fileId) throw new Error("The private EZ App detail CSV has not been configured.");

  const file = DriveApp.getFileById(fileId);
  const rows = parseCsvObjects_(file.getBlob().getDataAsString("UTF-8")).map(normalizeEzAppAdminRow_);
  const options = filters || {};
  const search = String(options.search || "").trim().toLowerCase();
  const status = String(options.status || "").trim();
  const county = String(options.county || "").trim().toLowerCase();

  const filtered = rows.filter((row) => {
    if (status && row.matchStatus !== status) return false;
    if (county && String(row.ezAppCounty || "").toLowerCase() !== county && String(row.vrvhCounty || "").toLowerCase() !== county) return false;
    if (!search) return true;
    return Object.values(row).join(" ").toLowerCase().includes(search);
  });

  filtered.sort((a, b) => String(b.submissionDate || "").localeCompare(String(a.submissionDate || "")) || String(a.lastName || "").localeCompare(String(b.lastName || "")));
  const summary = summarizeEzAppAdminRows_(rows);

  return {
    currentUser,
    fileName: file.getName(),
    fileUrl: file.getUrl(),
    lastUpdated: file.getLastUpdated().toISOString(),
    totals: summary.totals,
    byMatchStatus: summary.byMatchStatus,
    statusOptions: summary.byMatchStatus.map((item) => item.status),
    countyOptions: summary.counties,
    totalRows: rows.length,
    filteredCount: filtered.length,
    truncated: filtered.length > 1000,
    rows: filtered.slice(0, 1000)
  };
}

function normalizeEzAppAdminRow_(row) {
  return {
    firstName: row["First Name"] || "",
    middleName: row["Middle Name"] || "",
    lastName: row["Last Name"] || "",
    submissionId: row["EZ App Submission ID"] || "",
    submissionDate: row["EZ App Submission Date"] || "",
    ezAppAddress: row["EZ App Address"] || "",
    ezAppCity: row["EZ App City"] || "",
    ezAppCounty: row["EZ App County"] || "",
    ezAppZip: row["EZ App ZIP"] || "",
    email: row["Email"] || "",
    homePhone: row["Home Phone"] || "",
    workPhone: row["Work Phone"] || "",
    matchStatus: row["Match Status"] || "Unknown",
    currentVrvhStatus: row["Current VRVH Status"] || "",
    vrvhCounty: row["VRVH County"] || "",
    vrvhCity: row["VRVH City"] || "",
    vrvhZip: row["VRVH ZIP"] || "",
    vrvhRegistrationDate: row["VRVH Registration Date"] || "",
    registeredOnOrAfterEzApp: row["Registered On or After EZ App"] || "",
    countyChanged: row["County Changed"] || "",
    reviewNote: row["Address/County Review Note"] || ""
  };
}

function summarizeEzAppAdminRows_(rows) {
  const statusCounts = {};
  const counties = {};
  const totals = {allSubmissions: rows.length, foundInCurrentVrvh: 0, registeredOnOrAfterSubmission: 0, notFoundInCurrentVrvh: 0, multiplePossibleMatches: 0, missingRequiredMatchFields: 0, countyChanged: 0};

  rows.forEach((row) => {
    const status = row.matchStatus || "Unknown";
    statusCounts[status] = (statusCounts[status] || 0) + 1;
    if (status === "Registered on or after EZ App submission" || status.indexOf("Found in current VRVH") === 0) totals.foundInCurrentVrvh += 1;
    if (status === "Registered on or after EZ App submission") totals.registeredOnOrAfterSubmission += 1;
    if (status === "Not found in current VRVH") totals.notFoundInCurrentVrvh += 1;
    if (status.indexOf("Multiple possible") === 0) totals.multiplePossibleMatches += 1;
    if (status === "Missing required match fields") totals.missingRequiredMatchFields += 1;
    if (String(row.countyChanged).toUpperCase() === "YES") totals.countyChanged += 1;
    if (row.ezAppCounty) counties[row.ezAppCounty] = true;
    if (row.vrvhCounty) counties[row.vrvhCounty] = true;
  });

  return {
    totals,
    byMatchStatus: Object.keys(statusCounts).map((status) => ({status, count: statusCounts[status]})).sort((a, b) => b.count - a.count),
    counties: Object.keys(counties).sort()
  };
}

function parseCsvObjects_(content) {
  const matrix = Utilities.parseCsv(String(content || ""));
  if (!matrix.length) return [];
  const headers = matrix.shift().map((header, index) => index === 0 ? String(header || "").replace(/^\uFEFF/, "").trim() : String(header || "").trim());
  return matrix.filter((row) => row.some((value) => String(value || "").trim())).map((row) => {
    const item = {};
    headers.forEach((header, index) => item[header] = String(row[index] || "").trim());
    return item;
  });
}

function validateEzAppDetailCsv_(fileId) {
  const rows = parseCsvObjects_(DriveApp.getFileById(fileId).getBlob().getDataAsString("UTF-8"));
  if (!rows.length) throw new Error("The EZ App detail CSV is empty or could not be parsed.");
  const required = ["First Name", "Last Name", "Match Status", "EZ App County", "Current VRVH Status"];
  const missing = required.filter((field) => !Object.prototype.hasOwnProperty.call(rows[0], field));
  if (missing.length) throw new Error("The selected CSV is missing required fields: " + missing.join(", "));
}

function normalizeAdminEmails_(value) {
  const values = Array.isArray(value) ? value : String(value || "").split(/[;,\n]+/);
  return [...new Set(values.map((email) => String(email || "").trim().toLowerCase()).filter(Boolean))];
}

function allowedEzAppAdminEmails_() {
  return normalizeAdminEmails_(PropertiesService.getScriptProperties().getProperty(EZ_APP_ADMIN_EMAILS_PROPERTY));
}

function assertEzAppAdminAccess_() {
  const allowed = allowedEzAppAdminEmails_();
  if (!allowed.length) throw new Error("EZ App Admin is not configured.");
  const email = String(Session.getActiveUser().getEmail() || "").trim().toLowerCase();
  if (!email) throw new Error("Your Workspace identity could not be verified.");
  if (!allowed.includes(email)) throw new Error("This account is not approved to view private EZ App records.");
  return email;
}
'''

CODE.write_text(code, encoding='utf-8')

ADMIN.write_text(r'''<!doctype html>
<html lang="en">
<head>
  <base target="_top">
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <?!= include("Styles"); ?>
  <style>
    .admin-wrap{padding:24px;max-width:1800px;margin:auto}.admin-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:16px}.admin-tools{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px}.admin-tools input,.admin-tools select{min-height:42px;border:1px solid var(--line);border-radius:8px;padding:0 12px;background:#fff}.admin-tools input{min-width:280px}.admin-table-wrap{overflow:auto;max-height:68vh;border:1px solid var(--line);border-radius:8px;background:#fff}.admin-table{min-width:1800px}.admin-table th{position:sticky;top:0;background:#f7fafc;z-index:1}.private-banner{background:#fff5f5;border-color:#feb2b2;color:#742a2a}.admin-link{color:var(--teal);font-weight:800}
  </style>
</head>
<body>
  <main class="admin-wrap">
    <header class="admin-head">
      <div><p class="eyebrow">Private Admin</p><h1>EZ App Registration Follow-Up</h1></div>
      <a class="admin-link" href="?">Return to aggregate dashboard</a>
    </header>
    <div class="notice private-banner"><strong>Private person-level data.</strong> Only approved Workspace accounts may view this page. Do not share screenshots or export files outside approved GLA storage.</div>
    <div id="summary" class="metric-grid compact"></div>
    <div class="admin-tools">
      <input id="search" type="search" placeholder="Search name, email, phone, city, ZIP…">
      <select id="status"><option value="">All match statuses</option></select>
      <select id="county"><option value="">All counties</option></select>
      <button id="apply" class="nav-button active" type="button">Apply filters</button>
      <button id="clear" class="nav-button active" type="button">Clear</button>
    </div>
    <div id="meta" class="notice"></div>
    <div id="results"></div>
  </main>
<script>
const byId=(id)=>document.getElementById(id);const fmt=new Intl.NumberFormat('en-US');const esc=(v)=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
function card(label,value,detail=''){return `<article class="metric-card"><span>${esc(label)}</span><strong>${fmt.format(Number(value||0))}</strong><small>${esc(detail)}</small></article>`}
function filters(){return {search:byId('search').value,status:byId('status').value,county:byId('county').value}}
function load(){byId('results').innerHTML='<section class="loading-panel"><strong>Loading private EZ App records…</strong></section>';google.script.run.withSuccessHandler(render).withFailureHandler((e)=>byId('results').innerHTML=`<section class="panel empty-state"><h2>Unable to load</h2><p>${esc(e.message||e)}</p></section>`).getEzAppAdminData(filters())}
function render(data){const t=data.totals||{};byId('summary').innerHTML=card('All submissions',t.allSubmissions,'Current EZ App export')+card('Found in VRVH',t.foundInCurrentVrvh,'Any current match')+card('Registered after EZ App',t.registeredOnOrAfterSubmission,'Registration date on/after submission')+card('Not found',t.notFoundInCurrentVrvh,'Needs follow-up')+card('Manual review',t.multiplePossibleMatches,'Multiple possible matches')+card('County changed',t.countyChanged,'EZ App county differs from VRVH');
if(!byId('status').dataset.loaded){byId('status').innerHTML='<option value="">All match statuses</option>'+data.statusOptions.map(v=>`<option>${esc(v)}</option>`).join('');byId('county').innerHTML='<option value="">All counties</option>'+data.countyOptions.map(v=>`<option>${esc(v)}</option>`).join('');byId('status').dataset.loaded='1'}
byId('meta').innerHTML=`Signed in as <strong>${esc(data.currentUser)}</strong>. Showing <strong>${fmt.format(data.filteredCount)}</strong> of ${fmt.format(data.totalRows)} records. Source: <a class="admin-link" href="${esc(data.fileUrl)}" target="_blank">${esc(data.fileName)}</a>. Last updated ${esc(data.lastUpdated)}.${data.truncated?' First 1,000 matching rows shown.':''}`;
const cols=[['Name',r=>[r.firstName,r.middleName,r.lastName].filter(Boolean).join(' ')],['Contact',r=>[r.email,r.homePhone,r.workPhone].filter(Boolean).join(' | ')],['EZ App Date',r=>r.submissionDate],['EZ App Address',r=>[r.ezAppAddress,r.ezAppCity,r.ezAppCounty,r.ezAppZip].filter(Boolean).join(', ')],['Match Status',r=>r.matchStatus],['VRVH Status',r=>r.currentVrvhStatus],['VRVH Registration Date',r=>r.vrvhRegistrationDate],['VRVH Location',r=>[r.vrvhCity,r.vrvhCounty,r.vrvhZip].filter(Boolean).join(', ')],['Registered After EZ App',r=>r.registeredOnOrAfterEzApp],['County Changed',r=>r.countyChanged],['Review Note',r=>r.reviewNote]];
const head=cols.map(c=>`<th>${esc(c[0])}</th>`).join('');const body=data.rows.map(r=>`<tr>${cols.map(c=>`<td>${esc(c[1](r))}</td>`).join('')}</tr>`).join('');byId('results').innerHTML=`<div class="admin-table-wrap"><table class="admin-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`}
byId('apply').onclick=load;byId('clear').onclick=()=>{byId('search').value='';byId('status').value='';byId('county').value='';load()};byId('search').addEventListener('keydown',e=>{if(e.key==='Enter')load()});load();
</script>
</body>
</html>
''', encoding='utf-8')

print('Installed private EZ App admin page files.')
