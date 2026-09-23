"""Self-contained HTML dashboard for the bank margin & credit-cost bridge.

The organising idea is the audit trail, not a KPI wall. What distinguishes
this project from a table of year-on-year percentages is that every figure
carries a filing page citation and is guarded by a named check, so the
dashboard is built around getting from any number to its source and to the
check that stands behind it.

Everything rendered comes from the project's own CSVs and from the
reconciliation checks in nim_bridge, re-run here rather than copied, so the
page cannot drift from the data. No figure is written into the template.

Output is one file with no external requests, so it opens from disk and
survives being committed to a repository.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from nim_bridge import (INPUT_CSV, STATED_CSV, Q_CURRENT, Q_PRIOR,
                        build_bridge, reconcile, verify_attribution)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "dashboard" / "index.html"

COMPONENTS = [
    ("nii", "Net interest income", "nii_cr"),
    ("other_income", "Other income", "other_income_cr"),
    ("opex", "Operating expenses", "opex_cr"),
    ("provisions", "Provisions", "provisions_cr"),
    ("tax", "Tax", "tax_cr"),
]


def collect() -> dict:
    df = pd.read_csv(INPUT_CSV)
    stated = pd.read_csv(STATED_CSV)
    _, ok123, recs = reconcile(df, stated)
    bridge = build_bridge(df)
    _, ok4, recs4 = verify_attribution(bridge)
    if not (ok123 and ok4):
        raise SystemExit("Reconciliation failed — refusing to build the dashboard.")

    cur = df[df["quarter"] == Q_CURRENT].set_index("bank")
    pri = df[df["quarter"] == Q_PRIOR].set_index("bank")

    banks = []
    for _, r in bridge.iterrows():
        b = r["bank"]
        c, p = cur.loc[b], pri.loc[b]
        banks.append({
            "bank": b,
            "patGrowth": r["pat_growth_yoy_pct"],
            "niiGrowth": r["nii_growth_yoy_pct"],
            "niiSource": r["nii_source"],
            "contrib": {k: r[f"contrib_{k}_pct_of_prior_pat"] for k, _, _ in COMPONENTS},
            "contribCr": {k: r[f"contrib_{k}_cr"] for k, _, _ in COMPONENTS},
            "residualCr": r["rounding_residual_cr"],
            "deltaPatCr": r["delta_pat_cr"],
            "patPrior": p["pat_cr"], "patCurrent": c["pat_cr"],
            "lines": [
                {"key": k, "label": lab,
                 "prior": None if pd.isna(p[col]) else p[col],
                 "current": None if pd.isna(c[col]) else c[col]}
                for k, lab, col in COMPONENTS
            ],
            "nim": [_n(p["nim_pct"]), _n(c["nim_pct"]), _n(r["nim_change_bps"])],
            "gnpa": [_n(p["gnpa_pct"]), _n(c["gnpa_pct"]), _n(r["gnpa_change_bps"])],
            "netNpa": [_n(p["net_npa_pct"]), _n(c["net_npa_pct"])],
            "creditCost": [_n(p["credit_cost_pct"]), _n(c["credit_cost_pct"]),
                           _n(r["credit_cost_change_bps"])],
            "creditCostDef": _s(r["credit_cost_definition"]),
            "advances": [_n(p["advances_cr"]), _n(c["advances_cr"]),
                         _n(r["advances_growth_yoy_pct"])],
            "advancesBasis": _s(r["advances_basis"]),
            "sourcePrior": _s(p["source_page_note"]),
            "sourceCurrent": _s(c["source_page_note"]),
        })

    return {
        "quarterPrior": Q_PRIOR, "quarterCurrent": Q_CURRENT,
        "banks": banks,
        "checks": recs + recs4,
    }


def _n(v):
    return None if pd.isna(v) else float(v)


def _s(v):
    return None if pd.isna(v) else str(v)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bank Margin &amp; Credit-Cost Bridge</title>
<style>
:root{
  --navy:#1a3a5c; --rust:#c0522d; --sage:#5c7a5c; --sky:#4a7c9b; --ochre:#8c6d3f;
  --ink:#16202b; --muted:#5d6b7a; --line:#d8dee5; --bg:#f4f6f8; --panel:#ffffff;
  --pos:#2f6b4f; --neg:#a8412a; --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ink:#e6edf3; --muted:#9bacbd; --line:#2b3745; --bg:#0f151c; --panel:#161e27;
    --navy:#7ba7d0; --pos:#6bbd8f; --neg:#e08163; --sky:#6fa3c4; --ochre:#c0a165;
    --rust:#d97a52; --sage:#8fb08f;
  }
}
:root[data-theme="dark"]{
  --ink:#e6edf3; --muted:#9bacbd; --line:#2b3745; --bg:#0f151c; --panel:#161e27;
  --navy:#7ba7d0; --pos:#6bbd8f; --neg:#e08163; --sky:#6fa3c4; --ochre:#c0a165;
  --rust:#d97a52; --sage:#8fb08f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
.wrap{max-width:1280px;margin:0 auto;padding:20px 16px 48px}
header{border-bottom:2px solid var(--navy);padding-bottom:12px;margin-bottom:18px}
h1{font-size:19px;margin:0 0 3px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13px;margin:0}
.checkstrip{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px}
.chip{display:inline-flex;align-items:center;gap:6px;background:var(--panel);
  border:1px solid var(--line);border-radius:3px;padding:4px 9px;font-size:11.5px;white-space:nowrap}
.dot{width:7px;height:7px;border-radius:50%;flex:none}
.dot.ok{background:var(--pos)} .dot.na{background:var(--muted);opacity:.5}
.chip b{font-weight:600}
h2{font-size:14px;margin:26px 0 3px;letter-spacing:.02em;text-transform:uppercase;color:var(--navy)}
.note{color:var(--muted);font-size:12.5px;margin:0 0 10px;max-width:74ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:4px}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 9px;text-align:right;border-bottom:1px solid var(--line)}
td{white-space:nowrap}
th{background:var(--navy);color:#fff;font-weight:600;font-size:10.5px;
  text-transform:uppercase;letter-spacing:.02em;position:sticky;top:0;
  white-space:normal;line-height:1.25;vertical-align:bottom}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) th{color:#0f151c}}
:root[data-theme="dark"] th{color:#0f151c}
th:first-child,td:first-child{text-align:left}
tbody tr:last-child td{border-bottom:none}
td.num{font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:12.5px}
td.tot{font-weight:700;border-left:2px solid var(--line)}
.pos{color:var(--pos)} .neg{color:var(--neg)}
tr.bankrow{cursor:pointer}
tr.bankrow:hover td{background:color-mix(in srgb,var(--navy) 7%,transparent)}
tr.bankrow[aria-selected="true"] td{background:color-mix(in srgb,var(--navy) 13%,transparent)}
tr.bankrow[aria-selected="true"] td:first-child{box-shadow:inset 3px 0 0 var(--navy)}
.grid{display:grid;grid-template-columns:minmax(0,1.75fr) minmax(0,1fr);gap:16px;align-items:start}
.detail{position:sticky;top:12px}
.detail h3{font-size:13.5px;margin:0 0 2px}
.detail .who{color:var(--muted);font-size:12px;margin:0 0 10px}
.dbody{padding:12px 13px}
.walk{width:100%;max-width:430px;height:auto;display:block;margin:2px 0 10px}
/* capped so the SVG does not scale its text past the page's own type scale when the panel goes full-width at tablet widths */
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:12.5px;margin:0 0 10px}
.kv dt{color:var(--muted)} .kv dd{margin:0;font-family:var(--mono);text-align:right}
.cite{font-size:11.5px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:9px;margin-top:2px;line-height:1.45;white-space:pre-wrap;word-break:break-word}
.cite b{color:var(--ink);font-weight:600;display:block;margin-bottom:2px}
.cite + .cite{margin-top:9px}
.na{color:var(--muted);font-style:italic;font-size:12px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:11.5px;color:var(--muted);margin:8px 2px 0}
.legend i{display:inline-block;width:22px;height:9px;border-radius:2px;vertical-align:-1px;margin-right:5px}
.checks{display:grid;grid-template-columns:repeat(auto-fit,minmax(275px,1fr));gap:12px}
.ck{background:var(--panel);border:1px solid var(--line);border-radius:4px;padding:11px 12px}
.ck h4{margin:0 0 7px;font-size:12.5px;display:flex;align-items:center;gap:7px}
.ck ul{margin:0;padding:0;list-style:none;font-size:11.5px;color:var(--muted)}
.ck li{padding:3.5px 0;border-top:1px solid var(--line);line-height:1.4}
.ck li:first-child{border-top:none}
.ck .s{font-family:var(--mono);color:var(--ink);font-size:11px}
footer{margin-top:30px;padding-top:12px;border-top:1px solid var(--line);
  color:var(--muted);font-size:11.5px;line-height:1.6}
footer a{color:var(--navy)}
@media(max-width:900px){
  .grid{grid-template-columns:1fr}
  .detail{position:static}
  th{position:static}
}
@media(max-width:560px){
  .wrap{padding:14px 12px 36px}
  h1{font-size:17px}
  th,td{padding:6px 7px;font-size:12px}
}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Bank Margin &amp; Credit-Cost Bridge</h1>
  <p class="sub">HDFC · ICICI · Axis · Kotak Mahindra — standalone, __QP__ vs __QC__.
     Every figure page-cited; every comparison gated on four checks.</p>
  <div class="checkstrip" id="strip"></div>
</header>

<h2>Where profit growth came from</h2>
<p class="note">Each component's contribution to the change in profit, in percentage points of
   the prior-year quarter's PAT. Shading is proportional to magnitude — green added to profit,
   red subtracted. Select a bank for its full walk and sources.</p>
<div class="grid">
  <div class="panel scroll"><table id="attrib"></table></div>
  <div class="panel detail"><div class="dbody" id="detail"></div></div>
</div>
<div class="legend">
  <span><i style="background:var(--pos)"></i>added to profit</span>
  <span><i style="background:var(--neg)"></i>reduced profit</span>
  <span>Shading scaled to the largest single contribution in the panel.</span>
</div>

<h2>Margins and asset quality</h2>
<p class="note">Credit-cost <em>levels</em> are not comparable across banks — each defines the
   ratio differently, shown on selection. The change within a bank is. Cells marked
   <span class="na">not disclosed</span> are genuine gaps in the filing, not omissions.</p>
<div class="panel scroll"><table id="ratios"></table></div>

<h2>Reconciliation</h2>
<p class="note">Re-run against the CSVs each time this page is generated. The dashboard is not
   written unless all four pass.</p>
<div class="checks" id="checks"></div>

<footer>
  Source: Q1 FY26 and Q1 FY27 standalone results filings of each bank — URLs and SHA-256 hashes
  in <code>data/raw/source_manifest.md</code>. Generated by <code>src/build_dashboard.py</code>
  from <code>data/final/</code>; no figure on this page is written into the template.<br>
  Shaswat Sharma · <a href="https://github.com/theshaswat">github.com/theshaswat</a>
</footer>
</div>

<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const KEYS = ["nii","other_income","opex","provisions","tax"];
const LABEL = {nii:"Net interest income",other_income:"Other income",
               opex:"Operating expenses",provisions:"Provisions",tax:"Tax"};
const cr = v => v == null ? "—" : (v<0?"−":"") + "₹" + Math.abs(v).toLocaleString("en-IN",
                 {maximumFractionDigits:0});
const pp = v => v == null ? "—" : (v>=0?"+":"−") + Math.abs(v).toFixed(1);
const pct = v => v == null ? "—" : (v>=0?"+":"−") + Math.abs(v).toFixed(1) + "%";
const bps = v => v == null ? null : (v>=0?"+":"−") + Math.abs(v).toFixed(0) + " bps";
const sign = v => v == null ? "" : v>=0 ? "pos" : "neg";

/* Shading is scaled to the largest single contribution actually present, so the
   colour ramp always spans the real range rather than a hard-coded maximum. */
const MAXC = Math.max(...DATA.banks.flatMap(b => KEYS.map(k => Math.abs(b.contrib[k]))));
const tint = v => {
  const a = (Math.abs(v)/MAXC)*0.5;
  return `background:color-mix(in srgb, var(--${v>=0?'pos':'neg'}) ${(a*100).toFixed(1)}%, transparent)`;
};

function attribTable(){
  const head = `<thead><tr><th>Bank</th>${KEYS.map(k=>`<th>${LABEL[k]}</th>`).join("")}
    <th>Reported PAT growth</th></tr></thead>`;
  const rows = DATA.banks.map((b,i)=>`<tr class="bankrow" data-i="${i}" tabindex="0"
      role="button" aria-selected="${i===0}">
    <td>${esc(b.bank)}</td>
    ${KEYS.map(k=>`<td class="num" style="${tint(b.contrib[k])}">${pp(b.contrib[k])}</td>`).join("")}
    <td class="num tot ${sign(b.patGrowth)}">${pct(b.patGrowth)}</td></tr>`).join("");
  $("#attrib").innerHTML = head + `<tbody>${rows}</tbody>`;
  $("#attrib").querySelectorAll(".bankrow").forEach(tr=>{
    const pick = ()=>select(+tr.dataset.i);
    tr.addEventListener("click", pick);
    tr.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();pick();} });
  });
}

/* A waterfall from prior-quarter PAT to current, in Rs Crore. The bars are the
   same five components as the table above, at their actual rupee magnitudes. */
function waterfall(b){
  const steps = KEYS.map(k=>({label:LABEL[k], v:b.contribCr[k]}));
  if (Math.abs(b.residualCr) >= 1) steps.push({label:"Rounding", v:b.residualCr});
  const W=340, rowH=21, padL=132, padR=54, H=(steps.length+2)*rowH+8;
  let run = b.patPrior;
  const vals=[b.patPrior]; steps.forEach(s=>{run+=s.v; vals.push(run);});
  const lo=Math.min(0,...vals), hi=Math.max(...vals);
  const x = v => padL + ((v-lo)/(hi-lo||1))*(W-padL-padR);
  let y=4, out="";
  const bar=(label,x1,x2,cls,txt)=>{
    const l=Math.min(x1,x2), w=Math.max(1.5,Math.abs(x2-x1));
    out+=`<text x="${padL-7}" y="${y+13}" text-anchor="end" font-size="10.5"
      fill="var(--muted)">${esc(label)}</text>
      <rect x="${l}" y="${y+4}" width="${w}" height="12" rx="1.5" fill="var(--${cls})"/>
      <text x="${W-padR+6}" y="${y+13}" font-size="10.5" font-family="var(--mono)"
      fill="var(--ink)">${txt}</text>`;
    y+=rowH;
  };
  bar(DATA.quarterPrior+" PAT", x(0), x(b.patPrior), "navy", cr(b.patPrior));
  run=b.patPrior;
  steps.forEach(s=>{ const a=run; run+=s.v; bar(s.label, x(a), x(run), s.v>=0?"pos":"neg",
    (s.v>=0?"+":"−")+cr(Math.abs(s.v)).replace("₹","₹")); });
  bar(DATA.quarterCurrent+" PAT", x(0), x(b.patCurrent), "navy", cr(b.patCurrent));
  return `<svg class="walk" viewBox="0 0 ${W} ${H}" role="img"
    aria-label="Profit walk for ${esc(b.bank)}">${out}</svg>`;
}

function ratioBlock(b){
  const row=(k,label,a,bv,d,unit)=>{
    if(a==null && bv==null) return `<dt>${label}</dt><dd class="na">not disclosed</dd>`;
    return `<dt>${label}</dt><dd>${a==null?"—":a.toFixed(2)+unit} → ${bv==null?"—":bv.toFixed(2)+unit}
      ${d==null?"":`<span class="${sign(d)}"> ${bps(d)}</span>`}</dd>`;
  };
  return `<dl class="kv">
    ${row("nim","Net interest margin",b.nim[0],b.nim[1],b.nim[2],"%")}
    ${row("gnpa","Gross NPA",b.gnpa[0],b.gnpa[1],b.gnpa[2],"%")}
    ${row("cc","Credit cost",b.creditCost[0],b.creditCost[1],b.creditCost[2],"%")}
  </dl>`;
}

function select(i){
  DATA.banks.forEach((_,j)=>{
    const tr=$(`#attrib tr[data-i="${j}"]`); if(tr) tr.setAttribute("aria-selected", j===i);
  });
  const b=DATA.banks[i];
  const derived = b.niiSource==="derived"
    ? `<p class="note" style="margin:0 0 9px">NII is <b>derived</b> here as interest earned less
       interest expended — this filing prints no NII line — so it is excluded from the
       arithmetic tie-out.</p>` : "";
  $("#detail").innerHTML = `
    <h3>${esc(b.bank)}</h3>
    <p class="who">Profit walk, ${esc(DATA.quarterPrior)} → ${esc(DATA.quarterCurrent)}, ₹ Crore</p>
    ${waterfall(b)}
    ${derived}
    ${ratioBlock(b)}
    ${b.creditCostDef?`<p class="note" style="margin:-4px 0 9px">Credit cost defined as
      <b>${esc(b.creditCostDef)}</b> — not comparable with the other banks' levels.</p>`:""}
    ${b.advances[0]!=null?`<dl class="kv"><dt>Advances (${esc(b.advancesBasis||"")})</dt>
      <dd>${cr(b.advances[0])} → ${cr(b.advances[1])}
      <span class="${sign(b.advances[2])}"> ${pct(b.advances[2])}</span></dd></dl>`:""}
    <div class="cite"><b>${esc(DATA.quarterPrior)} source</b>${esc(b.sourcePrior||"—")}</div>
    <div class="cite"><b>${esc(DATA.quarterCurrent)} source</b>${esc(b.sourceCurrent||"—")}</div>`;
}

function ratiosTable(){
  const head=`<thead><tr><th>Bank</th><th>NII growth</th><th>NIM change</th>
    <th>Gross NPA</th><th>Gross NPA change</th><th>Credit cost change</th></tr></thead>`;
  const cell=v=>v==null?`<td class="na">not disclosed</td>`
    :`<td class="num ${sign(v)}">${bps(v)}</td>`;
  const rows=DATA.banks.map(b=>`<tr>
    <td>${esc(b.bank)}</td>
    <td class="num ${sign(b.niiGrowth)}">${pct(b.niiGrowth)}${b.niiSource==="derived"
      ?' <span class="na" title="derived, not printed by the bank">derived</span>':""}</td>
    ${cell(b.nim[2])}
    <td class="num">${b.gnpa[1]==null?"—":b.gnpa[1].toFixed(2)+"%"}</td>
    ${cell(b.gnpa[2])}
    ${cell(b.creditCost[2])}</tr>`).join("");
  $("#ratios").innerHTML=head+`<tbody>${rows}</tbody>`;
}

function checks(){
  const groups={};
  DATA.checks.forEach(c=>{(groups[c.check] ||= []).push(c);});
  $("#strip").innerHTML = Object.entries(groups).map(([name,cs])=>{
    const run=cs.filter(c=>c.passed!==null), pass=run.filter(c=>c.passed).length;
    const na=cs.length-run.length;
    return `<span class="chip"><span class="dot ${pass===run.length?"ok":"na"}"></span>
      ${esc(name)} <b>${pass}/${run.length}</b>${na?` <span class="na">+${na} n/a</span>`:""}</span>`;
  }).join("");
  $("#checks").innerHTML = Object.entries(groups).map(([name,cs])=>{
    const run=cs.filter(c=>c.passed!==null), pass=run.filter(c=>c.passed).length;
    return `<div class="ck"><h4><span class="dot ${pass===run.length?"ok":"na"}"></span>
      ${esc(name)} — ${pass}/${run.length} passed</h4><ul>${cs.map(c=>
      `<li>${c.passed===null?'<span class="na">not applicable</span>':"✓"}
        ${esc(c.subject)}<br><span class="s">${esc(c.detail)}</span></li>`).join("")}</ul></div>`;
  }).join("");
}

attribTable(); ratiosTable(); checks(); select(0);
</script>
</body>
</html>
"""


def build() -> None:
    data = collect()
    html = (HTML
            .replace("__DATA__", json.dumps(data, allow_nan=False))
            .replace("__QP__", data["quarterPrior"])
            .replace("__QC__", data["quarterCurrent"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Written: {OUT}  ({len(html):,} bytes, no external requests)")


if __name__ == "__main__":
    build()
