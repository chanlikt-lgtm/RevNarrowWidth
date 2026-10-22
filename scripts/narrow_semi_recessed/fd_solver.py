"""
General finite-difference Laplace solver for the field-oxide BVP (Eq. 6 for
Case I, and the analogous Case II problem with lateral spreading along y=0),
used as an independently-verified ground truth for Phi_swl / A,B (Case I) and
Phi_swl+Phi_lat / A',B' (Case II) -- since the closed-form Fourier series
(Eq. 11 / Eq. 17) could not be reconciled with this numerical solve (see
verify_series.py) after fixing the one dimensional inconsistency caught
earlier, and further image-based re-verification of the source PDF was not
available in-session.

Case II's x=0 boundary h(y) was NOT re-confirmed from the paper text (only
Case I's Eq. 6 and the modified y=0 condition, Eq. 14/15, were). It is
inferred here by physical continuity: at the Case I/II boundary (td=t1,
Wc=0), Case I's h(y) reduces to phi_s*(1-(t1-y)/td)^2 for 0<y<t1 (since the
t1-td<y<t1-td piece vanishes), so Case II's h(y) is taken to be the same
quadratic form over 0<=y<t1 with no zero-piece (since t1-td<0 has no meaning
inside the physical domain y>=0). This choice is validated below by checking
that A,B (Case I) and A',B' (Case II) agree in the Wc->0 limit -- a
self-consistency check independent of any new image reads.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from model import eps_ox


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
    Wc = td - t1
    Xmax = Xmax_factor * tf
    x = np.linspace(0, Xmax, Nx)
    y = np.linspace(0, tf, Ny)
    dx = x[1] - x[0]
    dy = y[1] - y[0]

    ni, nj = Nx - 2, Ny - 2

    def idx(i, j):
        return i * nj + j

    N = ni * nj
    Amat = sp.lil_matrix((N, N))
    b = np.zeros(N)

    cx = 1.0 / dx**2
    cy = 1.0 / dy**2
    cdiag = -2 * cx - 2 * cy

    if case == "I":
        left_bc = h_case1(y, Vg, phis, tg, t1, td)
        bottom_bc_arr = np.zeros_like(x)
    else:
        left_bc = h_case2(y, Vg, phis, tg, t1, td)
        bottom_bc_arr = f_case2(x, phis, t1, td, Wc)
    right_bc = Vg * y / tf
    top_bc = Vg

    for i in range(ni):
        for j in range(nj):
            k = idx(i, j)
            Amat[k, k] = cdiag
            if i - 1 >= 0:
                Amat[k, idx(i - 1, j)] += cx
            else:
                b[k] -= cx * left_bc[j + 1]
            if i + 1 < ni:
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
    phi = phi_flat.reshape(ni, nj)

    dphidx_x0 = (phi[0, :] - left_bc[1:-1]) / dx
    y_interior = y[1:-1]
    phi_swl = -eps_ox * np.trapz(dphidx_x0, y_interior)

    if case == "II":
        dphidy_y0 = (phi[:, 0] - bottom_bc_arr[1:-1]) / dy
        x_interior = x[1:-1]
        # Phi_lat integrates only over 0<x<Wc (Eq. 14), not the full domain
        m = x_interior < Wc
        phi_lat = -eps_ox * np.trapz(dphidy_y0[m], x_interior[m])
        return phi_swl, phi_lat
    return phi_swl, None


def AB_case1_fd(tf, tg, t1, td, **kw):
    p1, _ = solve_bvp(tf, tg, t1, td, 1.0, 0.0, "I", **kw)
    p2, _ = solve_bvp(tf, tg, t1, td, 0.0, 1.0, "I", **kw)
    A = p1 / eps_ox
    B = p2 / eps_ox + A
    return A, B


def AB_case2_fd(tf, tg, t1, td, **kw):
    """A', B' defined by Phi_swl + Phi_lat = eps_ox[(Vg-phis)A' + phis B']"""
    swl1, lat1 = solve_bvp(tf, tg, t1, td, 1.0, 0.0, "II", **kw)
    swl2, lat2 = solve_bvp(tf, tg, t1, td, 0.0, 1.0, "II", **kw)
    tot1 = (swl1 + lat1) / eps_ox
    tot2 = (swl2 + lat2) / eps_ox
    Ap = tot1
    Bp = tot2 + Ap
    return Ap, Bp


if __name__ == "__main__":
    tf, tg, t1 = 0.7e-6, 0.015e-6, 0.5e-6

    print("Continuity check at the Case I / Case II boundary (td -> t1):")
    for eps in [0.05e-6, 0.01e-6, 0.002e-6]:
        A1, B1 = AB_case1_fd(tf, tg, t1, t1 - eps, Nx=500, Ny=500)
        A2, B2 = AB_case2_fd(tf, tg, t1, t1 + eps, Nx=500, Ny=500)
        print(f"  |td-t1|={eps*1e9:5.1f} nm   "
              f"Case I: A={A1:.5f} B={B1:.5f}    "
              f"Case II: A'={A2:.5f} B'={B2:.5f}")
