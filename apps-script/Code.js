const INTAKE_FILE_PROPERTY = "INTAKE_JSON_FILE_ID";
const LEGACY_FILE_PROPERTY = "LEGACY_JSON_FILE_ID";

function doGet() {
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
    .setProperties(properties, true);

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

