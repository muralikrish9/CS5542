/**
 * app.js — KC Drug Market Dashboard (Neon Rewrite)
 * ApexCharts + custom calendar DOM + SSE streaming chat
 */

// ─── Global state ────────────────────────────────────────────────────────────
let dashData = null;
let charts = {};
let chatHistory = [];
let isStreaming = false;

// ─── Neon color palette ──────────────────────────────────────────────────────
const NEON_COLORS = ['#ff2d78', '#00ffcc', '#7dfbff', '#ffab00', '#ff716c', '#b1cbce'];

const BASE_OPTS = {
  chart: {
    background: 'transparent',
    toolbar: { show: true, tools: { download: true, selection: true, zoom: true, zoomin: true, zoomout: true, pan: true, reset: true } }
  },
  theme: { mode: 'dark' },
  grid: { borderColor: 'rgba(255,255,255,0.06)', strokeDashArray: 4 },
  tooltip: { theme: 'dark' },
  colors: NEON_COLORS,
};

// ─── Data fetch ──────────────────────────────────────────────────────────────
async function fetchData() {
  const res = await fetch('/api/data');
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function refreshData() {
  try {
    dashData = await fetchData();
    renderKPIs();
    renderForecast();
    renderCalendarGrid('deaths');
    renderDeathsChart();
    renderArrestsChart();
    renderOverlayChart();
    renderXcorrChart();
    renderXcorrTable();
    renderAnomalyChart();
    renderAnomalyList();
    renderDtwChart();
  } catch (err) {
    console.error('Data load error:', err);
  }
}

// ─── KPI render ──────────────────────────────────────────────────────────────
function renderKPIs() {
  const k = dashData.kpi;
  document.getElementById('kpi-deaths').textContent = k.total_deaths.toLocaleString();
  document.getElementById('kpi-arrests').textContent = k.total_arrests.toLocaleString();
  document.getElementById('kpi-sig').textContent = k.sig_correlations;
  document.getElementById('kpi-anomalies').textContent = k.n_anomalies;
  document.getElementById('kpi-range').textContent = k.date_range;
  document.getElementById('data-range-badge').textContent = k.date_range;

  if (dashData.synthetic) {
    document.getElementById('synth-badge').classList.add('show');
  }
}

// ─── Calendar: tab click handler ─────────────────────────────────────────────
function calTabClick(btn, mode) {
  document.querySelectorAll('#calendar-filter .filter-tab').forEach(b => {
    b.classList.remove('active-cyan');
    b.classList.remove('active');
    b.classList.add('filter-tab');
  });
  btn.classList.add('active-cyan');

  document.getElementById('cal-label').textContent = mode === 'arrests'
    ? 'KCPD drug arrests per month · Jackson County, MO'
    : 'Total drug-induced deaths per month · Jackson County, MO';

  renderCalendarGrid(mode);
}

// ─── Forecast / Early Warning ────────────────────────────────────────────────
function renderForecast() {
  const fc = dashData.forecast;
  if (!fc) return;

  const alertColors = {
    critical: '#ff2d78',
    elevated: '#ffab00',
    moderate: '#7dfbff',
    normal:   '#00ffcc',
  };
  const color = alertColors[fc.alert] || '#00ffcc';

  // ── Alert banner ──────────────────────────────────────────────────────────
  const banner = document.getElementById('alert-banner');
  banner.style.display = 'flex';
  banner.style.background = `rgba(${fc.alert === 'critical' ? '255,45,120' : fc.alert === 'elevated' ? '255,171,0' : '0,255,204'}, 0.08)`;
  banner.style.borderColor = color;

  const icon = document.getElementById('alert-icon');
  icon.style.color = color;
  icon.style.textShadow = `0 0 12px ${color}`;
  icon.textContent = fc.alert === 'critical' ? 'emergency' : fc.alert === 'elevated' ? 'warning' : 'check_circle';

  document.getElementById('alert-level-label').textContent = `${fc.alert.toUpperCase()} RISK`;
  document.getElementById('alert-level-label').style.color = color;
  document.getElementById('alert-rec').textContent = fc.recommendation;
  document.getElementById('alert-next-q').textContent = fc.next_quarter_total.toLocaleString();
  document.getElementById('alert-next-q').style.color = color;

  // Nav dot
  const navDot = document.getElementById('nav-alert-dot');
  if (navDot) { navDot.textContent = fc.alert.toUpperCase(); navDot.style.color = color; navDot.style.background = `rgba(${fc.alert === 'critical' ? '255,45,120' : '0,255,204'}, 0.15)`; navDot.style.borderColor = color; }

  // ── Stats panel ───────────────────────────────────────────────────────────
  document.getElementById('fc-r2').textContent = fc.r2;
  document.getElementById('fc-r2-badge').textContent = `R²=${fc.r2}`;
  document.getElementById('fc-std').textContent = `±${fc.std_err}`;
  document.getElementById('fc-hmean').textContent = `${fc.hist_mean}/mo`;

  // Monthly prediction list
  const list = document.getElementById('fc-monthly-list');
  list.innerHTML = fc.forecast_labels.map((label, i) => {
    const pred = fc.predicted[i];
    const lo = fc.lower_90[i];
    const hi = fc.upper_90[i];
    const pct = ((pred - fc.hist_mean) / fc.hist_mean * 100).toFixed(0);
    const sign = pct >= 0 ? '+' : '';
    const barW = Math.min(100, Math.round(pred / (fc.hist_mean * 1.5) * 100));
    return `<div>
      <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:4px;">
        <span style="font-family:'Work Sans',sans-serif; font-size:11px; font-weight:600; color:#9e8a8b; text-transform:uppercase;">${label}</span>
        <span style="font-family:'Epilogue',sans-serif; font-weight:700; font-size:15px; color:${color};">${Math.round(pred)}</span>
      </div>
      <div style="height:6px; background:rgba(255,255,255,0.06); border-radius:9999px; overflow:hidden; margin-bottom:3px;">
        <div style="height:100%; width:${barW}%; background:linear-gradient(90deg,${color},${color}88); border-radius:9999px; transition:width 0.6s ease;"></div>
      </div>
      <div style="font-family:'Work Sans',sans-serif; font-size:10px; color:#9e8a8b;">90% CI: ${lo}–${hi} &nbsp;·&nbsp; <span style="color:${pct >= 0 ? '#ff2d78' : '#00ffcc'}">${sign}${pct}% vs avg</span></div>
    </div>`;
  }).join('');

  // ── Validation panel ─────────────────────────────────────────────────────
  const val = fc.validation;
  const vPanel = document.getElementById('validation-panel');
  if (val && val.months && val.months.length > 0 && !val.error) {
    vPanel.style.display = 'block';
    document.getElementById('vsrr-as-of').textContent = val.data_as_of || '';
    const trendColor = val.trend_2024 === 'declining' ? '#00ffcc' : '#ff2d78';
    const trendArrow = val.trend_2024 === 'declining' ? '↓' : '↑';
    document.getElementById('validation-body').innerHTML = `
      <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:6px;">
        ${Object.entries(val.year_totals || {}).map(([yr, total]) =>
          `<div style="text-align:center; padding:4px 8px; border-radius:6px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);">
            <div style="font-family:'Work Sans',sans-serif; font-size:9px; color:#9e8a8b;">${yr}</div>
            <div style="font-family:'Epilogue',sans-serif; font-size:12px; font-weight:700; color:#ffdede;">${total}</div>
          </div>`
        ).join('')}
        <div style="text-align:center; padding:4px 8px; border-radius:6px; background:rgba(0,255,204,0.06); border:1px solid rgba(0,255,204,0.2);">
          <div style="font-family:'Work Sans',sans-serif; font-size:9px; color:#9e8a8b;">Trend</div>
          <div style="font-family:'Epilogue',sans-serif; font-size:12px; font-weight:700; color:${trendColor};">${trendArrow} ${val.trend_2024}</div>
        </div>
      </div>
      <div style="font-family:'Work Sans',sans-serif; font-size:11px; color:#9e8a8b; margin-bottom:6px;">
        Jan–Apr 2025 all-cause OD deaths: <strong style="color:${val.net_yoy_delta_q1 <= 0 ? '#00ffcc' : '#ff2d78'}">${val.net_yoy_delta_q1 > 0 ? '+' : ''}${val.net_yoy_delta_q1}</strong> vs same period 2024 &nbsp;·&nbsp;
        Model alert: <strong style="color:${color}">${fc.alert.toUpperCase()}</strong> ✓
      </div>
      <div style="display:flex; gap:6px; flex-wrap:wrap;">
        ${val.months.map(m => {
          const deltaColor = m.yoy_delta <= 0 ? '#00ffcc' : '#ff2d78';
          return `<div style="flex:1; min-width:80px; padding:6px 8px; border-radius:8px; background:rgba(255,171,0,0.05); border:1px solid rgba(255,171,0,0.2);">
            <div style="font-family:'Work Sans',sans-serif; font-size:9px; font-weight:600; color:#ffab00; text-transform:uppercase;">${m.label}</div>
            <div style="font-family:'Epilogue',sans-serif; font-size:13px; font-weight:700; color:#ffdede;">${m.vsrr_monthly_rate}</div>
            <div style="font-family:'Work Sans',sans-serif; font-size:9px; color:#9e8a8b;">all-cause avg/mo</div>
            <div style="font-family:'Work Sans',sans-serif; font-size:9px; color:${deltaColor};">YoY: ${m.yoy_delta > 0 ? '+' : ''}${m.yoy_delta}</div>
            <div style="font-family:'Work Sans',sans-serif; font-size:9px; color:#7dfbff; margin-top:2px;">model: ${m.predicted_alcohol}</div>
          </div>`;
        }).join('')}
      </div>`;
  } else {
    vPanel.style.display = 'none';
  }

  // ── Forecast chart ────────────────────────────────────────────────────────
  const el = document.getElementById('chart-forecast');
  el.innerHTML = '';

  const lastHistX = fc.historical_dates[fc.historical_dates.length - 1];
  const lastHistY = fc.historical_deaths[fc.historical_deaths.length - 1];
  const forecastEnd = fc.forecast_dates[fc.forecast_dates.length - 1] + 86400000 * 15;

  // Historical area (all 60 months of actual deaths)
  const histData = fc.historical_dates.map((d, i) => ({ x: d, y: fc.historical_deaths[i] }));

  // Forecast line — bridge from last real point so it connects cleanly
  const fcastData = [
    { x: lastHistX, y: lastHistY },
    ...fc.forecast_dates.map((d, i) => ({ x: d, y: fc.predicted[i] })),
  ];

  const opts = {
    ...BASE_OPTS,
    chart: {
      ...BASE_OPTS.chart,
      type: 'area',
      height: 340,
      id: 'forecast-chart',
      toolbar: { show: false },
    },
    series: [
      { name: fc.target_col + ' (actual)', type: 'area', data: histData },
      { name: 'Predicted deaths', type: 'line', data: fcastData },
    ],
    stroke: {
      curve: ['smooth', 'straight'],
      width: [2, 2.5],
      dashArray: [0, 7],
    },
    colors: ['#ff2d78', color],
    fill: {
      type: ['gradient', 'solid'],
      opacity: [1, 0],
      gradient: {
        type: 'vertical',
        gradientToColors: ['#ff2d78'],
        opacityFrom: 0.35,
        opacityTo: 0.02,
        stops: [0, 85, 100],
      },
    },
    markers: {
      size: [0, 6],
      colors: ['#0a0a12'],
      strokeColors: [color, color],
      strokeWidth: [0, 2.5],
      hover: { size: 8 },
    },
    dataLabels: {
      enabled: true,
      enabledOnSeries: [1],
      formatter: (v, { dataPointIndex }) => dataPointIndex === 0 ? '' : Math.round(v),
      style: {
        fontSize: '11px',
        fontFamily: "'Epilogue',sans-serif",
        fontWeight: '700',
        colors: [color],
      },
      background: {
        enabled: true,
        foreColor: color,
        borderColor: color,
        borderRadius: 4,
        borderWidth: 1,
        opacity: 0.12,
        padding: { left: 5, right: 5, top: 2, bottom: 2 },
      },
      offsetY: -10,
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false,
        style: { colors: '#9e8a8b', fontSize: '11px', fontFamily: "'Work Sans',sans-serif" },
        format: "MMM 'yy",
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      title: { text: 'Deaths / month', style: { color: '#9e8a8b', fontFamily: "'Work Sans',sans-serif" } },
      labels: { style: { colors: '#9e8a8b', fontFamily: "'Work Sans',sans-serif" } },
      min: 0,
    },
    annotations: {
      xaxis: [
        // Forecast zone — shaded background
        {
          x: lastHistX,
          x2: forecastEnd,
          fillColor: color,
          opacity: 0.05,
          label: {
            text: 'FORECAST ZONE',
            borderColor: 'transparent',
            position: 'center',
            style: {
              background: 'transparent',
              color,
              fontSize: '9px',
              fontFamily: "'Work Sans',sans-serif",
              fontWeight: '700',
              letterSpacing: '0.08em',
            },
            offsetY: 18,
          },
        },
        // Divider line
        {
          x: lastHistX,
          strokeDashArray: 5,
          borderColor: 'rgba(255,255,255,0.2)',
          label: {
            text: 'NOW',
            borderColor: 'transparent',
            style: {
              background: 'rgba(255,255,255,0.06)',
              color: '#9e8a8b',
              fontSize: '9px',
              fontFamily: "'Work Sans',sans-serif",
            },
            offsetY: 2,
          },
        },
        // COVID line
        {
          x: new Date('2020-03-01').getTime(),
          strokeDashArray: 4,
          borderColor: 'rgba(255,171,0,0.5)',
          label: {
            text: 'COVID-19',
            borderColor: 'transparent',
            style: {
              background: 'rgba(255,171,0,0.08)',
              color: '#ffab00',
              fontSize: '9px',
              fontFamily: "'Work Sans',sans-serif",
            },
            orientation: 'vertical',
            offsetY: -2,
          },
        },
      ],
      yaxis: [{
        y: fc.hist_mean,
        strokeDashArray: 4,
        borderColor: 'rgba(255,255,255,0.15)',
        label: {
          text: `avg ${fc.hist_mean}/mo`,
          borderColor: 'transparent',
          position: 'left',
          offsetX: 8,
          style: {
            background: 'transparent',
            color: '#9e8a8b',
            fontSize: '10px',
            fontFamily: "'Work Sans',sans-serif",
          },
        },
      }],
    },
    legend: {
      position: 'top',
      labels: { colors: '#ffdede', fontFamily: "'Work Sans',sans-serif", fontSize: '11px' },
    },
    tooltip: {
      ...BASE_OPTS.tooltip,
      x: { format: 'MMM yyyy' },
      shared: false,
      intersect: true,
      y: { formatter: (v, { seriesIndex }) => seriesIndex === 1
        ? `${Math.round(v)} projected deaths`
        : `${Math.round(v)} actual deaths`
      },
    },
  };

  if (charts['forecast']) charts['forecast'].destroy();
  charts['forecast'] = new ApexCharts(el, opts);
  charts['forecast'].render();
}

// ─── Deaths chart tab click ───────────────────────────────────────────────────
function deathsTabClick(btn, mode) {
  document.querySelectorAll('#deaths-filter .filter-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderDeathsChart(mode);
}

// ─── Calendar heatmap (custom DOM, NOT ApexCharts) ────────────────────────────
function renderCalendarGrid(mode) {
  buildCalGrid(mode);
}

function buildCalGrid(mode) {
  const container = document.getElementById('cal-grid');
  container.innerHTML = '';

  const calData = mode === 'arrests'
    ? dashData.calendar.arrests
    : dashData.calendar.deaths;

  if (!calData) {
    container.innerHTML = '<div style="color:#9e8a8b;text-align:center;padding:20px;font-family:\'Work Sans\',sans-serif;font-size:12px;">No data available</div>';
    return;
  }

  const months = dashData.calendar.months; // ['Jan',...,'Dec']
  const years = Object.keys(calData).sort((a, b) => b - a); // descending

  // Build anomaly lookup: Set of "YYYY-Mon" strings
  const anomalySet = new Set();
  if (dashData.anomalies && dashData.anomalies.length) {
    dashData.anomalies.forEach(a => {
      const d = new Date(a.date);
      const yr = String(d.getFullYear());
      const mo = months[d.getMonth()];
      anomalySet.add(`${yr}-${mo}`);
    });
  }

  // Compute per-year monthly averages for tooltip
  const yearAvgs = {};
  years.forEach(yr => {
    const vals = months.map(m => calData[yr][m] || 0).filter(v => v > 0);
    yearAvgs[yr] = vals.length ? (vals.reduce((s, v) => s + v, 0) / vals.length) : 0;
  });

  // Max value for tier thresholds
  let maxVal = 1;
  years.forEach(yr => {
    months.forEach(m => {
      const v = calData[yr][m] || 0;
      if (v > maxVal) maxVal = v;
    });
  });

  function getTier(val) {
    if (val === 0) return 0;
    const ratio = val / maxVal;
    if (ratio < 0.15) return 1;
    if (ratio < 0.35) return 2;
    if (ratio < 0.65) return 3;
    return 4;
  }

  // Wrapper uses CSS grid
  const wrapper = document.createElement('div');
  wrapper.style.cssText = 'display:inline-block; min-width:max-content;';

  // Month headers row
  const headerRow = document.createElement('div');
  headerRow.style.cssText = 'display:grid; grid-template-columns:40px repeat(12,26px); gap:6px; margin-bottom:4px;';

  const emptyCell = document.createElement('div');
  emptyCell.style.width = '40px';
  headerRow.appendChild(emptyCell);

  months.forEach(m => {
    const cell = document.createElement('div');
    cell.style.cssText = 'width:26px; text-align:center; font-family:\'Work Sans\',sans-serif; font-size:10px; font-weight:600; letter-spacing:0.05em; color:#9e8a8b; text-transform:uppercase;';
    cell.textContent = m.slice(0, 1);
    headerRow.appendChild(cell);
  });

  wrapper.appendChild(headerRow);

  // Year rows
  years.forEach(yr => {
    const row = document.createElement('div');
    row.style.cssText = 'display:grid; grid-template-columns:40px repeat(12,26px); gap:6px; margin-bottom:4px;';

    // Year label
    const yearLabel = document.createElement('div');
    yearLabel.style.cssText = 'width:40px; font-family:\'Work Sans\',sans-serif; font-size:10px; font-weight:600; color:#9e8a8b; display:flex; align-items:center; padding-right:4px; justify-content:flex-end;';
    yearLabel.textContent = yr;
    row.appendChild(yearLabel);

    months.forEach(m => {
      const val = calData[yr][m] || 0;
      const tier = getTier(val);
      const isAnomaly = anomalySet.has(`${yr}-${m}`);
      const avg = yearAvgs[yr];

      const cell = document.createElement('div');
      cell.className = `cal-cell tier-${tier}${isAnomaly ? ' anomaly-ring' : ''}`;
      cell.dataset.year = yr;
      cell.dataset.month = m;
      cell.dataset.val = val;
      cell.dataset.avg = avg.toFixed(1);

      // Tooltip events
      cell.addEventListener('mouseenter', () => {
        const tt = document.getElementById('cal-tooltip');
        const ttDate = document.getElementById('cal-tt-date');
        const ttVal = document.getElementById('cal-tt-val');
        const ttAvg = document.getElementById('cal-tt-avg');
        const ttAnom = document.getElementById('cal-tt-anomaly');

        ttDate.textContent = `${m} ${yr}`;
        const label = mode === 'arrests' ? 'arrests' : 'deaths';
        ttVal.textContent = `${val.toLocaleString()} ${label}`;

        if (avg > 0) {
          const pct = ((val - avg) / avg * 100).toFixed(0);
          const sign = pct >= 0 ? '+' : '';
          ttAvg.textContent = `${sign}${pct}% vs ${yr} avg (${avg.toFixed(0)})`;
        } else {
          ttAvg.textContent = '';
        }

        if (isAnomaly) {
          ttAnom.textContent = '⚠ Statistical anomaly (z ≥ 2.0)';
          ttAnom.classList.remove('hidden');
        } else {
          ttAnom.classList.add('hidden');
        }

        tt.style.display = 'block';
      });

      cell.addEventListener('mouseleave', () => {
        document.getElementById('cal-tooltip').style.display = 'none';
      });

      row.appendChild(cell);
    });

    wrapper.appendChild(row);
  });

  container.appendChild(wrapper);
}

// ─── Deaths timeline ─────────────────────────────────────────────────────────
function renderDeathsChart(mode = 'all') {
  const el = document.getElementById('chart-deaths');
  el.innerHTML = '';

  // Get sorted timestamps from first available series
  const firstKey = Object.keys(dashData.deaths_series)[0];
  const timestamps = (dashData.deaths_series[firstKey] || []).map(d => d.x);

  const series = Object.entries(dashData.deaths_series)
    .filter(([name]) => {
      if (mode === 'od') return name.includes('OD') || name.includes('Fentanyl') || name.includes('Heroin');
      return !name.includes('Non-Drug');
    })
    .map(([name, data]) => ({
      name,
      data: data.map(d => d.y || 0)
    }));

  const opts = {
    ...BASE_OPTS,
    chart: {
      ...BASE_OPTS.chart,
      type: 'bar',
      height: 360,
      id: 'deaths-chart',
      stacked: true,
      stackType: 'normal',
    },
    series,
    plotOptions: {
      bar: {
        columnWidth: '75%',
        borderRadius: 3,
        borderRadiusApplication: 'end',
        borderRadiusWhenStacked: 'last',
      }
    },
    stroke: { width: 0 },
    fill: { opacity: 0.92 },
    colors: ['#ff2d78', '#00ffcc', '#7dfbff', '#ffab00'],
    xaxis: {
      type: 'datetime',
      categories: timestamps,
      labels: {
        datetimeUTC: false,
        style: { colors: '#9e8a8b', fontSize: '11px', fontFamily: '\'Work Sans\',sans-serif' },
        format: "MMM 'yy",
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      title: { text: 'Deaths / month', style: { color: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } },
      labels: { style: { colors: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } }
    },
    legend: {
      position: 'top',
      labels: { colors: '#ffdede', fontFamily: '\'Work Sans\',sans-serif', fontSize: '11px' }
    },
    tooltip: {
      ...BASE_OPTS.tooltip,
      x: { format: 'MMM yyyy' },
      shared: true,
      intersect: false,
      y: { formatter: v => `${v} deaths` }
    },
    dataLabels: { enabled: false },
    annotations: {
      xaxis: [{
        x: new Date('2020-03-01').getTime(),
        borderColor: 'rgba(255,171,0,0.7)',
        strokeDashArray: 4,
        label: {
          text: 'COVID-19',
          borderColor: 'transparent',
          style: {
            background: 'rgba(255,171,0,0.15)',
            color: '#ffab00',
            fontSize: '10px',
            fontFamily: "'Work Sans',sans-serif",
            padding: { left: 6, right: 6, top: 3, bottom: 3 },
          },
          orientation: 'vertical',
          offsetX: 0,
          offsetY: -2,
        }
      }],
      yaxis: (() => {
        const allVals = Object.values(dashData.deaths_series).flatMap(s => s.map(d => d.y || 0));
        const avg = allVals.reduce((a, b) => a + b, 0) / (allVals.length || 1);
        const totalPerMonth = {};
        Object.values(dashData.deaths_series).forEach(s => s.forEach(d => {
          totalPerMonth[d.x] = (totalPerMonth[d.x] || 0) + (d.y || 0);
        }));
        const totals = Object.values(totalPerMonth);
        const monthlyAvg = totals.reduce((a, b) => a + b, 0) / (totals.length || 1);
        return [{
          y: Math.round(monthlyAvg),
          borderColor: 'rgba(255,45,120,0.4)',
          strokeDashArray: 5,
          label: {
            text: `Avg ${Math.round(monthlyAvg)}/mo`,
            borderColor: 'transparent',
            position: 'left',
            offsetX: 8,
            style: {
              background: 'rgba(255,45,120,0.1)',
              color: '#ff2d78',
              fontSize: '10px',
              fontFamily: "'Work Sans',sans-serif",
            }
          }
        }];
      })(),
    },
  };

  if (charts['deaths']) { charts['deaths'].destroy(); }
  charts['deaths'] = new ApexCharts(el, opts);
  charts['deaths'].render();
}

// ─── Arrests — smooth glow area with dot markers ─────────────────────────────
function renderArrestsChart() {
  const el = document.getElementById('chart-arrests');
  el.innerHTML = '';

  if (!dashData.arrests_series) {
    el.innerHTML = '<div style="color:#9e8a8b;text-align:center;padding:40px;font-family:\'Work Sans\',sans-serif;font-size:12px;">No arrest data available</div>';
    return;
  }

  // Find peak for annotation
  const peak = dashData.arrests_series.reduce((p, c) => c.y > p.y ? c : p, { y: 0, x: 0 });

  const opts = {
    ...BASE_OPTS,
    chart: {
      ...BASE_OPTS.chart,
      type: 'area',
      height: 310,
      id: 'arrests-chart',
      sparkline: { enabled: false },
      dropShadow: {
        enabled: true,
        top: 4,
        blur: 12,
        color: '#00ffcc',
        opacity: 0.18,
      },
    },
    series: [{ name: 'Drug Arrests', data: dashData.arrests_series }],
    stroke: { curve: 'smooth', width: 2.5, colors: ['#00ffcc'] },
    colors: ['#00ffcc'],
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.45,
        opacityTo: 0.02,
        stops: [0, 90, 100],
        colorStops: [{
          offset: 0, color: '#00ffcc', opacity: 0.45
        }, {
          offset: 100, color: '#7dfbff', opacity: 0
        }]
      }
    },
    markers: {
      size: 4,
      colors: ['#0a0a12'],
      strokeColors: '#00ffcc',
      strokeWidth: 2,
      shape: 'circle',
      hover: { size: 7, sizeOffset: 3 }
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false,
        style: { colors: '#9e8a8b', fontSize: '10px', fontFamily: '\'Work Sans\',sans-serif' },
        format: "MMM 'yy",
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      title: { text: 'Arrests / month', style: { color: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } },
      labels: { style: { colors: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } },
      min: 0,
    },
    annotations: {
      xaxis: [{
        x: new Date('2020-03-01').getTime(),
        borderColor: 'rgba(255,171,0,0.5)',
        strokeDashArray: 4,
        label: {
          text: 'COVID-19',
          borderColor: 'transparent',
          style: {
            background: 'rgba(255,171,0,0.12)',
            color: '#ffab00',
            fontSize: '10px',
            fontFamily: "'Work Sans',sans-serif",
            padding: { left: 6, right: 6, top: 3, bottom: 3 },
          },
          orientation: 'vertical',
          offsetY: -2,
        }
      }],
      points: peak.y > 0 ? [{
        x: peak.x,
        y: peak.y,
        marker: { size: 8, fillColor: '#00ffcc', strokeColor: '#0a0a12', strokeWidth: 2, radius: 4 },
        label: {
          text: `Peak: ${peak.y}`,
          borderColor: 'rgba(0,255,204,0.4)',
          style: {
            background: 'rgba(0,255,204,0.1)',
            color: '#00ffcc',
            fontSize: '10px',
            fontFamily: '\'Work Sans\',sans-serif',
            padding: { left: 6, right: 6, top: 3, bottom: 3 },
          },
          offsetY: -12,
        }
      }] : []
    },
    tooltip: {
      ...BASE_OPTS.tooltip,
      x: { format: 'MMM yyyy' },
      y: { formatter: v => `${v} arrests` }
    },
  };

  if (charts['arrests']) { charts['arrests'].destroy(); }
  charts['arrests'] = new ApexCharts(el, opts);
  charts['arrests'].render();
}

// ─── Dual-axis overlay ───────────────────────────────────────────────────────
function renderOverlayChart() {
  const el = document.getElementById('chart-overlay');
  el.innerHTML = '';

  const odKey = dashData.drug_columns.find(c => c.includes('OD') || c.includes('Unintentional')) || dashData.drug_columns[0];
  const odData = dashData.deaths_series[odKey] || [];

  const series = [
    { name: 'OD Deaths', data: odData, type: 'line' },
  ];
  if (dashData.arrests_series) {
    series.push({ name: 'Arrests', data: dashData.arrests_series, type: 'column' });
  }

  const opts = {
    ...BASE_OPTS,
    chart: { ...BASE_OPTS.chart, height: 260, id: 'overlay-chart' },
    series,
    stroke: { width: [2.5, 0], curve: 'smooth' },
    colors: ['#ff2d78', 'rgba(0,255,204,0.45)'],
    fill: { opacity: [1, 0.65] },
    plotOptions: { bar: { columnWidth: '65%', borderRadius: 2 } },
    xaxis: {
      type: 'datetime',
      labels: { datetimeUTC: false, style: { colors: '#9e8a8b', fontSize: '11px', fontFamily: '\'Work Sans\',sans-serif' } },
      axisBorder: { show: false }, axisTicks: { show: false },
    },
    yaxis: [
      { title: { text: 'Deaths', style: { color: '#ff2d78', fontFamily: '\'Work Sans\',sans-serif' } }, labels: { style: { colors: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } } },
      { opposite: true, title: { text: 'Arrests', style: { color: '#00ffcc', fontFamily: '\'Work Sans\',sans-serif' } }, labels: { style: { colors: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } } },
    ],
    legend: { position: 'top', labels: { colors: '#ffdede', fontFamily: '\'Work Sans\',sans-serif', fontSize: '11px' } },
    tooltip: { ...BASE_OPTS.tooltip, x: { format: 'MMM yyyy' }, shared: true },
  };

  if (charts['overlay']) { charts['overlay'].destroy(); }
  charts['overlay'] = new ApexCharts(el, opts);
  charts['overlay'].render();
}

// ─── Cross-correlation chart ─────────────────────────────────────────────────
function renderXcorrChart() {
  const el = document.getElementById('chart-xcorr');
  el.innerHTML = '';

  const xcorr = dashData.xcorr;
  if (!xcorr || Object.keys(xcorr).length === 0) {
    el.innerHTML = '<div style="color:#9e8a8b;text-align:center;padding:40px;font-family:\'Work Sans\',sans-serif;font-size:12px;">No cross-correlation data (arrests required)</div>';
    return;
  }

  const entries = Object.entries(xcorr).sort((a, b) => Math.abs(b[1].r) - Math.abs(a[1].r));
  const cats = entries.map(([name]) => name.length > 22 ? name.slice(0, 22) + '…' : name);
  const rValues = entries.map(([, v]) => parseFloat(v.r.toFixed(3)));
  const colors = entries.map(([, v]) => v.significant ? (v.r > 0 ? '#00ffcc' : '#ff2d78') : 'rgba(255,255,255,0.15)');

  const opts = {
    ...BASE_OPTS,
    chart: { ...BASE_OPTS.chart, type: 'bar', height: 280 },
    series: [{ name: 'Pearson r', data: rValues }],
    plotOptions: {
      bar: {
        horizontal: true,
        barHeight: '55%',
        borderRadius: 4,
        distributed: true,
        dataLabels: { position: 'right' },
      }
    },
    colors,
    dataLabels: {
      enabled: true,
      formatter: v => v.toFixed(3),
      style: { fontSize: '11px', colors: ['#ffdede'], fontFamily: '\'Work Sans\',sans-serif' },
      offsetX: 6,
    },
    xaxis: {
      categories: cats,
      min: -0.5, max: 0.5,
      tickAmount: 5,
      labels: { style: { colors: '#9e8a8b', fontSize: '11px', fontFamily: '\'Work Sans\',sans-serif' } },
    },
    yaxis: { labels: { style: { colors: '#9e8a8b', fontSize: '11px', fontFamily: '\'Work Sans\',sans-serif' }, maxWidth: 150 } },
    legend: { show: false },
    annotations: {
      xaxis: [
        { x: 0, borderColor: 'rgba(255,255,255,0.15)', label: { text: 'r=0', style: { color: '#9e8a8b', fontSize: '10px', background: 'transparent' } } }
      ]
    },
  };

  if (charts['xcorr']) { charts['xcorr'].destroy(); }
  charts['xcorr'] = new ApexCharts(el, opts);
  charts['xcorr'].render();
}

// ─── Cross-correlation table ─────────────────────────────────────────────────
function renderXcorrTable() {
  const tbody = document.getElementById('xcorr-tbody');
  const xcorr = dashData.xcorr;

  if (!xcorr || Object.keys(xcorr).length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:#9e8a8b;text-align:center;padding:20px;font-size:12px;">No data — arrests required</td></tr>';
    return;
  }

  const rows = Object.entries(xcorr)
    .sort((a, b) => Math.abs(b[1].r) - Math.abs(a[1].r))
    .map(([drug, v]) => {
      const lagDir = v.lag > 0 ? `↑ +${v.lag}mo` : v.lag < 0 ? `↓ ${v.lag}mo` : '→ 0mo';
      const lagColor = v.lag > 0 ? '#00ffcc' : v.lag < 0 ? '#ff2d78' : '#9e8a8b';
      const sigPill = v.significant
        ? '<span class="sig-pill yes">p&lt;0.05</span>'
        : '<span class="sig-pill no">n.s.</span>';
      const rColor = Math.abs(v.r) > 0.3 ? '#7dfbff' : '#9e8a8b';

      return `<tr>
        <td style="font-weight:500;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:'Work Sans',sans-serif;" title="${drug}">${drug}</td>
        <td><span style="color:${lagColor};font-family:'Work Sans',sans-serif;font-size:11px;">${lagDir}</span></td>
        <td><span style="font-family:monospace;color:${rColor};font-weight:600;">${v.r.toFixed(3)}</span></td>
        <td><span style="font-family:monospace;font-size:11px;color:#9e8a8b;">${v.p.toFixed(4)}</span></td>
        <td>${sigPill}</td>
      </tr>`;
    });

  tbody.innerHTML = rows.join('');
}

// ─── Anomaly chart ───────────────────────────────────────────────────────────
function renderAnomalyChart() {
  const el = document.getElementById('chart-anomaly');
  el.innerHTML = '';

  const odKey = dashData.drug_columns.find(c => c.includes('OD') || c.includes('Unintentional')) || dashData.drug_columns[0];
  const lineData = (dashData.deaths_series[odKey] || []).map(pt => ({ x: pt.x, y: pt.y }));

  const annotations = {
    points: dashData.anomalies
      .filter(a => a.source.includes('OD') || a.source.includes('Unintentional'))
      .map(a => ({
        x: a.date,
        y: a.value,
        marker: {
          size: 7,
          fillColor: a.direction === 'spike' ? '#ff2d78' : '#00ffcc',
          strokeColor: a.direction === 'spike' ? 'rgba(255,45,120,0.4)' : 'rgba(0,255,204,0.4)',
          strokeWidth: 3,
          radius: 2,
        },
        label: {
          text: `z=${a.z_score}`,
          borderColor: 'transparent',
          style: {
            background: a.direction === 'spike' ? 'rgba(255,45,120,0.15)' : 'rgba(0,255,204,0.12)',
            color: a.direction === 'spike' ? '#ff2d78' : '#00ffcc',
            fontSize: '10px',
            padding: { left: 4, right: 4, top: 2, bottom: 2 },
            fontFamily: '\'Work Sans\',sans-serif',
          },
          offsetY: -6,
        }
      }))
  };

  const opts = {
    ...BASE_OPTS,
    chart: { ...BASE_OPTS.chart, type: 'line', height: 300 },
    series: [{ name: odKey, data: lineData }],
    stroke: { curve: 'smooth', width: 2 },
    colors: ['#ff2d78'],
    fill: { type: 'gradient', gradient: { opacityFrom: 0.18, opacityTo: 0.02 } },
    xaxis: {
      type: 'datetime',
      labels: { datetimeUTC: false, style: { colors: '#9e8a8b', fontSize: '11px', fontFamily: '\'Work Sans\',sans-serif' } },
      axisBorder: { show: false }, axisTicks: { show: false },
    },
    yaxis: {
      title: { text: 'Deaths / month', style: { color: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } },
      labels: { style: { colors: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } }
    },
    annotations,
    tooltip: { ...BASE_OPTS.tooltip, x: { format: 'MMM yyyy' } },
    markers: { size: 0 },
  };

  if (charts['anomaly']) { charts['anomaly'].destroy(); }
  charts['anomaly'] = new ApexCharts(el, opts);
  charts['anomaly'].render();
}

// ─── Anomaly list ────────────────────────────────────────────────────────────
function renderAnomalyList() {
  const container = document.getElementById('anomaly-list');
  const anomalies = [...dashData.anomalies]
    .filter(a => a.direction === 'spike')
    .sort((a, b) => Math.abs(b.z_score) - Math.abs(a.z_score))
    .slice(0, 20);

  if (!anomalies.length) {
    container.innerHTML = '<div style="color:#9e8a8b;text-align:center;padding:20px;font-size:12px;font-family:\'Work Sans\',sans-serif;">No anomalies detected</div>';
    return;
  }

  container.innerHTML = anomalies.map(a => {
    const date = new Date(a.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    const absZ = Math.abs(a.z_score);
    const zClass = absZ >= 3 ? 'high' : absZ >= 2.5 ? 'med' : 'low';
    const shortSrc = a.source.replace('Deaths: ', '').replace('OD Deaths (Unintentional)', 'OD Deaths').slice(0, 24);

    return `<div class="anomaly-item">
      <div class="anomaly-dot ${a.direction}"></div>
      <div class="anomaly-meta" style="flex:1;min-width:0;">
        <div class="anomaly-source">${shortSrc}</div>
        <div class="anomaly-date">${date} &bull; ${Math.round(a.value)} events</div>
      </div>
      <div class="anomaly-z ${zClass}">z=${a.z_score.toFixed(1)}</div>
    </div>`;
  }).join('');
}

// ─── DTW heatmap ─────────────────────────────────────────────────────────────
function renderDtwChart() {
  const el = document.getElementById('chart-dtw');
  el.innerHTML = '';

  const { labels, matrix } = dashData.dtw;
  if (!labels || !labels.length) {
    el.innerHTML = '<div style="color:#9e8a8b;text-align:center;padding:40px;font-size:12px;font-family:\'Work Sans\',sans-serif;">No DTW data available</div>';
    return;
  }

  const shortLabels = labels.map(l =>
    l.replace('OD Deaths (Unintentional)', 'OD Deaths')
     .replace('Meth/Stimulants', 'Meth')
     .replace('Rx Opioids', 'Rx Opioids')
     .slice(0, 18)
  );

  const series = labels.map((rowLabel, i) => ({
    name: shortLabels[i],
    data: labels.map((colLabel, j) => ({
      x: shortLabels[j],
      y: parseFloat(matrix[i][j].toFixed(3)),
    }))
  }));

  const opts = {
    ...BASE_OPTS,
    chart: { ...BASE_OPTS.chart, type: 'heatmap', height: 320 },
    series,
    dataLabels: {
      enabled: true,
      formatter: v => v === 0 ? '—' : v.toFixed(2),
      style: { fontSize: '11px', colors: ['#ffdede'], fontFamily: '\'Work Sans\',sans-serif' },
    },
    colors: ['#ff2d78'],
    plotOptions: {
      heatmap: {
        shadeIntensity: 0.6,
        radius: 4,
        useFillColorAsStroke: false,
        colorScale: {
          ranges: [
            { from: 0,     to: 0.001, color: '#1a1025', name: 'Same (0)' },
            { from: 0.001, to: 0.3,   color: '#3b1255', name: 'Very similar' },
            { from: 0.3,   to: 0.6,   color: '#7b1fa2', name: 'Similar' },
            { from: 0.6,   to: 1.0,   color: '#c2185b', name: 'Moderate' },
            { from: 1.0,   to: 999,   color: '#ff2d78', name: 'Dissimilar' },
          ]
        }
      }
    },
    xaxis: {
      labels: { style: { colors: '#9e8a8b', fontSize: '10px', fontFamily: '\'Work Sans\',sans-serif' }, rotate: -30 }
    },
    yaxis: {
      labels: { style: { colors: '#9e8a8b', fontSize: '10px', fontFamily: '\'Work Sans\',sans-serif' } }
    },
    legend: { position: 'bottom', labels: { colors: '#9e8a8b', fontFamily: '\'Work Sans\',sans-serif' } },
    tooltip: {
      ...BASE_OPTS.tooltip,
      y: { formatter: v => v === 0 ? 'identical' : `distance: ${v.toFixed(3)}` }
    },
  };

  if (charts['dtw']) { charts['dtw'].destroy(); }
  charts['dtw'] = new ApexCharts(el, opts);
  charts['dtw'].render();
}

// ─── Chat ────────────────────────────────────────────────────────────────────
function clearChat() {
  chatHistory = [];
  const msgs = document.getElementById('chat-messages');
  msgs.innerHTML = `<div class="chat-empty-wrap" id="chat-empty">
    <span class="material-symbols-outlined">chat_bubble_outline</span>
    <p>Ask any question about the KC drug market data. The assistant has access to actual dataset values, cross-correlations, and anomaly events.</p>
  </div>`;
}

function askSuggestion(el) {
  document.getElementById('chat-input').value = el.textContent.trim();
  sendMessage();
}

function autoResizeInput() {
  const ta = document.getElementById('chat-input');
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 100) + 'px';
}

function appendMessage(role, content, streaming = false) {
  const msgs = document.getElementById('chat-messages');
  const empty = document.getElementById('chat-empty');
  if (empty) empty.remove();

  const id = `msg-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const isUser = role === 'user';

  const html = `<div class="message-row ${role}" id="${id}">
    <div class="msg-avatar ${isUser ? 'user-av' : 'assist-av'}">
      <span class="material-symbols-outlined" style="font-size:18px;">${isUser ? 'person' : 'smart_toy'}</span>
    </div>
    <div class="msg-bubble${streaming ? ' typing-cursor' : ''}" id="${id}-bubble">
      ${isUser ? escapeHtml(content) : (content ? renderMd(content) : '')}
    </div>
  </div>`;

  msgs.insertAdjacentHTML('beforeend', html);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

function renderMd(text) {
  try {
    return marked.parse(text, { breaks: true, gfm: true });
  } catch {
    return escapeHtml(text);
  }
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function sendMessage() {
  if (isStreaming) return;
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;

  input.value = '';
  autoResizeInput();

  appendMessage('user', msg);
  chatHistory.push({ role: 'user', content: msg });

  const msgId = appendMessage('assistant', '', true);
  const bubble = document.getElementById(`${msgId}-bubble`);

  isStreaming = true;
  document.getElementById('btn-send').disabled = true;

  let fullText = '';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, history: chatHistory.slice(-8) }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const payload = line.slice(6);
        if (payload === '[DONE]') break;

        try {
          const data = JSON.parse(payload);
          if (data.error) {
            fullText += `\n\n*[Error: ${data.error}]*`;
          } else if (data.text) {
            fullText += data.text;
          }
          bubble.innerHTML = renderMd(fullText);
          bubble.classList.add('typing-cursor');
          document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
        } catch { /* skip malformed */ }
      }
    }
  } catch (err) {
    fullText = `*[Connection error: ${err.message}. Is the server running?]*`;
    bubble.innerHTML = renderMd(fullText);
  }

  bubble.classList.remove('typing-cursor');
  bubble.innerHTML = renderMd(fullText);
  chatHistory.push({ role: 'assistant', content: fullText });

  isStreaming = false;
  document.getElementById('btn-send').disabled = false;
  document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
}

// ─── Sidebar nav active state ─────────────────────────────────────────────────
function setActive(el) {
  document.querySelectorAll('#sidebar .nav-item').forEach(n => n.classList.remove('active'));
  el.classList.add('active');
}

// ─── Input handlers ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('chat-input');

  input.addEventListener('input', autoResizeInput);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Global mousemove for calendar tooltip positioning
  document.addEventListener('mousemove', e => {
    const tt = document.getElementById('cal-tooltip');
    if (tt.style.display === 'none') return;

    let x = e.clientX + 16;
    let y = e.clientY + 16;

    // Flip if near right edge
    if (x + 200 > window.innerWidth) {
      x = e.clientX - 200;
    }
    // Flip if near bottom
    if (y + 120 > window.innerHeight) {
      y = e.clientY - 100;
    }

    tt.style.left = x + 'px';
    tt.style.top = y + 'px';
  });

  refreshData();
});
