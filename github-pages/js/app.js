const sections = [
  ['overview','Home'],['tracking','Tracking'],['voterFile','Voter File'],['purge','Purge'],['outreach','Outreach'],['registration','Registration'],['primary2026','2026 Primary'],['zodiac','Zodiac'],['geography','Geography']
];
const state = { section:'overview', county:'all', data:null };
const $ = id => document.getElementById(id);
const fmt = new Intl.NumberFormat('en-US');
const num = value => Number.isFinite(Number(value)) ? fmt.format(Number(value)) : '0';
const pct = value => `${(Number(value)||0).toFixed(1)}%`;

async function init(){
  renderNav();
  try {
    const res = await fetch('data/public-dashboard.json', { cache:'no-store' });
    if(!res.ok) throw new Error(`Could not load public data (${res.status})`);
    state.data = await res.json();
    validateData(state.data);
    renderFilters();
    renderAll();
  } catch (err) {
    $('privacyNotice').textContent = `Dashboard framework loaded, but public data did not load: ${err.message}`;
    renderShellOnly();
  }
}
function validateData(data){
  const asText = JSON.stringify(data).toLowerCase();
  const blocked = ['first name','last name','voterid','voter id','full address','phone number','email address','birth date'];
  const hit = blocked.find(term => asText.includes(term));
  if(hit) throw new Error(`Public data appears to include private field: ${hit}`);
}
function renderNav(){
  $('nav').innerHTML = sections.map(([id,label]) => `<button class="nav-button ${id==='overview'?'active':''}" data-section="${id}" type="button">${label}</button>`).join('');
  $('nav').addEventListener('click', e => {
    const btn = e.target.closest('[data-section]');
    if(!btn) return;
    state.section = btn.dataset.section;
    document.querySelectorAll('.nav-button').forEach(b => b.classList.toggle('active', b===btn));
    document.querySelectorAll('.dashboard-section').forEach(s => s.classList.toggle('active', s.id===state.section));
  });
}
function renderFilters(){
  const counties = [...new Set([...(state.data.tracking?.countyTotals||[]).map(r=>r.county),...(state.data.geography?.counties||[]).map(r=>r.county)])].sort();
  $('countyFilter').innerHTML = `<option value="all">All counties</option>${counties.map(c=>`<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('')}`;
  $('countyFilter').addEventListener('change', e => { state.county = e.target.value; renderAll(); });
}
function renderShellOnly(){
  $('sections').innerHTML = sections.map(([id,label]) => `<section id="${id}" class="dashboard-section ${id==='overview'?'active':''}"><div class="section-heading"><h2>${label}</h2></div><p class="empty">Waiting for public aggregate data.</p></section>`).join('');
}
function renderAll(){
  const d = state.data;
  $('privacyNotice').textContent = `${d.meta?.title || 'Public dashboard'} · Last built ${d.meta?.generatedAt || 'unknown'} · Aggregate-only public data.`;
  $('sections').innerHTML = sections.map(([id,label]) => `<section id="${id}" class="dashboard-section ${id===state.section?'active':''}"><div class="section-heading"><h2>${label}</h2><span class="status-pill">${statusFor(id)}</span></div>${renderSection(id)}</section>`).join('');
}
function statusFor(id){
  const map = {overview:'Public KPIs',tracking:'GLA contact source',voterFile:'Public-safe summary',purge:'60-day comparison',outreach:'Method totals',registration:'Outcome totals',primary2026:'Workbook-ready',zodiac:'Aggregate only',geography:'County rollups'};
  return map[id] || 'Ready';
}
function renderSection(id){
  const d = state.data;
  if(id==='overview') return metrics(d.overview || {}) + twoColumn(panel('Top Counties', table(['County','Added to VRVH','Contacted'], filteredRows(d.tracking?.countyTotals||[]).slice(0,10).map(r=>[r.county,num(r.addedToCurrentVrvh),num(r.contacted)]))), panel('Contact Sources', table(['Source','People','Added to VRVH'], (d.tracking?.sourceTotals||[]).slice(0,10).map(r=>[r.source,num(r.people),num(r.addedToCurrentVrvh)]))));
  if(id==='tracking') return metrics(d.tracking?.summary || {}) + twoColumn(panel('Updated GLA Contact Source', table(['Source','People','Added to VRVH','Not in GLA File'], (d.tracking?.sourceTotals||[]).map(r=>[r.source,num(r.people),num(r.addedToCurrentVrvh),num(r.notInGlaContactFile)]))), panel('Added to Current VRVH by County', table(['County','Added','Active','Inactive'], filteredRows(d.tracking?.countyTotals||[]).map(r=>[r.county,num(r.addedToCurrentVrvh),num(r.active),num(r.inactive)]))));
  if(id==='voterFile') return metrics(d.voterFile?.summary || {}) + panel('Registration Status', table(['Status','Count'], (d.voterFile?.registrationStatus||[]).map(r=>[r.status,num(r.count)])));
  if(id==='purge') return metrics(d.purge?.summary || {}) + panel('Removed Tracking Status', table(['Status','Count'], (d.purge?.removedTrackingStatus||[]).map(r=>[r.status,num(r.count)])));
  if(id==='outreach') return metrics(d.outreach?.summary || {}) + panel('Contact Status', table(['Status','Count'], (d.outreach?.contactStatus||[]).map(r=>[r.status,num(r.count)])));
  if(id==='registration') return metrics(d.registration?.summary || {}) + panel('Change Status', table(['Status','Count'], (d.registration?.changeStatus||[]).map(r=>[r.status,num(r.count)])));
  if(id==='primary2026') return placeholder('Primary workbook rollups can be added here after the public build script receives the aggregate workbook export.');
  if(id==='zodiac') return placeholder('Zodiac is approved here only as sign-level or county/sign aggregate totals. No birth dates.');
  if(id==='geography') return panel('County Performance', table(['County','People','Added to VRVH','Contacted'], filteredRows(d.geography?.counties||[]).map(r=>[r.county,num(r.people),num(r.addedToCurrentVrvh),num(r.contacted)])));
  return '';
}
function metrics(obj){
  const labels = {totalPeople:'People in source',addedToCurrentVrvh:'Added to current VRVH',notInGlaContactFile:'Not in GLA contact file',contacted:'Contacted',active:'Active',inactive:'Inactive',counties:'Counties',contactRate:'Contact rate'};
  return `<div class="metric-grid">${Object.entries(obj).map(([k,v])=>`<article class="metric-card"><span>${labels[k]||title(k)}</span><strong>${k.toLowerCase().includes('rate')?pct(v):num(v)}</strong></article>`).join('')}</div>`;
}
function panel(titleText, body){ return `<section class="panel"><h3>${titleText}</h3>${body}</section>`; }
function twoColumn(a,b){ return `<div class="two-column">${a}${b}</div>`; }
function table(head, rows){ if(!rows.length) return '<p class="empty">No aggregate rows available.</p>'; return `<table><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(c=>`<td>${escapeHtml(String(c ?? ''))}</td>`).join('')}</tr>`).join('')}</tbody></table>`; }
function placeholder(text){ return `<section class="panel"><p class="empty">${escapeHtml(text)}</p></section>`; }
function filteredRows(rows){ return state.county === 'all' ? rows : rows.filter(r => r.county === state.county); }
function title(key){ return key.replace(/([A-Z])/g,' $1').replace(/^./,c=>c.toUpperCase()); }
function escapeHtml(v){ return v.replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
init();
