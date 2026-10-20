# spectrum-cartographer

Open toolchain for **passive RF spectrum mapping** on commodity software-defined
radio hardware (HackRF One / HackRF Pro + OperaCake antenna switcher).

It sweeps bands, switches apertures, and turns recorded IQ into a readable map of
who is transmitting where — then flags the **residual**: emitters that don't match
a known-signal baseline. The research focus is resilient, low-power spectrum
awareness that still produces a usable picture without GPS or an always-on link.

Everything here is **receive-only** and research-oriented.

## Why

Most spectrum tools assume a quiet band, a workstation, and a network. This project
asks how far passive, prior-informed sensing can be pushed on a strict size, weight,
and power budget: a single low-cost radio, a switch, and an embedded-class processor.

## Method

```
capture  ->  noise-floor estimate  ->  emitter detection  ->  compare to baseline  ->  flag residual
```

1. **Capture** — step across a band plan, recording short IQ dwells per step
   (`tools/capture.py`). OperaCake switches antenna/band per step or on a timer.
2. **Map** — compute a power spectrogram / occupancy heatmap from the IQ
   (`tools/spectrum_map.py`).
3. **Baseline** — build a reference of expected occupancy from quiet-time captures.
4. **Residual** — compare a new capture to the baseline and surface only what's new
   or unexpected (`tools/detect_residual.py`).

See `docs/method.md` for the concept-level write-up.

## Hardware

- HackRF One or HackRF Pro (verify the Pro's exact tuning/sample specs on the
  Great Scott Gadgets page before relying on them).
- OperaCake antenna switcher (1 MHz – 4 GHz; 1x8, or paired 1x4).
- A host running Linux with the `hackrf` tools and SoapySDR.

## Quickstart

```bash
# deps (example)
pip install numpy scipy matplotlib SoapySDR

# capture a band sweep to IQ
python tools/capture.py --config opera_cake/sweep_profile.conf --out examples/captures/

# render an occupancy heatmap from a capture
python tools/spectrum_map.py examples/captures/<file>.cf32 --rate 20e6 --center 2.4e9

# compare a capture against a saved baseline
python tools/detect_residual.py --baseline baseline.npz --capture examples/captures/<file>.cf32
```

## Status

Early research scaffold. Flowgraphs and capture paths are being validated on
hardware. Issues and PRs welcome.

## License

GPLv3 — see `LICENSE`.
