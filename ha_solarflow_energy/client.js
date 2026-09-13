const I18N = {
  de: {
    title: "Energie",
    pv: "PV",
    house: "Haus",
    battery: "Akku",
    grid: "Netz",
    today: "heute",
    tomorrow: "morgen",
    forecast_today: "PV Ertrag heute",
    forecast_tomorrow: "PV Ertrag morgen",
    charging: "lädt",
    discharging: "entlädt",
    idle: "bereit",
    no_curve: "Keine Kurve",
    err_no_ha_connection: "Home Assistant Core Plugin nicht installiert.",
    err_fetch_failed: "Home Assistant nicht erreichbar.",
  },
  en: {
    title: "Energy",
    pv: "PV",
    house: "Home",
    battery: "Battery",
    grid: "Grid",
    today: "today",
    tomorrow: "tomorrow",
    forecast_today: "PV yield today",
    forecast_tomorrow: "PV yield tomorrow",
    charging: "charging",
    discharging: "discharging",
    idle: "idle",
    no_curve: "No curve",
    err_no_ha_connection: "Home Assistant Core plugin not installed.",
    err_fetch_failed: "Home Assistant is unreachable.",
  },
};

function t(locale, key) {
  const dict = I18N[locale] || I18N.en;
  return dict[key] || I18N.en[key] || key;
}
function num(locale, n, digits) {
  const s = Number(n).toFixed(digits);
  return locale === "de" ? s.replace(".", ",") : s;
}

function esc(v) {
  return String(v ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}
function power(locale, w) {
  const n = Number(w || 0);
  const a = Math.abs(n);
  if (a < 1000) return `${Math.round(a)} W`;
  return `${num(locale, a / 1000, a >= 10000 ? 1 : 2)} kW`;
}
function pct(v) {
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? `${Math.round(n)} %` : "–";
}
function kwh(locale, v) {
  if (v == null || v === "") return "–";
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? `${num(locale, n, 1)} kWh` : "–";
}
function batterySub(locale, d) {
  const n = Number(d.battery_w || 0);
  if (n < -50) return `${t(locale, "charging")} ${power(locale, Math.abs(n))}`;
  if (n > 50) return `${t(locale, "discharging")} ${power(locale, n)}`;
  return t(locale, "idle");
}
function gridSub(locale, d) {
  const n = Number(d.grid_w || 0);
  if (n < -50) return `${power(locale, Math.abs(n))} → Netz`;
  if (n > 50) return `${power(locale, n)} ← Netz`;
  return t(locale, "idle");
}
function errText(locale, code) {
  const key = `err_${code}`;
  return t(locale, key);
}

function sparkline(locale, points) {
  if (!points || points.length < 2) return `<div class="sf-chart-empty">${esc(t(locale, "no_curve"))}</div>`;
  const W = 440, H = 180;
  const L = 36, R = 8, T = 12, B = 24;
  const iw = W - L - R, ih = H - T - B;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const n = points.length;
  let d = "";
  for (let i = 0; i < n; i++) {
    const x = L + (i / (n - 1)) * iw;
    const y = T + ih - ((points[i] - min) / range) * ih;
    d += `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)} `;
  }
  const area = `${d}L${L + iw} ${T + ih} L${L} ${T + ih} Z`;
  return `
    <svg class="sf-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">
      <path d="${area}" class="area"/>
      <path d="${d}" class="line"/>
      ${max > 0 ? `<text x="${L - 4}" y="${T + 10}" class="axis-y">${power(locale, max)}</text>` : ""}
      <text x="${L - 4}" y="${T + ih}" class="axis-y">${power(locale, min)}</text>
      <line x1="${L}" x2="${L + iw}" y1="${T + ih}" y2="${T + ih}" class="axis-base"/>
    </svg>`;
}

export default function render(shadow, ctx) {
  const d = ctx.data || {};
  const o = (ctx.cell && ctx.cell.options) || {};
  const locale = ctx.locale || "de";
  const title = esc(String(o.label || "").trim() || t(locale, "title"));

  shadow.innerHTML = `
    <link rel="stylesheet" href="/static/style/spectra-widgets.css">
    <link rel="stylesheet" href="/static/icons/phosphor/regular/style.css">
    <link rel="stylesheet" href="/static/icons/phosphor/bold/style.css">
    <link rel="stylesheet" href="/plugins/ha_solarflow_energy/client.css">

    <div class="w sf-widget size-${esc(ctx.cell.size || "md")}" data-widget="ha_solarflow_energy">
      <div class="sf-head">
        <div class="sf-title">${title}</div>
        <div class="sf-time">${esc(d.time || "")}</div>
      </div>

      <div class="sf-main">
        <div class="sf-chart">
          ${sparkline(locale, d.sparkline)}
        </div>

        <div class="sf-stats">
          ${d.error ? `
          <div class="error-row"><i class="ph-bold ph-warning-circle"></i><span>${esc(errText(locale, d.error))}</span></div>
          ` : `
          <div class="stat"><i class="ph-bold ph-sun"></i><span>${esc(t(locale, "pv"))}</span><b>${power(locale, d.pv_w)}</b></div>
          <div class="stat"><i class="ph-bold ph-house-line"></i><span>${esc(t(locale, "house"))}</span><b>${power(locale, d.home_w)}</b></div>
          <div class="stat"><i class="ph-bold ph-battery-high"></i><span>${esc(t(locale, "battery"))} <small>${esc(batterySub(locale, d))}</small></span><b>${pct(d.battery_soc)}</b></div>
          <div class="stat"><i class="ph-bold ph-lightning"></i><span>${esc(t(locale, "grid"))} <small>${esc(gridSub(locale, d))}</small></span><b>${power(locale, d.grid_w)}</b></div>
          `}
        </div>
      </div>

      ${o.show_forecast === false ? "" : `
      <div class="sf-footer">
        <div class="sf-forecast">
          <div class="sf-fc-item">
            <i class="ph-bold ph-sun"></i>
            <span>${esc(t(locale, "forecast_today"))}</span>
            <b>${kwh(locale, d.forecast_today_kwh)}</b>
          </div>
          <div class="sf-fc-item">
            <i class="ph-bold ph-sun-horizon"></i>
            <span>${esc(t(locale, "forecast_tomorrow"))}</span>
            <b>${kwh(locale, d.forecast_tomorrow_kwh)}</b>
          </div>
        </div>
      </div>`}
    </div>`;
}
