"""Signal models for the physical-layer chapters (numpy only, computed when a scene is built).

Nothing here is a 10BASE-T1L implementation; these are small, honest models that make the
waveforms on screen behave like the real thing:

* cable: insertion loss IL(f) = k1*sqrt(f) + k2*f [dB, f in MHz], scaled to 25.6 dB at 3.75 MHz
  for 1 km, with the minimum phase that belongs to that magnitude (real-cepstrum method), so the
  impulse response is causal and has the long skin-effect tail;
* PAM-3 symbols at 7.5 MBd, an illustrative DC-balanced 4B3T code, the 1 + x^13 + x^33 scrambler;
* LMS echo canceller, FFE/DFE equaliser, second-order timing loop.
"""

from __future__ import annotations

import numpy as np

BAUD = 7.5e6
T_SYM = 1 / BAUD
K_SKIN, K_DIEL = 11.5, 0.9          # dB per km at 1 MHz for the sqrt(f) and f terms


def il_db(f_mhz, km=1.0):
    f = np.abs(np.asarray(f_mhz, dtype=float))
    return km * (K_SKIN * np.sqrt(f) + K_DIEL * f)


def _min_phase(mag):
    """Minimum-phase impulse response for a magnitude sampled on a full FFT grid."""
    n = len(mag)
    cep = np.fft.ifft(np.log(np.maximum(mag, 1e-12))).real
    fold = np.zeros(n)
    fold[0] = cep[0]
    fold[1:n // 2] = 2 * cep[1:n // 2]
    fold[n // 2] = cep[n // 2]
    return np.fft.ifft(np.exp(np.fft.fft(fold))).real


def cable_ir(osr=32, km=1.0, n_sym=256):
    """Impulse response of ``km`` of cable sampled at osr samples per symbol (unit DC gain)."""
    n = osr * n_sym
    f = np.fft.fftfreq(n, T_SYM / osr) / 1e6
    h = _min_phase(10 ** (-il_db(f, km) / 20))
    return h


def symbol_response(osr=32, km=1.0, n_sym=256):
    """Response to one rectangular symbol of unit height (sum over a symbol of the impulse response)."""
    h = cable_ir(osr, km, n_sym)
    p = np.convolve(h, np.ones(osr))[: len(h)]
    return p


def received(symbols, p, osr=32):
    """Superposition of shifted symbol responses: r(t) = sum_k a_k p(t - kT)."""
    x = np.zeros(len(symbols) * osr)
    x[::osr] = symbols
    return np.convolve(x, p)[: len(x)]


def rng_symbols(n, seed=1):
    return np.random.default_rng(seed).integers(-1, 2, n).astype(float)


# ---------------------------------------------------------------- equalisation
def design_equaliser(r_sym, a, n_ff=10, pre=3, n_fb=0, delay=None):
    """Least-squares (MMSE) FFE (+ optional DFE) for symbol-spaced samples r_sym of symbols a.

    Returns (c, b, d): y_n = sum_k c_k r_{n+pre-k} - sum_j b_j a_{n-d-j}, estimating a_{n-d}."""
    d = pre if delay is None else delay
    n = len(r_sym)
    rows, target = [], []
    for i in range(n_ff + n_fb + 10, n - n_ff - 2):
        ff = r_sym[i + pre - np.arange(n_ff)]
        fb = -a[i - d - 1 - np.arange(n_fb)] if n_fb else np.zeros(0)
        rows.append(np.concatenate([ff, fb]))
        target.append(a[i - d])
    A, y = np.array(rows), np.array(target)
    w, *_ = np.linalg.lstsq(A, y, rcond=None)
    return w[:n_ff], w[n_ff:], d


def eye(y, osr, start, n_traces, offset=0, span=2):
    """Slices of a waveform, ``span`` symbols wide, one per symbol period."""
    out = []
    for i in range(n_traces):
        a = start + i * osr + offset
        out.append(y[a: a + span * osr + 1])
    return out


# ---------------------------------------------------------------- coding
_ZERO = [(1, 0, -1), (1, -1, 0), (0, 1, -1), (0, -1, 1), (-1, 1, 0), (-1, 0, 1), (0, 0, 0)]
_PLUS1 = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)]
_PLUS2 = [(1, 1, 0), (1, 0, 1), (0, 1, 1)]
TABLE = {}
for _nib in range(16):
    if _nib < 7:
        TABLE[_nib] = (_ZERO[_nib], _ZERO[_nib])
    elif _nib < 13:
        _p = _PLUS1[_nib - 7]
        TABLE[_nib] = (_p, tuple(-x for x in _p))
    else:
        _p = _PLUS2[_nib - 13]
        TABLE[_nib] = (_p, tuple(-x for x in _p))


def encode_4b3t(bits):
    """Illustrative DC-balanced 4B3T: pick the triplet whose sum pulls the running sum to zero."""
    rds, out = 0, []
    for i in range(0, len(bits) - 3, 4):
        nib = int("".join(str(int(b)) for b in bits[i:i + 4]), 2)
        pos, neg = TABLE[nib]
        code = pos if rds <= 0 else neg
        rds += sum(code)
        out.append(code)
    return out


def lfsr(n, taps=(13, 33), seed=0x1ABCDEF01):
    """Side-stream scrambler sequence s_n = s_{n-a} xor s_{n-b} (Fibonacci LFSR)."""
    a, b = taps
    state = [(seed >> i) & 1 for i in range(b)]   # state[0] = s_{n-1}, ..., state[b-1] = s_{n-b}
    out = []
    for _ in range(n):
        s = state[a - 1] ^ state[b - 1]
        out.append(s)
        state = [s] + state[:-1]
    return np.array(out, dtype=int)


def highpass(x, alpha):
    """First-order high-pass y[n] = alpha*(y[n-1] + x[n] - x[n-1]) (AC coupling)."""
    y = np.zeros_like(x, dtype=float)
    for i in range(1, len(x)):
        y[i] = alpha * (y[i - 1] + x[i] - x[i - 1])
    return y


def psd(x, fs, nfft=1024):
    """Averaged periodogram (Hann), one-sided, returns (f, S)."""
    w = np.hanning(nfft)
    segs = [x[i:i + nfft] * w for i in range(0, len(x) - nfft, nfft // 2)]
    S = np.mean([np.abs(np.fft.rfft(s)) ** 2 for s in segs], axis=0)
    f = np.fft.rfftfreq(nfft, 1 / fs)
    return f, S / S.max()


# ---------------------------------------------------------------- echo cancellation
def echo_path(n_taps=80):
    """Symbol-spaced echo impulse response: hybrid leakage, then small connector/far-end reflections."""
    g = np.zeros(n_taps)
    k = np.arange(8)
    g[:8] = 0.32 * np.exp(-k / 1.4) * np.cos(0.9 * k)       # leakage through the analog hybrid
    for pos, amp in ((22, 0.045), (23, 0.02), (53, -0.03), (54, -0.012), (75, 0.016), (76, 0.008)):
        g[pos] += amp                                           # reflections: 300 m, 700 m, far end
    return g


def lms_echo(n=24000, n_taps=80, far_amp=0.052, noise=0.002, seed=3, snapshots=(0, 300, 1200, 4000, 23999)):
    """Run an LMS echo canceller with a gear-shifted step size; returns weights snapshots and residual echo."""
    rng = np.random.default_rng(seed)
    a = rng.integers(-1, 2, n + n_taps).astype(float)
    b = rng.integers(-1, 2, n + n_taps).astype(float)
    g = echo_path(n_taps)
    w = np.zeros(n_taps)
    snaps, resid = {}, np.zeros(n)
    for i in range(n):
        x = a[i + n_taps - 1 - np.arange(n_taps)]
        echo = g @ x
        r = echo + far_amp * b[i + n_taps] + noise * rng.standard_normal()
        e = r - w @ x
        mu = 0.02 if i < 800 else (0.004 if i < 4000 else 0.0008)
        w += mu * e * x
        resid[i] = (g - w) @ x
        if i in snapshots:
            snaps[i] = w.copy()
    return g, snaps, resid


# ---------------------------------------------------------------- timing recovery
def timing_loop(n=400, kp=0.08, ki=0.004, offset=0.42, drift=0.0015):
    """Second-order (PI) loop tracking a sampling-phase error [symbols]; returns the phase error."""
    theta, integ = 0.0, 0.0
    err = np.zeros(n)
    tx = offset
    for i in range(n):
        tx += drift                    # frequency offset between the crystals
        e = tx - theta
        err[i] = e
        integ += ki * e
        theta += kp * e + integ
    return err


def lms_history(n=60000, n_taps=80, far_amp=0.052, noise=0.002, seed=3, n_snap=90):
    """LMS echo canceller with gear-shifted step size.

    Returns (g, iters, weights, res_db): true echo path, snapshot iterations (log-spaced), weights at those
    iterations, and the residual-echo power relative to the transmit power (dB, averaged around each snapshot)."""
    rng = np.random.default_rng(seed)
    a = rng.integers(-1, 2, n + n_taps).astype(float)
    b = rng.integers(-1, 2, n + n_taps).astype(float)
    g = echo_path(n_taps)
    w = np.zeros(n_taps)
    iters = np.unique(np.round(np.logspace(0, np.log10(n - 1), n_snap)).astype(int))
    snaps, resid = [], np.zeros(n)
    want = set(iters.tolist())
    for i in range(n):
        x = a[i + n_taps - 1 - np.arange(n_taps)]
        r = g @ x + far_amp * b[i + n_taps] + noise * rng.standard_normal()
        e = r - w @ x
        mu = 0.02 if i < 800 else (0.004 if i < 4000 else (0.0008 if i < 16000 else 0.00015))
        w += mu * e * x
        resid[i] = (g - w) @ x
        if i in want:
            snaps.append(w.copy())
    r2 = resid ** 2
    res_db = np.array([10 * np.log10(np.mean(r2[max(0, i - max(8, i // 4)): i + 1]) / (2 / 3) + 1e-12) for i in iters])
    res_db[0] = 10 * np.log10(np.sum(g ** 2))          # before adaptation: the raw echo
    return g, iters, np.array(snaps), res_db


# ---------------------------------------------------------------- equaliser demo
def apply_ffe(x, c, pre, osr=32):
    y = np.zeros_like(x)
    for k, ck in enumerate(c):
        y += ck * np.roll(x, -(pre - k) * osr)
    return y


def rc_interp(samples, osr, phase, length, beta=0.5, span=5):
    """Smooth display waveform through symbol-spaced samples (raised-cosine interpolation):
    sample n lands at index n*osr + phase."""
    t = np.arange(-span * osr, span * osr + 1) / osr
    den = 1 - (2 * beta * t) ** 2
    rc = np.sinc(t) * np.where(np.abs(den) < 1e-6, np.pi / 4, np.cos(np.pi * beta * t) / np.where(np.abs(den) < 1e-6, 1, den))
    x = np.zeros(length + 2 * span * osr + osr)
    idx = np.arange(len(samples)) * osr + phase + span * osr
    ok = idx < len(x)
    x[idx[ok]] = samples[ok]
    y = np.convolve(x, rc, mode="same")
    return y[span * osr: span * osr + length]


def equalised_eyes(OSR=32, n=5000, sigma=0.003, seed=9):
    """Raw received waveform, and the slicer input after a short FFE and after FFE + DFE.

    The equalised signals only exist at the sampling instants; for display they are drawn through those samples
    with raised-cosine interpolation."""
    p = symbol_response(OSR)
    kpk = int(np.argmax(p))
    ph = kpk % OSR
    a = rng_symbols(n, seed=seed)
    r = received(a, p, OSR)
    rn = r + sigma * np.random.default_rng(seed + 1).standard_normal(len(r))
    rs = rn[ph::OSR][:n]
    d0 = kpk // OSR
    raw = rn / p[kpk]
    c, _, d1 = design_equaliser(rs, a, n_ff=4, pre=1, n_fb=0, delay=d0 + 1)
    y1s = apply_ffe(rn, c, 1, OSR)[ph::OSR][:n]
    c2, b2, d2 = design_equaliser(rs, a, n_ff=4, pre=1, n_fb=60, delay=d0 + 1)
    y2s = apply_ffe(rn, c2, 1, OSR)[ph::OSR][:n]
    for j in range(len(b2)):
        idx = np.arange(n) - d2 - 1 - j
        ok = idx >= 0
        y2s[ok] -= b2[j] * a[idx[ok]]
    L = len(rn)
    return a, raw, (rc_interp(y1s, OSR, ph, L), d1), (rc_interp(y2s, OSR, ph, L), d2), ph
