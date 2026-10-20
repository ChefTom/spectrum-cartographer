#!/usr/bin/env python3
"""Stepped band-sweep IQ capture using SoapySDR (HackRF backend).

Receive-only. Reads an OperaCake frequency profile, walks its band steps,
tunes the radio, records a short IQ dwell per step to disk as float32.

OperaCake control itself is done via the Great Scott Gadgets `hackrf_operacake`
tool; this script prints the port it expects per step so you can drive the
switch in lockstep (or wire it to the frequency-follow mode of the tool).

Example:
    python tools/capture.py --config opera_cake/sweep_profile.conf \
        --rate 20e6 --dwell 0.05 --out examples/captures/
"""
import argparse
import os
import time
import numpy as np


def load_profile(path):
    steps = []
    with open(path) as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            lo, hi, port = line.split()
            steps.append((float(lo), float(hi), port))
    return steps


def centers(steps, rate):
    """One or more tuned centers to cover each band step at the given rate."""
    plan = []
    for lo, hi, port in steps:
        f = lo + rate / 2
        while f - rate / 2 < hi:
            plan.append((f, port))
            f += rate
    return plan


def main():
    ap = argparse.ArgumentParser(description="stepped sweep IQ capture")
    ap.add_argument("--config", required=True)
    ap.add_argument("--rate", type=float, default=20e6)
    ap.add_argument("--dwell", type=float, default=0.05, help="seconds per step")
    ap.add_argument("--gain", type=float, default=32.0)
    ap.add_argument("--out", default="examples/captures/")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan, do not touch hardware")
    args = ap.parse_args()

    steps = load_profile(args.config)
    plan = centers(steps, args.rate)
    print(f"{len(plan)} tuned step(s) from {len(steps)} band(s)")

    if args.dry_run:
        for f, port in plan:
            print(f"  {f/1e6:9.3f} MHz   port {port}")
        return

    import SoapySDR
    from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32

    sdr = SoapySDR.Device(dict(driver="hackrf"))
    sdr.setSampleRate(SOAPY_SDR_RX, 0, args.rate)
    sdr.setGain(SOAPY_SDR_RX, 0, args.gain)
    os.makedirs(args.out, exist_ok=True)
    nsamp = int(args.rate * args.dwell)

    for f, port in plan:
        print(f"tune {f/1e6:9.3f} MHz  (OperaCake port {port})")
        sdr.setFrequency(SOAPY_SDR_RX, 0, f)
        st = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        sdr.activateStream(st)
        buff = np.empty(nsamp, np.complex64)
        got = 0
        while got < nsamp:
            tmp = np.empty(min(65536, nsamp - got), np.complex64)
            sr = sdr.readStream(st, [tmp], len(tmp))
            if sr.ret > 0:
                buff[got:got + sr.ret] = tmp[:sr.ret]
                got += sr.ret
        sdr.deactivateStream(st)
        sdr.closeStream(st)
        inter = np.empty(2 * got, np.float32)
        inter[0::2] = buff[:got].real
        inter[1::2] = buff[:got].imag
        fn = os.path.join(args.out, f"cap_{int(f)}_{port}.cf32")
        inter.tofile(fn)
        print(f"  -> {fn} ({got} samples)")
        time.sleep(0.01)


if __name__ == "__main__":
    main()
