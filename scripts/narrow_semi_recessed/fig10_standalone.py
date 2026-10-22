"""
STANDALONE reproduction of Fig. 10 (Na sweep, fully-recessed structure)
from Li, Hong, Cheng & Chan, "The Narrow-Channel Effect in MOSFET's with
Semi-Recessed Oxide Structures," IEEE TED 37(3), pp. 692-701, 1990.

Self-contained: no imports from model.py / fd_solver.py. Includes the
full finite-difference (FD) BVP solver used as the verified ground truth
for the Case I / Case II series coefficients A, B, since the paper's own
closed-form Fourier series (Eq. 11/17) was found, during this reproduction,
to disagree with an independent FD solve of the same stated boundary-value
problem (root cause of that discrepancy not fully identified -- see the
long verification discussion this conversation covered for scripts/
narrow_semi_recessed/verify_series.py and greens_function_check.py, both
of which independently confirm the FD numbers used here).

Only external dependencies: numpy, scipy, matplotlib.
"""
from functools import lru_cache

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib.pyplot as plt

# ==============================================================================
# Physical constants (SI)
# ==============================================================================
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


def select_case(Na, Vbg, t1):
    """Returns ('I' or 'II', td). Case I: td<t1 (inverse narrow-width
    effect). Case II: td>t1 (conventional effect, lateral 'wing')."""
    td = td_depth(Na, Vbg)
    return ("I" if td < t1 else "II"), td


# ==============================================================================
# Finite-difference BVP solver (ground truth for A, B -- Eq. 6 boundary
# condition solved directly, bypassing the paper's closed-form series)
# ==============================================================================
def h_case1(y, Vg, phis, tg, t1, td):
    out = np.zeros_like(y)
    m1 = y > t1 + tg
    m2 = (y > t1) & (y <= t1 + tg)
    m3 = (y > t1 - td) & (y <= t1)
    out[m1] = Vg
    out[m2] = phis + (Vg - phis) / tg * (y[m2] - t1)
    out[m3] = phis * (1 - (t1 - y[m3]) / td) ** 2
    return out


def h_case2(y, Vg, phis, tg, t1, td):
    out = np.zeros_like(y)
    m1 = y > t1 + tg
    m2 = (y > t1) & (y <= t1 + tg)
    m3 = y <= t1
    out[m1] = Vg
    out[m2] = phis + (Vg - phis) / tg * (y[m2] - t1)
    out[m3] = phis * (1 - (t1 - y[m3]) / td) ** 2
    return out


def f_case2(x, phis, t1, td, Wc):
    out = np.zeros_like(x)
    m = x < Wc
    out[m] = phis * (1 - (t1 + x[m]) / td) ** 2
    return out


def solve_bvp(tf, tg, t1, td, Vg, phis, case, Xmax_factor=6, Nx=700, Ny=700):
    """Solve Laplace's eq. on x in [0,Xmax], y in [0,tf] with the Eq. 6
    boundary condition at x=0, via a 5-point finite-difference Laplacian
    and a sparse direct solve. Returns the sidewall flux Phi_swl (and,
    for Case II, the additional lateral flux Phi_lat under the 'wing')."""
    Wc = td - t1
    Xmax = Xmax_factor * tf
    x = np.linspace(0, Xmax, Nx)
    y = np.linspace(0, tf, Ny)
    dx = x[1] - x[0]
    dy = y[1] - y[0]

    ni_, nj = Nx - 2, Ny - 2

    def idx(i, j):
        return i * nj + j

    N = ni_ * nj
    Amat = sp.lil_matrix((N, N))
    b = np.zeros(N)

    cx = 1.0 / dx ** 2
    cy = 1.0 / dy ** 2
    cdiag = -2 * cx - 2 * cy

    if case == "I":
        left_bc = h_case1(y, Vg, phis, tg, t1, td)
        bottom_bc_arr = np.zeros_like(x)
    else:
        left_bc = h_case2(y, Vg, phis, tg, t1, td)
        bottom_bc_arr = f_case2(x, phis, t1, td, Wc)
    right_bc = Vg * y / tf
    top_bc = Vg

    for i in range(ni_):
        for j in range(nj):
            k = idx(i, j)
            Amat[k, k] = cdiag
            if i - 1 >= 0:
                Amat[k, idx(i - 1, j)] += cx
            else:
                b[k] -= cx * left_bc[j + 1]
            if i + 1 < ni_:
                Amat[k, idx(i + 1, j)] += cx
            else:
                b[k] -= cx * right_bc[j + 1]
            if j - 1 >= 0:
                Amat[k, idx(i, j - 1)] += cy
            else:
                b[k] -= cy * bottom_bc_arr[i + 1]
            if j + 1 < nj:
                Amat[k, idx(i, j + 1)] += cy
            else:
                b[k] -= cy * top_bc

    Amat = Amat.tocsr()
    phi_flat = spla.spsolve(Amat, b)
    phi = phi_flat.reshape(ni_, nj)

    dphidx_x0 = (phi[0, :] - left_bc[1:-1]) / dx
    y_interior = y[1:-1]
    phi_swl = -eps_ox * np.trapz(dphidx_x0, y_interior)

    if case == "II":
        dphidy_y0 = (phi[:, 0] - bottom_bc_arr[1:-1]) / dy
        x_interior = x[1:-1]
        m = x_interior < Wc  # Eq. 14: integrate only over the wing, 0<x<Wc
        phi_lat = -eps_ox * np.trapz(dphidy_y0[m], x_interior[m])
        return phi_swl, phi_lat
    return phi_swl, None


def AB_case1_fd(tf, tg, t1, td, **kw):
    """A, B (Case I) via two solves exploiting linearity in (Vg, phis)."""
    p1, _ = solve_bvp(tf, tg, t1, td, 1.0, 0.0, "I", **kw)
    p2, _ = solve_bvp(tf, tg, t1, td, 0.0, 1.0, "I", **kw)
    A = p1 / eps_ox
    B = p2 / eps_ox + A
    return A, B


def AB_case2_fd(tf, tg, t1, td, **kw):
    """A', B' (Case II): Phi_swl + Phi_lat = eps_ox[(Vg-phis)A' + phis*B']."""
    swl1, lat1 = solve_bvp(tf, tg, t1, td, 1.0, 0.0, "II", **kw)
    swl2, lat2 = solve_bvp(tf, tg, t1, td, 0.0, 1.0, "II", **kw)
    tot1 = (swl1 + lat1) / eps_ox
    tot2 = (swl2 + lat2) / eps_ox
    Ap = tot1
    Bp = tot2 + Ap
    return Ap, Bp


@lru_cache(maxsize=None)
def _ab_fd_cached(tf, tg, t1, td, case, N):
    """Cached since A,B (or A',B') don't depend on channel width W --
    reused across an entire W-sweep, making the FD approach tractable."""
    if case == "I":
        return AB_case1_fd(tf, tg, t1, td, Nx=N, Ny=N)
    return AB_case2_fd(tf, tg, t1, td, Nx=N, Ny=N)


def ab_fd(tf, tg, t1, Na, Vbg, N=300):
    """(case, td, A, B) using the FD-verified BVP solve."""
    case, td = select_case(Na, Vbg, t1)
    A, B = _ab_fd_cached(tf, tg, t1, td, case, N)
    return case, td, A, B


# ==============================================================================
# Threshold-voltage model (Eq. 12/13 form, Case I; Eq. 18/19 form, Case II)
# ==============================================================================
def vth(W, tf, tg, t1, Na, Vbg, rho_s=0.0, rho_f=0.0, rho_g=0.0, N=300):
    """phi_ms omitted (W-independent constant, cancels in delta_vth)."""
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
            q * Na * (td + (np.pi / 2) * (Wc ** 2 / W))
            - rho_g
            - 2 * rho_s * (t1 / W)
            - 2 * rho_f * (Wc / W)
        )
    return 2 * phif * (1 + a / W) / (1 + b / W) + (Qp / Cox) * (1 / (1 + b / W))


def vth_wide(tf, tg, t1, Na, Vbg, rho_g=0.0, N=300):
    """Vth(W -> infinity)."""
    phif = phi_f(Na)
    case, td = select_case(Na, Vbg, t1)
    Cox = eps_ox / tg
    Qp_inf = q * Na * td - rho_g
    return 2 * phif + Qp_inf / Cox


def delta_vth(W, tf, tg, t1, Na, Vbg, rho_s=0.0, rho_f=0.0, N=300):
    """Vth(W) - Vth(wide) -- the quantity plotted in every figure of the paper."""
    return vth(W, tf, tg, t1, Na, Vbg, rho_s, rho_f, N=N) - vth_wide(tf, tg, t1, Na, Vbg, N=N)


# ==============================================================================
# Fig. 10: Na sweep, fully-recessed structure (t1 = tf - tg, Sec. III-B)
# ==============================================================================
if __name__ == "__main__":
    OUT = r"E:\claude\RAG\reports"

    tf, tg = 0.7e-6, 0.015e-6
    t1_full = tf - tg          # fully recessed: 0.685 um

    W_um = np.linspace(0.05, 4.0, 400)
    W = W_um * 1e-6
    Vbg = 0.0
    na_list = (1e14, 1e15, 1e16, 1e17)   # cm^-3, read off the paper's legend

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for na_cm3 in na_list:
        Na = na_cm3 * 1e6  # cm^-3 -> m^-3
        case, td = select_case(Na, Vbg, t1_full)
        y = np.array([delta_vth(w, tf, tg, t1_full, Na, Vbg) for w in W])
        ax.plot(W_um, y, label=f"Na={na_cm3:.0e} cm-3 (Case {case})")
        print(f"Na={na_cm3:.0e} cm-3  ->  Case {case}, td={td*1e6:.4f} um")

    ax.set_xlabel("Channel width (um)")
    ax.set_ylabel("Vth - Vth(wide)  (V)")
    ax.set_title("Fig 10 repro: Na, fully recessed (t1=tf-tg)")
    ax.legend(fontsize=7)
    ax.axhline(0, color="k", lw=0.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/li1990_fig10_repro_standalone.png", dpi=150)
    print("Wrote", f"{OUT}/li1990_fig10_repro_standalone.png")
