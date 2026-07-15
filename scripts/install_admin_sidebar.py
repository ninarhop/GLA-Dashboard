from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODE_PATH = ROOT / "apps-script" / "Code.js"
LAYOUT_PATH = ROOT / "apps-script" / "DashboardLayout.html"

ACCESS_FUNCTION = '''
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
'''.strip()

ADMIN_SLOT = '''
        <div id="adminNavSlot" class="admin-nav-slot" hidden>
          <a id="ezAdminNavLink" class="nav-button admin-nav-link" href="?view=ez-admin">
            EZ App Admin
          </a>
        </div>
'''.strip()

ACCESS_SCRIPT = '''
  google.script.run
    .withSuccessHandler((state) => {
      const slot = document.getElementById("adminNavSlot");
      if (!slot) return;
      if (state && state.configured && state.approved) {
        slot.hidden = false;
      }
    })
    .withFailureHandler(() => {})
    .getEzAppAdminAccessState();
'''.strip()

STYLE_BLOCK = '''
      .admin-nav-slot {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid rgba(255, 255, 255, 0.18);
      }

      .admin-nav-link {
        display: block;
        text-decoration: none;
      }
'''.strip()


def install_code() -> None:
    text = CODE_PATH.read_text(encoding="utf-8")
    if "function getEzAppAdminAccessState()" not in text:
        marker = "function getConfiguredEzAppAdmin() {"
        if marker not in text:
            raise SystemExit("Could not find the EZ App Admin configuration section in Code.js.")
        text = text.replace(marker, ACCESS_FUNCTION + "\n\n" + marker, 1)
        CODE_PATH.write_text(text, encoding="utf-8")


def install_layout() -> None:
    text = LAYOUT_PATH.read_text(encoding="utf-8")

    if 'id="adminNavSlot"' not in text:
        marker = '<nav id="nav" class="section-nav" aria-label="Executive dashboard navigation"></nav>'
        if marker not in text:
            raise SystemExit("Could not find the dashboard sidebar navigation in DashboardLayout.html.")
        text = text.replace(marker, marker + "\n" + ADMIN_SLOT, 1)

    if ".admin-nav-slot" not in text:
        marker = "<script>"
        text = text.replace(marker, "<style>\n" + STYLE_BLOCK + "\n</style>\n" + marker, 1)

    if ".getEzAppAdminAccessState();" not in text:
        marker = "})();"
        if marker not in text:
            raise SystemExit("Could not find the end of DashboardLayout.html.")
        text = text.replace(marker, ACCESS_SCRIPT + "\n" + marker, 1)

    LAYOUT_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    install_code()
    install_layout()
    print("EZ App Admin sidebar button installed.")
    print("The button appears only for configured, approved administrators.")


if __name__ == "__main__":
    main()
