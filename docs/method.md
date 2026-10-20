# Method (concept level)

This describes the approach at a level meant to be reproducible, not a hardware
design. It is receive-only.

## 1. Capture
Walk a band plan as a list of center frequencies. At each step, let the front end
settle, then record a short IQ dwell. An antenna switcher (OperaCake) selects the
antenna/band appropriate to the step (frequency-keyed) or cycles antennas on a
timer. Dwell length trades time resolution against the weakest signal you can pull
out of the noise.

## 2. Occupancy map
For each dwell, estimate power spectral density (Welch), stack the dwells into a
time-frequency image, and render occupancy as a heatmap. This is the "map" — a
picture of energy vs. frequency vs. time across the swept span.

## 3. Baseline
Collect occupancy over a quiet or representative period and reduce it to a
per-bin reference: a central level and a spread (e.g. median and MAD). This is the
"expected" spectrum for that place and band plan.

## 4. Residual
Compare a new capture to the baseline per bin. Flag bins that exceed the baseline
by more than a set number of spreads, and group adjacent flagged bins into
candidate emitters. The residual is the set of signals that the baseline does not
explain — new, moved, or unexpected activity. This keeps the operator's attention
(and downstream compute) on the unknown, not on the already-known background.

## Why prior-informed
Scanning everything at full sensitivity is expensive in time and power. A baseline
prior lets the system spend its limited dwell budget where change is happening,
which is the core efficiency idea behind the project.
