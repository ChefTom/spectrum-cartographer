# flowgraphs

GNU Radio Companion (`.grc`) flowgraphs for capture and live display.

For reproducibility the capture path is also provided as a plain Python script
(`tools/capture.py`) that uses SoapySDR, so you don't need GRC to use the project.

Planned flowgraphs:
- `sweep_capture.grc` — HackRF source -> throttle/settle -> file sink, driven by
  the band plan in `opera_cake/sweep_profile.conf`.
- `live_waterfall.grc` — HackRF source -> QT GUI frequency/ waterfall sink for
  real-time viewing.

Keep flowgraphs receive-only. Do not add transmit blocks.
