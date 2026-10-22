"""
Model: Li, Hong, Cheng & Chan, "The Narrow-Channel Effect in MOSFET's
with Semi-Recessed Oxide Structures," IEEE Trans. Electron Devices,
vol. 37, no. 3, pp. 692-701, March 1990.

Conformal-mapping solution of Laplace's equation in the field-oxide
sidewall/lateral region (Figs. 2-4), yielding a closed-form threshold
voltage Vth(W) for an n-channel MOSFET with semi-recessed field
isolation. Two regimes depending on whether the channel depletion
depth td is smaller (Case I) or larger (Case II) than the recess
depth t1:

  Case I  (td < t1): depletion stays within the sidewall (Fig. 2/3).
  Case II (td > t1): depletion spills laterally under the field oxide,
                      forming a quarter-circular "wing" of radius
                      Wc = td - t1 (Fig. 4).

Fully-recessed and nonrecessed structures are obtained from the SAME
formulas by setting t1 = tf - tg (fully recessed, Fig. 1(b)) or
t1 -> 0 (nonrecessed, Fig. 1(c)) -- stated explicitly in the paper
(Sec. III-B/III-C) rather than via a separate model.

All lengths in meters, charges in C/m^2, doping in m^-3, SI units
throughout. Interface charge densities rho_g (gate), rho_s (sidewall),
rho_f (lateral-under-field-oxide) are assumed common (= Qss) when the
paper sweeps "fixed oxide charge."
"""

import numpy as np

# ---- physical constants (SI) ------------------------------------------------
q = 1.602e-19          # C
eps0 = 8.854e-12       # F/m
eps_ox = 3.9 * eps0    # F/m
eps_si = 11.7 * eps0   # F/m
kT_q = 0.02585         # V, room temperature
ni = 1.5e16            # m^-3  (1.5e10 cm^-3)


def phi_f(Na):
    """Bulk Fermi potential (V)."""
    return kT_q * np.log(Na / ni)


def td_depth(Na, Vbg, phif=None):
    """Depletion depth under the gate (Eq. 1), m."""
    if phif is None:
        phif = phi_f(Na)
    return np.sqrt(2 * eps_si * (2 * phif + abs(Vbg)) / (q * Na))


# ---- Case I: td < t1 (Eq. 11) ------------------------------------------------
def series_AB_case1(tf, tg, t1, td, nmax=6000):
    n = np.arange(1, nmax + 1, dtype=np.float64)
    k = np.pi / tf

    s_half_td = np.sin(0.5 * n * k * td)
    s_half_tg = np.sin(0.5 * n * k * tg)
    s_ref = np.sin(n * k * (t1 - td / 2))
    c_mid = np.cos(n * k * (t1 + tg / 2))

    A = (8 / (np.pi * k * tg)) * np.sum(s_half_td * s_half_tg * s_ref * c_mid / n**2)

    s_t1 = np.sin(n * k * t1)
    term1 = np.sum(s_ref * s_half_td * s_t1 / n**2)
    term2 = np.sum((s_ref**2) * (s_half_td**2) / n**3)
    B = (8 / (np.pi * k * td)) * term1 - (16 / (np.pi * k**2 * td**2)) * term2

    return A, B


# ---- Case II: td > t1 (Eq. 17) -----------------------------------------------
def series_AB_case2(tf, tg, t1, td, nmax=6000):
    Wc = td - t1
    k = np.pi / tf
    n = np.arange(1, nmax + 1, dtype=np.float64)

    e1 = np.exp(-n * k * Wc)
    cos_t1 = np.cos(n * k * t1)
    s_half_tg = np.sin(0.5 * n * k * tg)
    c_mid = np.cos(n * k * (t1 + tg / 2))

    Aprime = -Wc / tf + (4 / (np.pi * k * tg)) * np.sum(
        (e1 - cos_t1) * s_half_tg * c_mid / n**2
    )

    sin_t1 = np.sin(n * k * t1)
    term1 = np.sum((e1 - cos_t1) * sin_t1 / n**2)
    term2 = np.sum(
        (2 * e1 * cos_t1 - cos_t1**2 - 0.5 * (1 + np.exp(-2 * n * k * Wc))) / n**3
    )

    Bprime = (
        (2 * Wc / (np.pi * td**2)) * (k * t1**2 - (k * td + np.pi) * t1 + np.pi * tf / 3)
        + 2 * Wc**3 / (3 * tf * td**2)
        + (4 / (np.pi * k * td)) * term1
        + (4 / (np.pi * k**2 * td**2)) * term2
    )

    return Aprime, Bprime


def select_case(Na, Vbg, t1):
    """Returns ('I' or 'II', td)."""
    td = td_depth(Na, Vbg)
    return ("I" if td < t1 else "II"), td


# ---- IMPORTANT: series vs. FD verification ----------------------------------
# The Eq.(11)/(17) closed-form series above (series_AB_case1/2) were
# transcribed from high-resolution crops of the source PDF and cross-checked
# three times against the printed page. However, an independent finite-
# difference solve of the ACTUAL boundary-value problem (Eq. 6 for Case I,
# Eq. 14/15 for Case II; see fd_solver.py) does NOT reproduce these series
# values, even after fixing a confirmed dimensional inconsistency in A's
# prefactor. The FD solver itself was validated two independent ways that do
# NOT depend on Eq. (11)/(17) at all:
#   1. Case I converges to a hand-derived closed-form sharp-step limit
#      (td,tg -> 0) as those parameters shrink (verify_series.py).
#   2. Case I and Case II FD solutions agree with each other in the limit
#      td -> t1 (Wc -> 0), where the two BVPs coincide (fd_solver.py).
# Given this, the FD solve is used as the verified ground truth for A,B
# (Case I) and A',B' (Case II) throughout this reproduction; the series
# functions are kept only for reference/inspection, not for the figures.
from functools import lru_cache
import fd_solver as _fd


@lru_cache(maxsize=None)
def _ab_fd_cached(tf, tg, t1, td, case, N):
    if case == "I":
        return _fd.AB_case1_fd(tf, tg, t1, td, Nx=N, Ny=N)
    return _fd.AB_case2_fd(tf, tg, t1, td, Nx=N, Ny=N)


def ab_fd(tf, tg, t1, Na, Vbg, N=300):
    """(case, td, A, B) using the FD-verified BVP solve, cached per design point."""
    case, td = select_case(Na, Vbg, t1)
    A, B = _ab_fd_cached(tf, tg, t1, td, case, N)
    return case, td, A, B


def vth(W, tf, tg, t1, Na, Vbg, rho_s=0.0, rho_f=0.0, rho_g=0.0, N=300):
    """
    Threshold voltage (Eq. 12/13 form for Case I, Eq. 18/19 form for Case
    II), with A,B (or A',B') from the FD-verified BVP solve (see note
    above) rather than the still-unreconciled closed-form series.
    phi_ms is left out (W-independent constant); include separately if
    an absolute Vth is needed. rho_g does not affect Vth(W)-Vth(wide)
    since it only ever enters the W-independent part of Q'.
    """
    phif = phi_f(Na)
    case, td, A, B = ab_fd(tf, tg, t1, Na, Vbg, N)
    Cox = eps_ox / tg
    a = 2 * tg * (B - A)
    b = -2 * tg * A

    if case == "I":
        Qp = q * Na * td - rho_g - 2 * rho_s * (td / W)
    else:
        Wc = td - t1
        Qp = (
            q * Na * (td + (np.pi / 2) * (Wc**2 / W))
            - rho_g
            - 2 * rho_s * (t1 / W)
            - 2 * rho_f * (Wc / W)
        )

    return 2 * phif * (1 + a / W) / (1 + b / W) + (Qp / Cox) * (1 / (1 + b / W))


def vth_wide(tf, tg, t1, Na, Vbg, rho_g=0.0, N=300):
    """Vth(W -> infinity): a/W, b/W, and the 1/W charge terms all vanish."""
    phif = phi_f(Na)
    case, td = select_case(Na, Vbg, t1)
    Cox = eps_ox / tg
    Qp_inf = q * Na * td - rho_g
    return 2 * phif + Qp_inf / Cox


def delta_vth(W, tf, tg, t1, Na, Vbg, rho_s=0.0, rho_f=0.0, N=300):
    """Vth(W) - Vth(wide), the quantity plotted in every figure of the paper."""
    return vth(W, tf, tg, t1, Na, Vbg, rho_s, rho_f, N=N) - vth_wide(
        tf, tg, t1, Na, Vbg, N=N
    )
