(() => {
  const root = document.getElementById("app");
  if (!root) return;

  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar" aria-label="Dashboard sections">
        <div class="brand-block">
          <div class="brand-mark" aria-hidden="true">
            <span>GLA</span>
          </div>
          <div>
            <div class="brand-name">Get Loud Arkansas</div>
            <div class="brand-subtitle">Public aggregate dashboard</div>
          </div>
        </div>
        <nav id="nav" class="section-nav" aria-label="Executive dashboard navigation"></nav>
      </aside>

      <main class="content">
        <header class="topbar">
          <div>
            <p class="eyebrow">Executive Dashboard</p>
            <h1>Registration Outreach and Voter Status</h1>
          </div>
          <div class="filter-row" aria-label="Dashboard filters">
            <label>
              County
              <select id="countyFilter">
                <option value="all">All counties</option>
              </select>
            </label>
          </div>
        </header>

        <div id="privacyNotice" class="notice" role="status"></div>
        <section id="sections" class="sections" aria-live="polite"></section>
      </main>
    </div>
  `;
})();
