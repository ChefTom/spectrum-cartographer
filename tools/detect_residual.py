#!/usr/bin/env python3
"""Flag residual emitters: compare a capture's occupancy to a saved baseline.

Receive-only. Builds or loads a per-bin baseline (median + MAD) and reports
frequency bins whose power exceeds the baseline by a threshold, grouped into
contiguous candidate emitters. The residual is activity the baseline does not
explain.

Build a baseline from quiet-time captures:
    python tools/detect_residual.py --build baseline.npz q1.cf32 q2.cf32 --rate 20e6

Score a new capture against it:
    python tools/detect_residual.py --baseline baseline.npz --capture new.cf32 --rate 20e6
"""
import argparse
import sys
import numpy as np


def psd(path, rate, nfft, dtype):
    if dtype == "cf32":
        raw = np.fromfile(path, dtype=np.float32)
        iq = raw[0::2] + 1j * raw[1::2]
    else:
        raw = np.fromfile(path, dtype=np.int8).astype(np.float32) / 127.0
        iq = raw[0::2] + 1j * raw[1::2]
    n = len(iq) // nfft
    if n == 0:
        sys.exit(f"{path}: shorter than one FFT frame")
    frames = iq[: n * nfft].reshape(n, nfft)
    win = np.hanning(nfft)
    spec = np.fft.fftshift(np.fft.fft(frames * win, axis=1), axes=1)
    p = 20 * np.log10(np.abs(spec) + 1e-12)
    return p.mean(axis=0)  # mean power per bin


def build_baseline(paths, rate, nfft, dtype, out):
    rows = np.vstack([psd(p, rate, nfft, dtype) for p in paths])
    med = np.median(rows, axis=0)
    mad = np.median(np.abs(rows - med), axis=0) + 1e-9
    np.savez(out, median=med, mad=mad, rate=rate, nfft=nfft)
    print(f"baseline from {len(paths)} capture(s) -> {out}")


def score(baseline, capture, rate, nfft, dtype, k):
    b = np.load(baseline)
    med, mad = b["median"], b["mad"]
    cur = psd(capture, rate, nfft, dtype)
    if cur.shape != med.shape:
        sys.exit("capture/baseline FFT size mismatch")
    z = (cur - med) / mad
    flagged = z > k
    # group contiguous flagged bins into candidate emitters
    groups, start = [], None
    for i, f in enumerate(flagged):
        if f and start is None:
            start = i
        elif not f and start is not None:
            groups.append((start, i - 1)); start = None
    if start is not None:
        groups.append((start, len(flagged) - 1))

    half = rate / 2
    print(f"{len(groups)} candidate residual emitter(s) (k={k}):")
    for a, c in groups:
        fa = (-half + (a / nfft) * rate) / 1e6
        fc = (-half + (c / nfft) * rate) / 1e6
        peak = z[a:c + 1].max()
        print(f"  {fa:+8.3f} .. {fc:+8.3f} MHz (offset from center)  peak z={peak:4.1f}")


def main():
    ap = argparse.ArgumentParser(description="residual emitter detector")
    ap.add_argument("--build", metavar="OUT")
    ap.add_argument("captures", nargs="*")
    ap.add_argument("--baseline")
    ap.add_argument("--capture")
    ap.add_argument("--rate", type=float, required=True)
    ap.add_argument("--nfft", type=int, default=1024)
    ap.add_argument("--dtype", choices=["cf32", "cs8"], default="cf32")
    ap.add_argument("-k", type=float, default=6.0, help="threshold in MADs")
    args = ap.parse_args()

    if args.build:
        if not args.captures:
            sys.exit("--build needs one or more quiet-time captures")
        build_baseline(args.captures, args.rate, args.nfft, args.dtype, args.build)
    elif args.baseline and args.capture:
        score(args.baseline, args.capture, args.rate, args.nfft, args.dtype, args.k)
    else:
        ap.error("either --build OUT captures..., or --baseline B --capture C")


if __name__ == "__main__":
    main()
