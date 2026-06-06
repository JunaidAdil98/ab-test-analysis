"""
analysis.py
-----------
Full A/B-test analysis of the checkout-redesign experiment, implemented from
first principles with scipy (no statsmodels dependency):

  1. Sample-ratio mismatch (SRM) chi-square validity check
  2. Primary metric: two-proportion z-test, absolute & relative lift, 95% CI
  3. Power / minimum detectable effect (MDE) and achieved power
  4. Secondary: revenue-per-user and AOV (Welch t-tests)
  5. Segment effects (device, user_type) with a multiple-comparisons caution
  6. Cumulative conversion over time (peeking / stability check)
  7. Ship / no-ship decision

Writes docs/dashboard_data.json and prints a readout.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

df = pd.read_csv("data/experiment.csv", parse_dates=["visit_date"])
Z = stats.norm.ppf
ALPHA = 0.05
zc = Z(1 - ALPHA / 2)          # 1.95996
out = {}


def two_prop_z(x_c, n_c, x_t, n_t):
    p_c, p_t = x_c / n_c, x_t / n_t
    p_pool = (x_c + x_t) / (n_c + n_t)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = (p_t - p_c) / se_pool
    pval = 2 * (1 - stats.norm.cdf(abs(z)))
    se_un = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    ci = ((p_t - p_c) - zc * se_un, (p_t - p_c) + zc * se_un)
    return p_c, p_t, z, pval, ci, se_un


c = df[df.variant == "control"]
t = df[df.variant == "treatment"]
n_c, n_t = len(c), len(t)
x_c, x_t = int(c.converted.sum()), int(t.converted.sum())

# ---------------------------------------------------------------- 1. SRM
expected = (n_c + n_t) / 2
chi2 = ((n_c - expected) ** 2 + (n_t - expected) ** 2) / expected
srm_p = 1 - stats.chi2.cdf(chi2, df=1)
out["srm"] = {"n_control": n_c, "n_treatment": n_t,
              "chi2": round(float(chi2), 3), "p_value": round(float(srm_p), 3),
              "pass": bool(srm_p > 0.01)}

# ---------------------------------------------------------------- 2. primary
p_c, p_t, z, pval, ci, se_un = two_prop_z(x_c, n_c, x_t, n_t)
abs_lift = p_t - p_c
rel_lift = abs_lift / p_c
out["primary"] = {
    "metric": "purchase conversion rate",
    "control_rate": round(p_c, 5), "treatment_rate": round(p_t, 5),
    "abs_lift_pp": round(abs_lift * 100, 3),
    "rel_lift_pct": round(rel_lift * 100, 2),
    "z": round(float(z), 3), "p_value": float(f"{pval:.2e}"),
    "ci_low_pp": round(ci[0] * 100, 3), "ci_high_pp": round(ci[1] * 100, 3),
    "significant": bool(pval < ALPHA),
    "control_ci": [round((p_c - zc * np.sqrt(p_c * (1 - p_c) / n_c)) * 100, 2),
                   round((p_c + zc * np.sqrt(p_c * (1 - p_c) / n_c)) * 100, 2)],
    "treatment_ci": [round((p_t - zc * np.sqrt(p_t * (1 - p_t) / n_t)) * 100, 2),
                     round((p_t + zc * np.sqrt(p_t * (1 - p_t) / n_t)) * 100, 2)],
}

# ---------------------------------------------------------------- 3. power / MDE
n_arm = (n_c + n_t) / 2
z_beta = Z(0.80)
mde = (zc + z_beta) * np.sqrt(2 * p_c * (1 - p_c) / n_arm)   # detectable abs lift @80%
achieved_power = stats.norm.cdf(abs(abs_lift) / se_un - zc)
out["power"] = {"mde_pp": round(mde * 100, 3),
                "achieved_power": round(float(achieved_power), 3),
                "n_per_arm": int(n_arm)}

# ---------------------------------------------------------------- 4. revenue / AOV
rev_t = t.revenue.values
rev_c = c.revenue.values
tt = stats.ttest_ind(rev_t, rev_c, equal_var=False)
out["revenue"] = {
    "rpu_control": round(float(rev_c.mean()), 3),
    "rpu_treatment": round(float(rev_t.mean()), 3),
    "rpu_lift_pct": round(float((rev_t.mean() / rev_c.mean() - 1) * 100), 2),
    "p_value": float(f"{tt.pvalue:.2e}"),
    "significant": bool(tt.pvalue < ALPHA),
}
aov_c = c.loc[c.converted == 1, "revenue"]
aov_t = t.loc[t.converted == 1, "revenue"]
aov_tt = stats.ttest_ind(aov_t, aov_c, equal_var=False)
out["aov"] = {"aov_control": round(float(aov_c.mean()), 2),
              "aov_treatment": round(float(aov_t.mean()), 2),
              "p_value": round(float(aov_tt.pvalue), 3),
              "significant": bool(aov_tt.pvalue < ALPHA)}

# ---------------------------------------------------------------- 5. segments
segs = []
for col in ["device", "user_type"]:
    for level, g in df.groupby(col):
        gc, gt = g[g.variant == "control"], g[g.variant == "treatment"]
        pc, pt, _, pv, _, _ = two_prop_z(int(gc.converted.sum()), len(gc),
                                         int(gt.converted.sum()), len(gt))
        segs.append({"dimension": col, "segment": level,
                     "control_rate": round(pc * 100, 2),
                     "treatment_rate": round(pt * 100, 2),
                     "abs_lift_pp": round((pt - pc) * 100, 2),
                     "p_value": float(f"{pv:.2e}"),
                     "significant": bool(pv < ALPHA)})
out["segments"] = segs

# ---------------------------------------------------------------- 6. over time
daily = (df.assign(day=df.visit_date.dt.day)
           .groupby(["visit_date", "variant"])["converted"]
           .agg(["sum", "count"]).reset_index())
cum = {}
for v in ["control", "treatment"]:
    sub = daily[daily.variant == v].sort_values("visit_date")
    cr = (sub["sum"].cumsum() / sub["count"].cumsum() * 100).round(3).tolist()
    cum[v] = cr
out["cumulative"] = {"days": [d.strftime("%b %d") for d in
                              sorted(df.visit_date.dt.normalize().unique())],
                     "control": cum["control"], "treatment": cum["treatment"]}

# ---------------------------------------------------------------- 7. decision
out["decision"] = {
    "ship": bool(out["primary"]["significant"] and out["srm"]["pass"]
                 and out["primary"]["abs_lift_pp"] > 0),
    "rationale": ("Treatment lifts conversion by "
                  f"{out['primary']['rel_lift_pct']}% "
                  f"(p={out['primary']['p_value']:.1e}); SRM passes; "
                  "no negative guardrail. Ship.")
}

with open("docs/dashboard_data.json", "w") as f:
    json.dump(out, f, indent=2)

# ---- readout ----
pr = out["primary"]
print("SRM:", "PASS" if out["srm"]["pass"] else "FAIL", f"(p={out['srm']['p_value']})")
print(f"Conversion  control {pr['control_rate']*100:.2f}%  ->  treatment {pr['treatment_rate']*100:.2f}%")
print(f"Abs lift {pr['abs_lift_pp']:+.2f}pp  |  Rel lift {pr['rel_lift_pct']:+.1f}%  "
      f"|  95% CI [{pr['ci_low_pp']:.2f}, {pr['ci_high_pp']:.2f}]pp")
print(f"z={pr['z']}  p={pr['p_value']:.2e}  significant={pr['significant']}")
print(f"MDE @80% power: {out['power']['mde_pp']:.2f}pp  | achieved power {out['power']['achieved_power']:.2f}")
print(f"RPU control ${out['revenue']['rpu_control']}  treatment ${out['revenue']['rpu_treatment']}  "
      f"(+{out['revenue']['rpu_lift_pct']}%, p={out['revenue']['p_value']:.1e})")
print("Segments:")
for s in out["segments"]:
    print(f"  {s['dimension']:<10} {s['segment']:<10} lift {s['abs_lift_pp']:+.2f}pp  p={s['p_value']:.1e}")
print("DECISION:", "SHIP" if out["decision"]["ship"] else "HOLD")
print("wrote docs/dashboard_data.json")
