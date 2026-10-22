"""
Independent numerical check of the Case I series coefficients A, B (Eq. 11)
against a direct finite-difference solution of the actual 2-D boundary value
problem defined in Eq. (6):

    grad^2 phi(x,y) = 0        on x in [0, Xmax], y in [0, tf]
    phi(x, 0)  = f(x) = 0
    phi(x, tf) = g(x) = Vg
    phi(0, y)  = h(y)          (piecewise, Eq. 6)
    phi(Xmax,y) = Vg*y/tf      (far-field 1-D solution consistent with the
                                 y=0 and y=tf conditions holding for ALL x)

Phi_swl = -eps_ox * integral_0^tf (dphi/dx)|_{x=0} dy

is linear in (Vg, phi_s) [since h(y) is linear in them], so two solves
isolate A and B directly, matching Eq. (9)/(10)'s decomposition
Phi_swl = eps_ox[(Vg-phi_s)*A + phi_s*B]:

    Solve 1: Vg=1, phi_s=0  ->  Phi_swl_1 = eps_ox * A
    Solve 2: Vg=0, phi_s=1  ->  Phi_swl_2 = eps_ox * (B - A)

This settles empirically whether the printed Eq. (11) prefactor for A
(8k/(pi*tg), literally as typeset) or the dimensionally-corrected form
(8/(pi*k*tg)) is the one that actually solves the stated BVP.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from model import eps_ox, series_AB_case1

tf, tg, t1, td = 0.7e-6, 0.015e-6, 0.5e-6, 0.2994379411906389e-6
Xmax = 6 * tf   # far enough that the sidewall perturbation has decayed


def h_of_y(y, Vg, phis):
    out = np.zeros_like(y)
    m1 = (y > t1 + tg)
    m2 = (y > t1) & (y <= t1 + tg)
    m3 = (y > t1 - td) & (y <= t1)
    out[m1] = Vg
    out[m2] = phis + (Vg - phis) / tg * (y[m2] - t1)
    out[m3] = phis * (1 - (t1 - y[m3]) / td) ** 2
    return out


def solve_phi_swl(Vg, phis, Nx=900, Ny=900):
    x = np.linspace(0, Xmax, Nx)
    y = np.linspace(0, tf, Ny)
    dx = x[1] - x[0]
    dy = y[1] - y[0]

    # unknowns: interior points i=1..Nx-2, j=1..Ny-2 (Dirichlet on all 4 edges)
    ni, nj = Nx - 2, Ny - 2

    def idx(i, j):
        return i * nj + j

    N = ni * nj
    A = sp.lil_matrix((N, N))
    b = np.zeros(N)

    cx = 1.0 / dx**2
    cy = 1.0 / dy**2
    cdiag = -2 * cx - 2 * cy

    left_bc = h_of_y(y, Vg, phis)          # x = 0
    right_bc = Vg * y / tf                  # x = Xmax
    bottom_bc = 0.0                         # y = 0
    top_bc = Vg                             # y = tf

    for i in range(ni):
        for j in range(nj):
            k = idx(i, j)
            A[k, k] = cdiag
            # neighbor i-1 (x direction)
            if i - 1 >= 0:
                A[k, idx(i - 1, j)] += cx
            else:
                b[k] -= cx * left_bc[j + 1]
            # neighbor i+1
            if i + 1 < ni:
                A[k, idx(i + 1, j)] += cx
            else:
                b[k] -= cx * right_bc[j + 1]
            # neighbor j-1 (y direction)
            if j - 1 >= 0:
                A[k, idx(i, j - 1)] += cy
            else:
                b[k] -= cy * bottom_bc
            # neighbor j+1
            if j + 1 < nj:
                A[k, idx(i, j + 1)] += cy
            else:
                b[k] -= cy * top_bc

    A = A.tocsr()
    phi_flat = spla.spsolve(A, b)
    phi = phi_flat.reshape(ni, nj)

    # d(phi)/dx at x=0 using the interior column i=0 and the known x=0 boundary
    dphidx_x0 = (phi[0, :] - left_bc[1:-1]) / dx  # forward difference

    # Phi_swl = -eps_ox * integral_0^tf dphi/dx|_{x=0} dy  (trapezoidal, incl. endpoints=0 slope contribution at y=0,tf approximated by nearest interior)
    y_interior = y[1:-1]
    integral = np.trapz(dphidx_x0, y_interior)
    phi_swl = -eps_ox * integral
    return phi_swl


if __name__ == "__main__":
    print("Grid convergence check:")
    for N in [300, 600, 900]:
        ps1 = solve_phi_swl(1.0, 0.0, Nx=N, Ny=N)
        A_num = ps1 / eps_ox
        print(f"  N={N:4d}  A(numerical) = {A_num:.6e}")

    ps1 = solve_phi_swl(1.0, 0.0, Nx=900, Ny=900)
    ps2 = solve_phi_swl(0.0, 1.0, Nx=900, Ny=900)
    A_num = ps1 / eps_ox
    B_num = ps2 / eps_ox + A_num

    A_fix, B_fix = series_AB_case1(tf, tg, t1, td)          # A = 8/(pi k tg) ...
    k = np.pi / tf
    # "as printed" variant: A = 8k/(pi tg) * (same sum as A_fix but recomputed with that prefactor)
    n = np.arange(1, 6001)
    s1 = np.sin(0.5*n*k*td); s2 = np.sin(0.5*n*k*tg); s3 = np.sin(n*k*(t1-td/2)); c1 = np.cos(n*k*(t1+tg/2))
    A_asprinted = (8*k/(np.pi*tg)) * np.sum(s1*s2*s3*c1/n**2)

    print()
    print(f"{'':22s}{'A':>16s}{'B':>16s}")
    print(f"{'Numerical FD (BVP)':22s}{A_num:16.6e}{B_num:16.6e}")
    print(f"{'Series, as printed':22s}{A_asprinted:16.6e}{B_fix:16.6e}")
    print(f"{'Series, k-fixed':22s}{A_fix:16.6e}{B_fix:16.6e}")
    print()
    print(f"Ratio numerical/as-printed A: {A_num/A_asprinted:.4f}")
    print(f"Ratio numerical/k-fixed    A: {A_num/A_fix:.4f}")
