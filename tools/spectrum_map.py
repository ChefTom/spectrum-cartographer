#!/usr/bin/env python3
#
#      _    ____ ____ _____ ___  ____
#     / \  / ___/ ___| ____/ _ \/ ___|
#    / _ \| |  | |  _|  _|| | | \___ \
#   / ___ \ |__| |_| | |__| |_| |___) |
#  /_/   \_\____\____|_____\___/|____/
#
#  spectrum-cartographer  --  passive RF spectrum mapping
#  ACGEOS Systems  |  info@ACGEOS.com
#  Licensed under GPLv3. Receive-only.
#
"""Render a power spectrogram / occupancy heatmap from a recorded IQ file.

Receive-only spectrum mapping. Reads interleaved complex samples and plots a
time-frequency power image. Supports float32 (.cf32/.cfile) and int8 (.cs8).

Example:
    python tools/spectrum_map.py capture.cf32 --rate 20e6 --center 2.4e9
"""
import argparse
import sys
import numpy as np


def read_iq(path, dtype):
    if dtype == "cf32":
        raw = np.fromfile(path, dtype=np.float32)
        iq = raw[0::2] + 1j * raw[1::2]
    elif dtype == "cs8":
        raw = np.fromfile(path, dtype=np.int8).astype(np.float32) / 127.0
        iq = raw[0::2] + 1j * raw[1::2]
    else:
        raise ValueError(f"unknown dtype {dtype}")
    return iq


def spectrogram(iq, nfft):
    n = len(iq) // nfft
    if n == 0:
        sys.exit("capture shorter than one FFT frame")
    frames = iq[: n * nfft].reshape(n, nfft)
    win = np.hanning(nfft)
    spec = np.fft.fftshift(np.fft.fft(frames * win, axis=1), axes=1)
    power = 20 * np.log10(np.abs(spec) + 1e-12)
    return power


def main():
    ap = argparse.ArgumentParser(description="IQ -> occupancy heatmap")
    ap.add_argument("iq_file")
    ap.add_argument("--rate", type=float, required=True, help="sample rate Hz")
    ap.add_argument("--center", type=float, default=0.0, help="center freq Hz")
    ap.add_argument("--nfft", type=int, default=1024)
    ap.add_argument("--dtype", choices=["cf32", "cs8"], default="cf32")
    ap.add_argument("--out", default=None, help="save PNG instead of showing")
    args = ap.parse_args()

    iq = read_iq(args.iq_file, args.dtype)
    power = spectrogram(iq, args.nfft)

    import matplotlib
    if args.out:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    f0 = (args.center - args.rate / 2) / 1e6
    f1 = (args.center + args.rate / 2) / 1e6
    t1 = len(iq) / args.rate

    plt.figure(figsize=(10, 6))
    plt.imshow(power, aspect="auto", origin="lower",
               extent=[f0, f1, 0, t1], cmap="viridis")
    plt.colorbar(label="power (dB, uncal)")
    plt.xlabel("frequency (MHz)")
    plt.ylabel("time (s)")
    plt.title("spectrum-cartographer :: occupancy")
    plt.tight_layout()
    if args.out:
        plt.savefig(args.out, dpi=120)
        print(f"wrote {args.out}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
