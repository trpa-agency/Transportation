/* Shared helpers for the funding model pages: formatting, AG Grid and Plotly setup, storage, files.
   No funding logic lives here; all of it is in engine/funding-engine.js. */
(function () {
  'use strict';
  const FE = window.FundingEngine;
  const UI = {};
  UI.FE = FE;
  UI.LEVEL_COLORS = { federal: '#0072CE', state: '#4A6118', local: '#B47E00', private: '#7B6A8A', fare: '#B5A64C', other: '#8A93A3' };
  UI.LEVEL_LABELS = { federal: 'Federal', state: 'State', local: 'Local public', private: 'Private', fare: 'Fares', other: 'Other' };
  UI.COMMIT = {
    formula: { label: 'Formula apportionment', color: '#003B71' }, agreement: { label: 'Written agreement or fee', color: '#0072CE' },
    budget: { label: 'Annual budget contribution', color: '#6FA2DC' }, earned: { label: 'Earned (fares, interest, credits)', color: '#B4CBE8' },
    onetime: { label: 'One-time or time-limited', color: '#E87722' }, none: { label: 'Not committed', color: '#9C3E27' }, proposed: { label: 'Proposed or new', color: '#7B6A8A' }
  };
  UI.COST = '#003B71'; UI.GAP = '#9C3E27'; UI.POS = '#0072CE';
  UI.$ = id => document.getElementById(id);
  UI.esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  UI.money = v => FE.money(v);
  UI.moneyShort = v => { if (v == null || isNaN(v)) return '—'; const a = Math.abs(v); const s = a >= 1e6 ? (a / 1e6).toFixed(a >= 1e7 ? 1 : 2).replace(/\.?0+$/, '') + ' million' : Math.round(a).toLocaleString('en-US'); return (v < 0 ? '−' : '') + '$' + s; };
  UI.pct = (p, d = 1) => { if (p == null || isNaN(p)) return '—'; return (+(p * 100).toFixed(d)) + '%'; };
  UI.signed = (v, fmt = UI.money) => { if (v == null || isNaN(v) || Math.abs(v) < 0.5) return '—'; return (v > 0 ? '+' : '') + fmt(v); };
  UI.deltaClass = (v, goodIfUp = true) => Math.abs(v) < 0.5 ? 'flat' : ((v > 0) === goodIfUp ? 'up' : 'down');
  UI.sum = a => a.reduce((x, y) => x + (+y || 0), 0);
  UI.parseNum = v => { if (v == null || v === '') return null; const n = +String(v).replace(/[$,%\s]/g, ''); return isNaN(n) ? null : n; };
  UI.levelBadge = lv => `<span class="swatch" style="background:${UI.LEVEL_COLORS[lv] || '#ccc'}"></span>${UI.esc(UI.LEVEL_LABELS[lv] || lv)}`;
  UI.sevBadge = s => s === 'error' ? '<span class="badge danger">Error</span>' : s === 'warning' ? '<span class="badge warning">Warning</span>' : '<span class="badge info">Info</span>';
  UI.cite = (m, type, id, field) => FE.citations(m, type, id).filter(c => !field || c.field === field).map(c => (c.document_id ? (m.documents.find(d => d.document_id === c.document_id) || {}).file_name + ' › ' : '') + c.locator).join('; ');

  /* AG Grid */
  const FONT = 'Open Sans, system-ui, sans-serif';
  UI.FONT = FONT;
  UI.gridTheme = (typeof agGrid !== 'undefined') ? agGrid.themeQuartz.withParams({ accentColor: '#0072CE', fontFamily: FONT, fontSize: 12, headerFontSize: 11, headerTextColor: '#6B7688',
    headerBackgroundColor: '#F3F6FA', rowHeight: 30, headerHeight: 34, spacing: 5, borderColor: '#E2E6EC', foregroundColor: '#003B71' }) : null;
  const GRIDS = {}, GRID_EL = {};
  UI.grids = GRIDS;
  // Create a grid once; later calls update columns and rows in place so scroll position and selection survive edits.
  UI.grid = (key, el, opts) => {
    const g = GRIDS[key];
    if (g && GRID_EL[key] === el && !(g.isDestroyed && g.isDestroyed())) {
      if (opts.columnDefs) g.setGridOption('columnDefs', opts.columnDefs);
      g.setGridOption('pinnedBottomRowData', opts.pinnedBottomRowData || []);
      g.setGridOption('rowData', opts.rowData);
      g.refreshCells({ force: true });
      return g;
    }
    if (g) { try { g.destroy(); } catch (e) { /* already gone */ } }
    GRID_EL[key] = el;
    return (GRIDS[key] = agGrid.createGrid(el, Object.assign({ theme: UI.gridTheme, defaultColDef: { sortable: true, resizable: true, filter: true, minWidth: 70 },
      tooltipShowDelay: 300, stopEditingWhenCellsLoseFocus: true, singleClickEdit: true, animateRows: false }, opts)));
  };
  UI.destroyGrids = () => { for (const k of Object.keys(GRIDS)) { try { GRIDS[k].destroy(); } catch (e) { /* ignore */ } delete GRIDS[k]; } };
  UI.numCol = o => Object.assign({ type: 'rightAligned', cellClass: 'num', headerClass: 'num', cellDataType: 'number', filter: 'agNumberColumnFilter',
    valueFormatter: p => p.value == null ? '—' : UI.money(p.value) }, o);
  UI.pctCol = o => UI.numCol(Object.assign({ valueFormatter: p => p.value == null ? '—' : UI.pct(p.value) }, o));
  UI.csv = (key, name) => { const g = GRIDS[key]; if (g) g.exportDataAsCsv({ fileName: name + '.csv' }); };

  /* Plotly */
  UI.PCFG = { responsive: true, displayModeBar: false };
  UI.layout = extra => {
    const ax = { gridcolor: '#E8ECF1', linecolor: '#DDDDDD', zerolinecolor: '#B8C2CF', tickfont: { size: 11 }, automargin: true };
    const base = { font: { family: FONT, color: '#003B71', size: 12 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', margin: { t: 40, r: 16, b: 40, l: 60 },
      hoverlabel: { font: { family: FONT, size: 12 }, bgcolor: '#fff', bordercolor: '#C9D2DE' }, legend: { orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom', traceorder: 'normal', font: { size: 11 } }, bargap: 0.28 };
    const out = Object.assign(base, extra || {});
    out.xaxis = Object.assign({}, ax, (extra || {}).xaxis); out.yaxis = Object.assign({}, ax, (extra || {}).yaxis);
    return out;
  };
  UI.plot = (el, data, layout) => { if (typeof Plotly !== 'undefined') Plotly.react(el, data, UI.layout(layout), UI.PCFG); };

  /* Storage (per-viewer convenience only; every page works without it) */
  UI.store = {
    get(key) { try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : null; } catch (e) { return null; } },
    set(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); return true; } catch (e) { return false; } },
    del(key) { try { localStorage.removeItem(key); } catch (e) { /* ignore */ } }
  };
  UI.download = (name, text, type = 'application/json') => {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name;
    document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  };
  UI.pickFile = cb => { const i = document.createElement('input'); i.type = 'file'; i.accept = '.json,application/json'; i.onchange = () => { const f = i.files[0]; if (!f) return; const r = new FileReader(); r.onload = () => { try { cb(JSON.parse(r.result)); } catch (e) { alert('Could not read that file: ' + e.message); } }; r.readAsText(f); }; i.click(); };

  /* Model loading: a working copy (edited) and the untouched source data (baseline) */
  UI.loadModels = storeKey => {
    const baseline = FE.load(window.FUNDING_SEED);
    let model = null;
    const saved = storeKey ? UI.store.get(storeKey) : null;
    if (saved && saved.tables) { try { model = FE.load(saved); } catch (e) { model = null; } }
    return { baseline, model: model || FE.load(window.FUNDING_SEED), restored: !!model };
  };
  UI.wireSeg = (el, cb) => el.querySelectorAll('button').forEach(b => b.addEventListener('click', () => { el.querySelectorAll('button').forEach(x => x.setAttribute('aria-checked', String(x === b))); cb(b.dataset.v); }));
  UI.yearOptions = (m, sel) => m.years.map((y, i) => `<option value="${i}" ${i === sel ? 'selected' : ''}>${y}</option>`).join('');
  UI.libsOk = () => typeof agGrid !== 'undefined' && typeof Plotly !== 'undefined' && !!FE && !!window.FUNDING_SEED;
  window.UI = UI;
})();
