/* ========================================
   Dashboard CED Uncisal — Application Logic
   ======================================== */

const CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vSIepYnDvWMen_cKY3x24fzkMNaIthf54BBqtxBflw74z_NQFvvKIJLmaY49SytS_aQ0kkuM7SgRAJe/pub?gid=368857864&single=true&output=csv';
const APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxVFHvGopgNcP_GNPZq62QZncRkm4yd8gQF--PFfvPqFy9-Kxz5JLdzUk2ma_x2Bv-m/exec';
const REFRESH_INTERVAL = 60000; // 60 seconds instead of 5s

let RAW = [];
const FIELDS = [
  { id: "fCurso", key: "curso", label: "Curso" },
  { id: "fPolo", key: "polo", label: "Polo" },
  { id: "fSitCurso", key: "situacao_curso", label: "Situação no Curso" },
  { id: "fSitPeriodo", key: "situacao_periodo", label: "Situação no Período" },
  { id: "fPerCurso", key: "periodo_curso", label: "Período do Curso" },
  { id: "fPerLetivo", key: "periodo_letivo", label: "Período Letivo" },
  { id: "fCampus", key: "campus", label: "Campus" },
  { id: "fCodigo", key: "codigo_curso", label: "Código do Curso" }
];

let filters = Object.fromEntries(FIELDS.map(f => [f.key, []]));
filters.search = '';
let data = [];
let page = 1;
let perPage = 10;
let charts = {};
let refreshing = false;
let lastCsvSignature = '';
let lastRefreshAt = null;
let lastRefreshStatus = 'inicial';
let sortKey = null;
let sortDir = 'asc';
let refreshTimer = null;

const $ = id => document.getElementById(id);

/* ========================================
   Utility Functions
   ======================================== */

function cap(t) {
  return String(t || '').toLowerCase().split(/\s+/)
    .map((w, i) => ['de', 'da', 'do', 'das', 'dos', 'e', 'em', 'no', 'na', 'nos', 'nas', 'para', 'por', 'com', 'a', 'o'].includes(w) && i > 0
      ? w : w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function fixAcronyms(t) {
  return String(t || '').replace(/ Ppl/g, ' PPL').replace(/ ppl/g, ' PPL');
}

function course(v) {
  const f = {
    'LETRAS LÍNGUA BRASILEIRA DE SINAIS FORMAÇÃO DE PROFESSORES': 'Letras Libras - Formação de Professores',
    'LICENCIATURA EM MATEMÁTICA': 'Licenciatura em Matemática',
    'GESTÃO EMPREENDEDORA E INOVAÇÃO DO TURISMO': 'Gestão Empreendedora e Inovação do Turismo',
    'MATEMÁTICA FORMAÇÃO DE PROFESSORES': 'Matemática - Formação de Professores'
  };
  return f[String(v || '').toUpperCase()] || cap(v || 'Não informado');
}

function htmlSafe(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function statusTone(value) {
  const normalized = String(value || 'Não informado').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  if (normalized.includes('matriculado')) return { cls: 'status-matriculado', style: '' };
  if (normalized.includes('em aberto')) return { cls: 'status-em-aberto', style: '' };
  if (normalized.includes('trancado')) return { cls: 'status-trancado', style: '' };
  if (normalized.includes('cancel')) return { cls: 'status-cancelado', style: '' };
  if (normalized.includes('evasao')) return { cls: 'status-evasao', style: '' };
  if (normalized.includes('nao informado')) return { cls: 'status-nao-informado', style: '' };
  let hash = 0;
  for (let i = 0; i < normalized.length; i++) hash = (hash * 31 + normalized.charCodeAt(i)) % 360;
  return {
    cls: 'status-dinamico',
    style: '--status-bg:hsl(' + hash + ' 74% 94%);--status-fg:hsl(' + hash + ' 62% 29%);--status-line:hsl(' + hash + ' 62% 82%);'
  };
}

/* ========================================
   CSV Parsing & Data Normalization
   ======================================== */

function unique(h) {
  let s = {};
  return h.map(x => {
    x = String(x || '').replace(/^\uFEFF/, '').trim();
    s[x] = (s[x] || 0) + 1;
    if (x === 'Período' && s[x] === 1) return 'Período Letivo';
    if (x === 'Período' && s[x] === 2) return 'Período do Curso';
    return s[x] > 1 ? x + ' ' + s[x] : x;
  });
}

function parseCsv(text) {
  let rows = [], row = [], val = '', q = false;
  let del = (text.slice(0, 1000).match(/;/g) || []).length > (text.slice(0, 1000).match(/,/g) || []).length ? ';' : ',';
  for (let i = 0; i < text.length; i++) {
    let ch = text[i], n = text[i + 1];
    if (ch === '"') {
      if (q && n === '"') { val += '"'; i++; } else q = !q;
    } else if (ch === del && !q) {
      row.push(val); val = '';
    } else if ((ch === '\n' || ch === '\r') && !q) {
      if (ch === '\r' && n === '\n') i++;
      row.push(val); rows.push(row); row = []; val = '';
    } else val += ch;
  }
  if (val || row.length) { row.push(val); rows.push(row); }
  let h = unique(rows.shift() || []);
  return rows
    .filter(r => r.some(c => String(c || '').trim()))
    .map(r => Object.fromEntries(h.map((x, i) => [x, String(r[i] || '').trim()])));
}

function norm(r, i) {
  let polo = r['Polo'] || 'Não informado';
  let mun = polo.toLowerCase().startsWith('polo ') ? polo.replace(/^polo\s+/i, '') : polo;
  return {
    id: i + 1,
    matricula: r['Matrícula'] || '',
    nome: cap(r['Nome'] || ''),
    campus: (r['Campus'] || 'Não informado').replaceAll('_', ' '),
    codigo_curso: r['Código Curso'] || 'Não informado',
    curso: course(r['Descrição do Curso']),
    email_academico: r['Email Acadêmico'] || '',
    polo: fixAcronyms(cap(polo)),
    municipio_polo: fixAcronyms(cap(mun)),
    situacao_curso: cap(r['Situação no Curso'] || 'Não informado'),
    situacao_periodo: cap(r['Situação no Período'] || 'Não informado'),
    periodo_letivo: r['Período Letivo'] || (String(r['Período'] || '').includes('.') ? r['Período'] : 'Não informado'),
    periodo_curso: r['Período do Curso'] || (String(r['Período'] || '').includes('.') ? 'Não informado' : (r['Período'] || 'Não informado'))
  };
}

function mergeMissingPeriods(records) {
  let prior = new Map(RAW.map(r => [r.matricula, r]));
  let knownLetivo = [...new Set(RAW.map(r => r.periodo_letivo).filter(v => v && v !== 'Não informado'))];
  let defaultLetivo = knownLetivo.length === 1 ? knownLetivo[0] : '';
  return records.map(r => {
    let old = prior.get(r.matricula);
    if (old && r.periodo_letivo === 'Não informado' && old.periodo_letivo && old.periodo_letivo !== 'Não informado')
      r.periodo_letivo = old.periodo_letivo;
    if (r.periodo_letivo === 'Não informado' && defaultLetivo)
      r.periodo_letivo = defaultLetivo;
    if (old && r.periodo_curso === 'Não informado' && old.periodo_curso && old.periodo_curso !== 'Não informado')
      r.periodo_curso = old.periodo_curso;
    return r;
  });
}

/* ========================================
   Data Loading (Online + Fallback)
   ======================================== */

async function loadCsvRows() {
  let url = CSV_URL + '&_=' + Date.now();
  let res = await fetch(url, { cache: 'reload' });
  if (!res.ok) throw new Error('CSV HTTP ' + res.status);
  let txt = await res.text();
  return {
    source: 'published-csv',
    signature: txt.length + ':' + txt.slice(0, 180) + ':' + txt.slice(-180),
    records: mergeMissingPeriods(parseCsv(txt).map(norm).filter(r => r.nome || r.matricula))
  };
}

async function loadOnlineRows() {
  if (APPS_SCRIPT_URL && APPS_SCRIPT_URL.trim()) {
    try {
      let url = APPS_SCRIPT_URL + (APPS_SCRIPT_URL.includes('?') ? '&' : '?') + '_=' + Date.now();
      let res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error('Apps Script HTTP ' + res.status);
      let text = await res.text();
      let payload = JSON.parse(text);
      let rows = Array.isArray(payload) ? payload : (payload.rows || []);
      let json = JSON.stringify(rows);
      let records = mergeMissingPeriods(rows.map(norm).filter(r => r.nome || r.matricula));
      if (!records.length) throw new Error('Apps Script sem registros válidos');
      return {
        source: 'apps-script',
        signature: json.length + ':' + json.slice(0, 180) + ':' + json.slice(-180),
        records
      };
    } catch (appsError) {
      console.warn('Endpoint Apps Script indisponível. Usando CSV publicado como fallback.', appsError);
    }
  }
  return loadCsvRows();
}

async function loadInitialData() {
  try {
    const res = await fetch('data.json');
    if (res.ok) {
      RAW = await res.json();
      data = [...RAW];
      return true;
    }
  } catch (e) {
    console.warn('data.json não encontrado, tentando fonte online...', e);
  }
  return false;
}

/* ========================================
   Smart Refresh (with pause when hidden)
   ======================================== */

async function refresh() {
  if (refreshing) return;
  refreshing = true;
  lastRefreshStatus = 'consultando';
  updateFooterStatus();

  try {
    let loaded = await loadOnlineRows();
    lastRefreshAt = new Date();

    if (loaded.signature === lastCsvSignature) {
      lastRefreshStatus = 'sem alterações';
      updateFooterStatus();
      return;
    }

    if (!loaded.records.length) throw new Error('Planilha sem registros válidos');

    RAW = loaded.records;
    lastCsvSignature = loaded.signature;
    lastRefreshStatus = 'atualizado';
    populate();
    apply();
    updateFooterStatus();
  } catch (e) {
    lastRefreshStatus = 'erro';
    updateFooterStatus();
    console.warn('Falha ao atualizar dados da planilha. Mantendo dados atuais.', e);
  } finally {
    refreshing = false;
  }
}

function startRefreshCycle() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    if (!document.hidden) refresh();
  }, REFRESH_INTERVAL);
}

function updateFooterStatus() {
  const el = $('lastUpdate');
  if (!el) return;
  if (lastRefreshAt) {
    el.textContent = 'Última atualização: ' + lastRefreshAt.toLocaleTimeString('pt-BR');
  } else {
    el.textContent = 'Carregando dados...';
  }
}

/* ========================================
   Filter Logic
   ======================================== */

function vals(v) {
  return Array.isArray(v) ? v.filter(x => x && x !== 'ALL') : [];
}

function count(key, arr = data) {
  return arr.reduce((a, r) => {
    let k = r[key] || 'Não informado';
    a[k] = (a[k] || 0) + 1;
    return a;
  }, {});
}

function sorted(o) {
  return Object.entries(o).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'pt-BR'));
}

function populate() {
  FIELDS.forEach(f => {
    let sel = $(f.id), keep = new Set(vals(filters[f.key]));
    sel.innerHTML = '<option value="ALL">Selecionar todas as opções</option>';
    [...new Set(RAW.map(r => r[f.key]).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, 'pt-BR'))
      .forEach(v => {
        let o = document.createElement('option');
        o.value = v;
        o.textContent = v;
        o.selected = keep.has(v);
        sel.appendChild(o);
      });
    sel.options[0].selected = keep.size === 0;
    updateDrop(f.id);
  });
}

/* ========================================
   Custom Multi-select Dropdowns
   ======================================== */

function createDrop(f) {
  let sel = $(f.id);
  let wrap = document.createElement('div');
  wrap.className = 'multi';
  wrap.id = f.id + 'Drop';
  wrap.innerHTML = '<button type="button" class="multi-btn"><span></span><i class="fa-solid fa-chevron-down"></i></button><div class="menu"></div>';
  sel.after(wrap);
  wrap.querySelector('button').onclick = e => {
    e.stopPropagation();
    document.querySelectorAll('.multi.open').forEach(m => {
      if (m !== wrap) m.classList.remove('open');
    });
    wrap.classList.toggle('open');
  };
  updateDrop(f.id);
}

function updateDrop(id) {
  let f = FIELDS.find(x => x.id === id), sel = $(id), wrap = $(id + 'Drop');
  if (!wrap) return;
  let chosen = new Set(vals(filters[f.key]));
  let opts = [...sel.options].filter(o => chosen.has(o.value));
  wrap.querySelector('button span').textContent =
    opts.length === 0 ? 'Selecionar todas as opções' :
    opts.length === 1 ? opts[0].textContent :
    opts.length + ' opções selecionadas';
  let menu = wrap.querySelector('.menu');
  menu.innerHTML = '';
  [...sel.options].forEach(o => {
    let active = o.value === 'ALL' ? chosen.size === 0 : chosen.has(o.value);
    let b = document.createElement('button');
    b.type = 'button';
    b.className = 'option' + (active ? ' selected' : '') + (o.value === 'ALL' ? ' all' : '');
    b.innerHTML = '<span class="check"><i class="fa-solid fa-check"></i></span><span>' + o.textContent + '</span>';
    b.onclick = e => {
      e.stopPropagation();
      toggle(f, o.value);
    };
    menu.appendChild(b);
  });
}

function toggle(f, v) {
  if (v === 'ALL') {
    filters[f.key] = [];
  } else {
    let s = new Set(vals(filters[f.key]));
    s.has(v) ? s.delete(v) : s.add(v);
    filters[f.key] = [...s];
  }
  updateDrop(f.id);
  apply();
}

/* ========================================
   Apply Filters & Re-render
   ======================================== */

function apply() {
  data = RAW.filter(r =>
    FIELDS.every(f => !vals(filters[f.key]).length || vals(filters[f.key]).includes(r[f.key])) &&
    (!filters.search || [r.nome, r.matricula, r.curso, r.polo, r.email_academico]
      .some(v => String(v).toLowerCase().includes(filters.search.toLowerCase())))
  );
  // Apply sort if active
  if (sortKey) {
    data.sort((a, b) => {
      let va = String(a[sortKey] || ''), vb = String(b[sortKey] || '');
      let cmp = va.localeCompare(vb, 'pt-BR', { numeric: true });
      return sortDir === 'desc' ? -cmp : cmp;
    });
  }
  page = 1;
  render();
}

/* ========================================
   Count-Up Animation for Metrics
   ======================================== */

function animateValue(el, start, end, suffix = '') {
  if (start === end) {
    el.textContent = end.toLocaleString('pt-BR') + suffix;
    return;
  }
  const duration = 600;
  const startTime = performance.now();
  function tick(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = Math.round(start + (end - start) * eased);
    el.textContent = current.toLocaleString('pt-BR') + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ========================================
   Render Functions
   ======================================== */

function metric() {
  let total = data.length;
  let mat = data.filter(r => r.situacao_curso === 'Matriculado').length;
  let ab = data.filter(r => r.situacao_curso === 'Em Aberto' || r.situacao_periodo === 'Em Aberto').length;
  let cursos = new Set(data.map(r => r.curso)).size;
  let polos = new Set(data.map(r => r.polo)).size;
  let pct = total ? Math.round(mat / total * 100) : 0;

  // Animate count-up
  animateValue($('mTotal'), parseInt($('mTotal').textContent.replace(/\D/g, '')) || 0, total);
  animateValue($('mMat'), parseInt($('mMat').textContent.replace(/\D/g, '')) || 0, mat);
  animateValue($('mAberto'), parseInt($('mAberto').textContent.replace(/\D/g, '')) || 0, ab);
  animateValue($('mCursos'), parseInt($('mCursos').textContent.replace(/\D/g, '')) || 0, cursos);
  animateValue($('mPolos'), parseInt($('mPolos').textContent.replace(/\D/g, '')) || 0, polos);
  animateValue($('mPct'), parseInt($('mPct').textContent.replace(/\D/g, '')) || 0, pct, '%');
}

function chart(id, type, entries, opt = {}) {
  if (typeof Chart === 'undefined') return;
  let labels = entries.map(x => x[0]);
  let d = entries.map(x => x[1]);
  let colors = [
    { bg: 'rgba(45, 54, 216, 0.85)', border: '#2d36d8' },
    { bg: 'rgba(255, 138, 18, 0.85)', border: '#ff8a12' },
    { bg: 'rgba(0, 159, 90, 0.85)', border: '#009f5a' },
    { bg: 'rgba(237, 50, 55, 0.85)', border: '#ed3237' },
    { bg: 'rgba(255, 176, 45, 0.85)', border: '#ffb02d' },
    { bg: 'rgba(59, 24, 201, 0.85)', border: '#3b18c9' },
    { bg: 'rgba(10, 166, 166, 0.85)', border: '#0aa6a6' },
    { bg: 'rgba(104, 116, 125, 0.85)', border: '#68747d' }
  ];

  if (charts[id]) {
    charts[id].data.labels = labels;
    charts[id].data.datasets[0].data = d;
    charts[id].update();
    return;
  }

  charts[id] = new Chart($(id), {
    type,
    data: {
      labels,
      datasets: [{
        label: 'Discentes',
        data: d,
        backgroundColor: labels.map((_, i) => colors[i % colors.length].bg),
        borderColor: labels.map((_, i) => colors[i % colors.length].border),
        borderWidth: 1.5,
        borderRadius: type === 'bar' ? 8 : 0,
        hoverOffset: 12
      }]
    },
    options: Object.assign({
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 800,
        easing: 'easeOutQuart'
      },
      plugins: {
        legend: {
          display: type !== 'bar',
          position: 'right',
          labels: { usePointStyle: true }
        },
        tooltip: {
          padding: 12,
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          titleFont: { weight: 'bold' },
          cornerRadius: 8
        }
      },
      scales: type === 'bar' ? {
        x: { beginAtZero: true, ticks: { precision: 0 } },
        y: { grid: { display: false } }
      } : {}
    }, opt)
  });
}

function chartsRender() {
  chart('cCurso', 'bar', sorted(count('curso')), { indexAxis: 'y', plugins: { legend: { display: false } } });
  chart('cPolo', 'bar', sorted(count('polo')).slice(0, 12), { indexAxis: 'y', plugins: { legend: { display: false } } });
  chart('cSit', 'doughnut', sorted(count('situacao_curso')));
  chart('cPerCurso', 'pie', sorted(count('periodo_curso')));
  chart('cPerLetivo', 'doughnut', sorted(count('periodo_letivo')));
}

function lists() {
  let total = data.length || 1;
  $('statusList').innerHTML = sorted(count('situacao_curso')).map(([l, c]) =>
    '<div><div class="bar-top"><span>' + l + '</span><span>' + c + '</span></div>' +
    '<div class="bar-track"><div class="bar-fill" style="width:' + Math.round(c / total * 100) + '%"></div></div></div>'
  ).join('');

  $('poloGrid').innerHTML = sorted(count('polo')).slice(0, 12).map(([l, c]) =>
    '<div class="polo-card"><strong>' + l + '</strong><span>' + c + '</span></div>'
  ).join('');
}

function table() {
  let size = perPage === 'ALL' ? (data.length || 1) : perPage;
  let totalPages = Math.max(1, Math.ceil(data.length / size));
  page = Math.min(page, totalPages);
  let start = perPage === 'ALL' ? 0 : (page - 1) * size;
  let rows = data.slice(start, start + size);

  $('tbody').innerHTML = rows.map((r, i) => {
    let toneCurso = statusTone(r.situacao_curso);
    let tonePeriodo = statusTone(r.situacao_periodo);
    return '<tr>' +
      '<td>' + (start + i + 1) + '</td>' +
      '<td><strong>' + htmlSafe(r.matricula) + '</strong></td>' +
      '<td>' + htmlSafe(r.nome) + '</td>' +
      '<td>' + htmlSafe(r.curso) + '</td>' +
      '<td>' + htmlSafe(r.polo) + '</td>' +
      '<td><span class="pill ' + toneCurso.cls + '" style="' + toneCurso.style + '">' + htmlSafe(r.situacao_curso) + '</span></td>' +
      '<td><span class="pill ' + tonePeriodo.cls + '" style="' + tonePeriodo.style + '">' + htmlSafe(r.situacao_periodo) + '</span></td>' +
      '<td>' + htmlSafe(r.periodo_letivo) + '</td>' +
      '<td>' + htmlSafe(r.periodo_curso) + '</td>' +
      '<td>' + htmlSafe(r.email_academico) + '</td>' +
      '</tr>';
  }).join('');

  $('pageInfo').textContent = 'Mostrando ' + (data.length ? start + 1 : 0) + '-' +
    Math.min(start + size, data.length) + ' de ' + data.length.toLocaleString('pt-BR') + ' registros';
  $('pageNum').textContent = 'Página ' + page + ' de ' + totalPages;
  $('prev').disabled = page <= 1;
  $('next').disabled = page >= totalPages;
}

function render() {
  FIELDS.forEach(f => $(f.id).parentElement.classList.toggle('active', vals(filters[f.key]).length > 0));
  $('search').classList.toggle('active', filters.search.length > 0);
  metric();
  chartsRender();
  lists();
  table();
  updateFooterStatus();
}

/* ========================================
   Table Sorting
   ======================================== */

const SORT_KEYS = ['matricula', 'nome', 'curso', 'polo', 'situacao_curso', 'situacao_periodo', 'periodo_letivo', 'periodo_curso', 'email_academico'];

function setupSorting() {
  const headers = document.querySelectorAll('thead th');
  headers.forEach((th, i) => {
    if (i === 0) return; // skip # column
    const key = SORT_KEYS[i - 1];
    if (!key) return;
    th.style.cursor = 'pointer';
    th.innerHTML += ' <i class="fa-solid fa-sort sort-icon"></i>';
    th.addEventListener('click', () => {
      if (sortKey === key) {
        sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        sortKey = key;
        sortDir = 'asc';
      }
      // Update header styles
      headers.forEach(h => h.classList.remove('sorted'));
      th.classList.add('sorted');
      const icon = th.querySelector('.sort-icon');
      if (icon) icon.className = 'fa-solid sort-icon ' + (sortDir === 'asc' ? 'fa-sort-up' : 'fa-sort-down');
      apply();
    });
  });
}

/* ========================================
   IntersectionObserver for Chart Reveal
   ======================================== */

function setupChartReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.chart-body').forEach(el => {
    el.classList.add('reveal');
    observer.observe(el);
  });
}

/* ========================================
   Staggered Fade-In on Load
   ======================================== */

function setupFadeIn() {
  const targets = document.querySelectorAll('.header, .filters, .accent, .metric, .grid2, .grid3, .table-card, footer');
  targets.forEach(el => el.classList.add('fade-in'));
}

/* ========================================
   Export Functions (Lazy Load)
   ======================================== */

const COLS = [
  ['matricula', 'Matrícula'],
  ['nome', 'Nome'],
  ['campus', 'Campus'],
  ['codigo_curso', 'Código Curso'],
  ['curso', 'Curso'],
  ['email_academico', 'Email Acadêmico'],
  ['polo', 'Polo'],
  ['situacao_curso', 'Situação no Curso'],
  ['situacao_periodo', 'Situação no Período'],
  ['periodo_letivo', 'Período Letivo'],
  ['periodo_curso', 'Período do Curso']
];

function exportRows() {
  return data.map(r => Object.fromEntries(COLS.map(([k, l]) => [l, r[k] || ''])));
}

function blob(c, t, n) {
  let b = new Blob([c], { type: t });
  let u = URL.createObjectURL(b);
  let a = document.createElement('a');
  a.href = u; a.download = n;
  document.body.appendChild(a);
  a.click(); a.remove();
  URL.revokeObjectURL(u);
}

function loadScript(url) {
  return new Promise((resolve, reject) => {
    if (document.querySelector('script[src="' + url + '"]')) { resolve(); return; }
    let s = document.createElement('script');
    s.src = url;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

async function exp() {
  let f = $('format').value;
  let btn = $('export');
  btn.classList.add('export-loading');
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Exportando...';

  try {
    if (f === 'xlsx') {
      await loadScript('https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js');
      let ws = XLSX.utils.json_to_sheet(exportRows());
      let wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Discentes');
      XLSX.writeFile(wb, 'discentes_ced_uncisal.xlsx');
    } else if (f === 'pdf') {
      await loadScript('https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js');
      await loadScript('https://cdn.jsdelivr.net/npm/jspdf-autotable@3.8.4/dist/jspdf.plugin.autotable.min.js');
      let doc = new jspdf.jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
      doc.text('CED Uncisal - Relatório de Discentes', 40, 36);
      doc.autoTable({
        head: [COLS.map(x => x[1])],
        body: data.map(r => COLS.map(([k]) => r[k] || '')),
        startY: 54,
        styles: { fontSize: 6, cellPadding: 3 },
        headStyles: { fillColor: [45, 54, 216] }
      });
      doc.save('discentes_ced_uncisal.pdf');
    } else {
      let h = COLS.map(x => x[1]).join(';');
      let rs = data.map(r => COLS.map(([k]) => '"' + String(r[k] || '').replace(/"/g, '""') + '"').join(';'));
      blob('\ufeff' + [h, ...rs].join('\r\n'), 'text/csv;charset=utf-8;', 'discentes_ced_uncisal.csv');
    }
  } catch (e) {
    console.error('Erro ao exportar:', e);
    alert('Erro ao exportar. Tente novamente.');
  } finally {
    btn.classList.remove('export-loading');
    btn.innerHTML = '<i class="fa-solid fa-file-arrow-down"></i> Baixar relatório';
  }
}

/* ========================================
   Initialization
   ======================================== */

document.addEventListener('DOMContentLoaded', async () => {
  // Setup fade-in animations
  setupFadeIn();

  // Create dropdowns
  FIELDS.forEach(createDrop);

  // Load initial data from data.json
  const loaded = await loadInitialData();
  if (loaded) {
    populate();
    render();
  }

  // Event listeners
  document.addEventListener('click', e => {
    if (!e.target.closest('.multi'))
      document.querySelectorAll('.multi.open').forEach(m => m.classList.remove('open'));
  });

  $('search').oninput = e => { filters.search = e.target.value; apply(); };

  $('clear').onclick = () => {
    FIELDS.forEach(f => { filters[f.key] = []; updateDrop(f.id); });
    filters.search = ''; $('search').value = '';
    sortKey = null; sortDir = 'asc';
    document.querySelectorAll('thead th').forEach(h => h.classList.remove('sorted'));
    apply();
  };

  $('perPage').onchange = e => {
    perPage = e.target.value === 'ALL' ? 'ALL' : Number(e.target.value);
    page = 1;
    table();
  };

  $('prev').onclick = () => { if (page > 1) { page--; table(); } };
  $('next').onclick = () => { page++; table(); };
  $('export').onclick = exp;

  $('theme').onclick = () => {
    document.documentElement.classList.toggle('dark');
    // Destroy and recreate charts for theme change
    Object.keys(charts).forEach(k => { charts[k].destroy(); delete charts[k]; });
    chartsRender();
  };

  // Setup sorting on table headers
  setupSorting();

  // Setup chart reveal animations
  setupChartReveal();

  // Start refresh cycle (60s, pauses when tab hidden)
  refresh();
  startRefreshCycle();

  window.addEventListener('focus', () => {
    if (!document.hidden) refresh();
  });

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) refresh();
  });
});
