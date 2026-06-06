"""
generate_data.py
----------------
Simulates a randomized online experiment: a checkout-flow redesign.

  Control   = existing checkout
  Treatment = streamlined checkout

Primary metric : purchase conversion rate
Secondary      : revenue per user (RPU), average order value (AOV)
Covariates     : device (mobile/desktop), user_type (new/returning)

A genuine, heterogeneous treatment effect is built in (larger lift on mobile)
so the analysis recovers real, segment-dependent signal. Synthetic data for a
portfolio demonstration -- NOT real traffic.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(2024)
N = 60000
START = pd.Timestamp("2025-03-01")

# assignment ~50/50 (tiny realistic wobble; checked later via SRM test)
group = RNG.choice(["control", "treatment"], size=N, p=[0.501, 0.499])
device = RNG.choice(["mobile", "desktop"], size=N, p=[0.62, 0.38])
user_type = RNG.choice(["new", "returning"], size=N, p=[0.45, 0.55])

# ---- baseline conversion probability (control) ----
p = np.full(N, 0.090)
p += np.where(device == "desktop", 0.045, 0.0)        # desktop converts better
p += np.where(user_type == "returning", 0.040, 0.0)   # returning convert better

# ---- treatment effect (heterogeneous: helps mobile + new users most) ----
te = np.zeros(N)
te += np.where((group == "treatment") & (device == "mobile"), 0.024, 0.0)
te += np.where((group == "treatment") & (device == "desktop"), 0.005, 0.0)
te += np.where((group == "treatment") & (user_type == "new"), 0.008, 0.0)
p_final = np.clip(p + te, 0.01, 0.95)

converted = (RNG.random(N) < p_final).astype(int)

# ---- order value for converters (lognormal); treatment ~ neutral on AOV ----
aov = np.where(converted == 1, RNG.lognormal(mean=4.2, sigma=0.5, size=N), 0.0)
revenue = np.round(converted * aov, 2)

visit_date = START + pd.to_timedelta(RNG.integers(0, 14, size=N), unit="D")

df = pd.DataFrame({
    "user_id": [f"U{1_000_000 + i}" for i in range(N)],
    "variant": group,
    "device": device,
    "user_type": user_type,
    "visit_date": visit_date.date,
    "converted": converted,
    "revenue": revenue,
})
df.to_csv("data/experiment.csv", index=False)

# quick console sanity check
g = df.groupby("variant")["converted"].agg(["mean", "count"])
print(df.shape)
print(g)
print("overall lift (pp):",
      round((g.loc["treatment", "mean"] - g.loc["control", "mean"]) * 100, 3))
