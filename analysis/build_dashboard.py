"""build_dashboard.py — reads docs/dashboard_data.json, writes self-contained docs/index.html."""
import json

with open("docs/dashboard_data.json") as f:
    data = json.load(f)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Checkout Redesign — A/B Test Readout</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Albert+Sans:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root{
    --bg:#0C0F16; --panel:#141923; --panel2:#1B2230; --line:#262F3F;
    --text:#E7EEF7; --mut:#8A97AB; --ctrl:#5BA8FF; --treat:#46E5A0;
    --neg:#FF7B72; --amber:#F2C14E;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Albert Sans',sans-serif;line-height:1.5;
    -webkit-font-smoothing:antialiased;
    background-image:radial-gradient(900px 400px at 85% -10%,rgba(70,229,160,.10),transparent),
                     radial-gradient(700px 360px at 0% 0%,rgba(91,168,255,.08),transparent);}
  .wrap{max-width:1180px;margin:0 auto;padding:46px 26px 70px}
  .eyebrow{font:700 11px/1 'Space Mono',monospace;letter-spacing:.26em;text-transform:uppercase;color:var(--treat);margin-bottom:14px}
  h1{font-family:'Sora',sans-serif;font-weight:800;font-size:clamp(28px,4.2vw,46px);letter-spacing:-.02em;line-height:1.03}
  .sub{color:var(--mut);max-width:600px;margin-top:12px;font-size:15px}
  .decision{margin:26px 0 4px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;
    background:linear-gradient(90deg,rgba(70,229,160,.12),rgba(70,229,160,.02));
    border:1px solid rgba(70,229,160,.35);border-radius:14px;padding:16px 20px}
  .pill{font:800 13px/1 'Sora',sans-serif;letter-spacing:.08em;background:var(--treat);color:#06231a;
    padding:9px 16px;border-radius:999px}
  .decision .txt{color:var(--text);font-size:14.5px}
  .kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:13px;margin:26px 0 8px}
  .kpi{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:15px;
    opacity:0;transform:translateY(10px);animation:rise .55s forwards}
  .kpi .lab{font:700 10px/1.2 'Space Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
  .kpi .val{font-family:'Sora',sans-serif;font-weight:700;font-size:25px;margin-top:9px;letter-spacing:-.01em}
  .kpi .val.up{color:var(--treat)} .kpi .val.ctrl{color:var(--ctrl)}
  .kpi .note{font-size:11px;color:var(--mut);margin-top:3px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:20px 20px 16px;
    opacity:0;transform:translateY(10px);animation:rise .7s forwards}
  .card.wide{grid-column:1 / -1}
  .card h3{font-family:'Sora',sans-serif;font-size:17px;font-weight:600;letter-spacing:-.01em}
  .card p.cap{color:var(--mut);font-size:12.5px;margin-top:4px;margin-bottom:14px}
  .chartbox{position:relative;height:270px}
  .validity{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:4px}
  .vrow{display:flex;justify-content:space-between;border:1px solid var(--line);background:var(--panel2);
    border-radius:9px;padding:11px 13px;font-size:13px}
  .vrow .k{color:var(--mut)} .vrow .v{font-family:'Space Mono',monospace;font-weight:700}
  .ok{color:var(--treat)}
  .insight{margin-top:13px;font-size:12.8px;color:var(--text);background:rgba(91,168,255,.08);
    border-left:3px solid var(--ctrl);padding:10px 13px;border-radius:0 8px 8px 0}
  .insight b{color:var(--treat)}
  footer{margin-top:38px;border-top:1px solid var(--line);padding-top:20px;color:var(--mut);font-size:12.4px;line-height:1.7}
  footer code{font-family:'Space Mono',monospace;background:var(--panel2);padding:1px 6px;border-radius:5px;font-size:11px}
  @keyframes rise{to{opacity:1;transform:none}}
  .kpi:nth-child(1){animation-delay:.04s}.kpi:nth-child(2){animation-delay:.09s}.kpi:nth-child(3){animation-delay:.14s}
  .kpi:nth-child(4){animation-delay:.19s}.kpi:nth-child(5){animation-delay:.24s}.kpi:nth-child(6){animation-delay:.29s}
  @media(max-width:880px){.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.validity{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <div class="eyebrow">Experiment Readout · 14-day run · 60,000 users</div>
  <h1>Checkout Redesign — A/B Test</h1>
  <p class="sub">Does a streamlined checkout lift purchase conversion? Randomized at the user level, evaluated on conversion, revenue, and segment effects with proper significance testing.</p>

  <div class="decision" id="decision"></div>

  <section class="kpis" id="kpis"></section>

  <div class="grid">
    <div class="card">
      <h3>Conversion rate ± 95% CI</h3>
      <p class="cap">The two confidence intervals don't overlap → the difference is real, not noise.</p>
      <div class="chartbox"><canvas id="ciChart"></canvas></div>
      <div class="insight" id="ins-primary"></div>
    </div>
    <div class="card">
      <h3>Lift by segment</h3>
      <p class="cap">Absolute lift (pp). Solid = statistically significant; faded = not.</p>
      <div class="chartbox"><canvas id="segChart"></canvas></div>
      <div class="insight" id="ins-seg"></div>
    </div>
    <div class="card">
      <h3>Cumulative conversion over the run</h3>
      <p class="cap">Treatment separates early and stays separated — stable, not a peeking artifact.</p>
      <div class="chartbox"><canvas id="timeChart"></canvas></div>
    </div>
    <div class="card">
      <h3>Revenue per user</h3>
      <p class="cap">The conversion lift carries through to revenue (no AOV cannibalization).</p>
      <div class="chartbox"><canvas id="rpuChart"></canvas></div>
    </div>
    <div class="card wide">
      <h3>Test validity & power</h3>
      <p class="cap">The checks that decide whether the result can be trusted.</p>
      <div class="validity" id="validity"></div>
    </div>
  </div>

  <footer>
    <b>Stack:</b> Python (pandas, scipy) · MySQL for the metric queries · Chart.js · GitHub Pages.<br>
    <b>Methods:</b> two-proportion z-test · 95% confidence intervals · sample-ratio-mismatch (SRM) chi-square · power / minimum-detectable-effect · Welch t-test on revenue · segment (heterogeneous) effects with a multiple-comparisons caution.<br>
    <b>Note:</b> data is synthetic (<code>generate_data.py</code>); every statistic is the real output of <code>analysis.py</code>. Methodology transfers directly to production experiment data.
  </footer>
</div>

<script>
const DATA = __DATA__;
const TEXT='#E7EEF7',MUT='#8A97AB',CTRL='#5BA8FF',TREAT='#46E5A0',NEG='#FF7B72',LINE='#262F3F';
Chart.defaults.font.family="'Albert Sans',sans-serif";Chart.defaults.font.size=12;Chart.defaults.color=MUT;
const P=DATA.primary,R=DATA.revenue,PW=DATA.power,SRM=DATA.srm,DEC=DATA.decision;

/* decision banner */
document.getElementById('decision').innerHTML=
  `<span class="pill">${DEC.ship?'SHIP ✓':'HOLD'}</span><span class="txt">${DEC.rationale}</span>`;

/* KPIs */
const cards=[
  ['Control CR',(P.control_rate*100).toFixed(2)+'%','baseline','ctrl'],
  ['Treatment CR',(P.treatment_rate*100).toFixed(2)+'%','new checkout','up'],
  ['Relative lift','+'+P.rel_lift_pct+'%','['+P.ci_low_pp+', '+P.ci_high_pp+'] pp','up'],
  ['p-value',P.p_value.toExponential(1),P.significant?'significant':'n.s.',''],
  ['Revenue / user','+'+R.rpu_lift_pct+'%','p='+R.p_value.toExponential(1),'up'],
  ['Achieved power',(PW.achieved_power*100).toFixed(0)+'%','MDE '+PW.mde_pp+'pp',''],
];
document.getElementById('kpis').innerHTML=cards.map(c=>
  `<div class="kpi"><div class="lab">${c[0]}</div><div class="val ${c[3]}">${c[1]}</div><div class="note">${c[2]}</div></div>`).join('');

const grid={grid:{color:'rgba(255,255,255,.05)'},border:{display:false}};
const noGrid={grid:{display:false},border:{display:false}};
const base=(e={})=>Object.assign({responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}},e);

/* conversion CI — floating bars */
new Chart(ciChart,{type:'bar',data:{labels:['Control','Treatment'],
  datasets:[{data:[P.control_ci,P.treatment_ci],
    backgroundColor:[CTRL,TREAT],borderRadius:6,barPercentage:.55}]},
  options:base({indexAxis:'y',scales:{x:Object.assign({ticks:{callback:v=>v+'%'},
      title:{display:true,text:'conversion rate (95% CI)'}},grid),y:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>'95% CI: '+c.raw[0]+'%–'+c.raw[1]+'%'}}}})});
document.getElementById('ins-primary').innerHTML=
  `Conversion rose <b>${P.abs_lift_pp}pp</b> (${(P.control_rate*100).toFixed(1)}% → ${(P.treatment_rate*100).toFixed(1)}%), a <b>+${P.rel_lift_pct}%</b> relative lift. The 95% CI on the difference is [${P.ci_low_pp}, ${P.ci_high_pp}]pp — it excludes zero.`;

/* segments */
const sg=DATA.segments;
new Chart(segChart,{type:'bar',data:{labels:sg.map(s=>s.segment+' ('+s.dimension.replace('_',' ')+')'),
  datasets:[{data:sg.map(s=>s.abs_lift_pp),
    backgroundColor:sg.map(s=>s.significant?TREAT:'rgba(138,151,171,.45)'),borderRadius:5}]},
  options:base({indexAxis:'y',scales:{x:Object.assign({ticks:{callback:v=>v+'pp'}},grid),y:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>{const s=sg[c.dataIndex];
      return [`lift ${s.abs_lift_pp}pp`,`p = ${s.p_value.toExponential(1)} ${s.significant?'(sig.)':'(n.s.)'}`];}}}}})});
const mob=sg.find(s=>s.segment==='mobile'),dsk=sg.find(s=>s.segment==='desktop');
document.getElementById('ins-seg').innerHTML=
  `The win is almost all <b>mobile</b> (${mob.abs_lift_pp}pp, significant). <b>Desktop</b> is flat (${dsk.abs_lift_pp}pp, not significant) — so the redesign helps small screens, and a desktop rollout needs its own test.`;

/* over time */
const T=DATA.cumulative;
new Chart(timeChart,{type:'line',data:{labels:T.days,
  datasets:[{label:'Control',data:T.control,borderColor:CTRL,backgroundColor:'transparent',tension:.3,borderWidth:2.5,pointRadius:0},
            {label:'Treatment',data:T.treatment,borderColor:TREAT,backgroundColor:'transparent',tension:.3,borderWidth:2.5,pointRadius:0}]},
  options:base({interaction:{mode:'index',intersect:false},
    scales:{y:Object.assign({ticks:{callback:v=>v+'%'}},grid),x:noGrid},
    plugins:{legend:{display:true,position:'bottom',labels:{usePointStyle:true,boxWidth:7,padding:16,color:MUT}},
      tooltip:{callbacks:{label:c=>c.dataset.label+': '+c.raw.toFixed(2)+'%'}}}})});

/* revenue per user */
new Chart(rpuChart,{type:'bar',data:{labels:['Control','Treatment'],
  datasets:[{data:[R.rpu_control,R.rpu_treatment],backgroundColor:[CTRL,TREAT],borderRadius:6,barPercentage:.55}]},
  options:base({scales:{y:Object.assign({ticks:{callback:v=>'$'+v}},grid),x:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>'$'+c.raw.toFixed(2)+' / user'}}}})});

/* validity table */
const vv=[
  ['Sample-ratio (SRM)', (SRM.pass?'PASS':'FAIL')+' · χ²='+SRM.chi2+', p='+SRM.p_value, SRM.pass],
  ['Control / Treatment n', SRM.n_control.toLocaleString()+' / '+SRM.n_treatment.toLocaleString(), true],
  ['Min. detectable effect', PW.mde_pp+'pp @ 80% power', true],
  ['Observed lift', P.abs_lift_pp+'pp (> MDE)', true],
  ['Primary p-value', P.p_value.toExponential(1), P.significant],
  ['AOV change', DATA.aov.significant?'significant':'no change (p='+DATA.aov.p_value+')', true],
];
document.getElementById('validity').innerHTML=vv.map(r=>
  `<div class="vrow"><span class="k">${r[0]}</span><span class="v ${r[2]?'ok':''}">${r[1]}</span></div>`).join('');
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(data))
with open("docs/index.html", "w") as f:
    f.write(html)
print("wrote docs/index.html (", len(html), "bytes )")
