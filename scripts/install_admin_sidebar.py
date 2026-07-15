from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODE_PATH = ROOT / "apps-script" / "Code.js"
LAYOUT_PATH = ROOT / "apps-script" / "DashboardLayout.html"

ACCESS_FUNCTION = '''function getEzAppAdminAccessState() {
  const properties = PropertiesService.getScriptProperties();
  const detailFileId = String(
    properties.getProperty(EZ_APP_DETAIL_FILE_PROPERTY) || ""
  ).trim();
  const allowed =