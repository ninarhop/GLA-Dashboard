const INTAKE_FILE_PROPERTY = "INTAKE_JSON_FILE_ID";
const LEGACY_FILE_PROPERTY = "LEGACY_JSON_FILE_ID";
const EZ_APP_DETAIL_FILE_PROPERTY = "EZ_APP_DETAIL_FILE_ID";
const EZ_APP_ADMIN_EMAILS_PROPERTY = "EZ_APP_ADMIN_EMAILS";

function doGet(e) {
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
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function getDashboardData(url, required) {
  const isLegacy = String(url || "").includes("public-dashboard.json");
  const propertyName = isLegacy
    ? LEGACY_FILE_PROPERTY
    : INTAKE_FILE_PROPERTY;

  const fileId = PropertiesService.getScriptProperties()
    .getProperty(propertyName);

  if (!fileId) {
    if (!required || isLegacy) {
      return null;
    }

    throw new Error(
      "The current aggregate dashboard JSON file has not been configured."
    );
  }

  const file = DriveApp.getFileById(fileId);
  const content = file.getBlob().getDataAsString("UTF-8");
  const data = JSON.parse(content);

  validateAggregateOnly_(data);
  return data;
}

function configureDashboardFiles(intakeFileId, legacyFileId) {
  const intakeId = String(intakeFileId || "").trim();
  const legacyId = String(legacyFileId || "").trim();

  if (!intakeId) {
    throw new Error("The current intake aggregate JSON file ID is required.");
  }

  validateDriveJson_(intakeId);

  const properties = {
    [INTAKE_FILE_PROPERTY]: intakeId
  };

  if (legacyId) {
    validateDriveJson_(legacyId);
    properties[LEGACY_FILE_PROPERTY] = legacyId;
  }

  PropertiesService.getScriptProperties()
    .setProperties(properties);

  return getConfiguredDashboardFiles();
}

function getConfiguredDashboardFiles() {
  const properties = PropertiesService.getScriptProperties();
  const intakeId = properties.getProperty(INTAKE_FILE_PROPERTY);
  const legacyId = properties.getProperty(LEGACY_FILE_PROPERTY);

  return {
    intake: describeFile_(intakeId),
    legacy: describeFile_(legacyId)
  };
}

function describeFile_(fileId) {
  if (!fileId) {
    return { configured: false };
  }

  const file = DriveApp.getFileById(fileId);

  return {
    configured: true,
    fileName: file.getName(),
    fileId: fileId,
    lastUpdated: file.getLastUpdated().toISOString()
  };
}

function validateDriveJson_(fileId) {
  const file = DriveApp.getFileById(fileId);
  const content = file.getBlob().getDataAsString("UTF-8");
  const data = JSON.parse(content);

  validateAggregateOnly_(data);
}

function validateAggregateOnly_(data) {
  const text = JSON.stringify(data).toLowerCase();
  const blocked = [
    "first name",
    "last name",
    "middle name",
    "voterid",
    "voter id",
    "date of birth",
    "birth date",
    "full address",
    "phone number",
    "email address",
    "signature"
  ];

  const found = blocked.find((field) => text.includes(field));

  if (found) {
    throw new Error(
      "Privacy validation failed. Person-level field detected: " + found
    );
  }
}



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
  });

  return getConfiguredEzAppAdmin();
}

function getEzAppAdminAccessState() {
  const properties = PropertiesService.getScriptProperties();
  const detailFileId = String(
    properties.getProperty(EZ_APP_DETAIL_FILE_PROPERTY) || ""
  ).trim();
  const allowed = allowedEzAppAdminEmails_();
  const email = String(Session.getActiveUser().getEmail() || "")
    .trim()
    .toLowerCase();

  return {
    configured: Boolean(detailFileId && allowed.length),
    approved: Boolean(email && allowed.includes(email)),
    email: email
  };
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
