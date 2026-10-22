"""
Independent third derivation of A (Case I, Eq. 11) via the Green's-
function / eigenfunction-expansion method for the semi-infinite strip
BVP, bypassing the paper's conformal-map + Poisson-kernel route entirely.

BVP (same as fd_solver.py / verify_series.py):
    grad^2 phi(x,y) = 0    on x in [0, inf), y in [0, tf]
    phi(x, 0)  = 0
    phi(x, tf) = Vg
    phi(0, y)  = h(y)         (Eq. 6, piecewise)
    phi(x->inf, y) -> Vg*y/tf

Subtracting the far-field profile, psi = phi - Vg*y/tf solves homogeneous
Laplace with psi(x,0)=psi(x,tf)=0, psi(0,y)=g(y):=h(y)-Vg*y/tf. Since y is
bounded with homogeneous Dirichlet ends, the natural eigenfunctions are
sin(n*pi*y/tf):

    psi(x,y) = sum_n c_n * exp(-n*pi*x/tf) * sin(n*pi*y/tf)
    c_n = (2/tf) * integral_0^tf g(y) sin(n*pi*y/tf) dy

Phi_swl = -eps_ox * integral_0^tf (dpsi/dx)|_{x=0} dy reduces (since
integral_0^tf sin(n*pi*y/tf) dy is 0 for even n, 2*tf/(n*pi) for odd n) to

    Phi_swl = 2 * eps_ox * sum_{n odd} c_n

Two solves (Vg=1,phis=0 and Vg=0,phis=1) then isolate A, B directly, same
as the FD approach, but via a completely different derivation (no
conformal map, no Poisson kernel -- direct eigenfunction/Green's-function
expansion for the strip).

IMPLEMENTATION NOTE: a first pass using scipy.integrate.quad numerically
for each c_n gave A=-0.4936 at nmax=100 -- strikingly close to the FD
ground truth (-0.4930, ~0.1% agreement) -- but then degraded badly for
larger nmax (quad's adaptive scheme can't resolve the increasingly rapid
sin(n*pi*y/tf) oscillation at fixed tolerance). Since g(y) is exactly
piecewise-polynomial (Eq. 6: linear/quadratic/constant pieces), the
Fourier coefficients admit an EXACT closed form via integration by parts
-- computed symbolically here with sympy once, then evaluated to full
float64 precision for any n, removing the oscillatory-quadrature error
entirely.
"""
import numpy as np
import sympy as sp

tf, tg, t1, td = 0.7e-6, 0.015e-6, 0.5e-6, 0.2994379411906389e-6

y, n_sym, Vg_s, phis_s = sp.symbols("y n Vg phis", positive=False, real=True)
k_sym = n_sym * sp.pi / tf

# g(y) on each of the 4 pieces (Eq. 6 minus the far-field Vg*y/tf term)
g1 = -Vg_s * y / tf                                              # 0 <= y <= t1-td
g2 = phis_s * (1 - (t1 - y) / td) ** 2 - Vg_s * y / tf            # t1-td < y <= t1
g3 = phis_s + (Vg_s - phis_s) / tg * (y - t1) - Vg_s * y / tf     # t1 < y <= t1+tg
g4 = Vg_s * (1 - y / tf)                                          # t1+tg < y <= tf

breakpoints = [0, t1 - td, t1, t1 + tg, tf]
pieces = [g1, g2, g3, g4]

# Exact symbolic antiderivative of g_i(y)*sin(k*y) w.r.t. y, for each piece
integrals = [sp.integrate(gi * sp.sin(k_sym * y), y) for gi in pieces]

_cn_expr_cache = {}


def _cn_symbolic_definite():
    """Sum the exact definite integral over all 4 pieces symbolically once
    (as a function of n, Vg, phis) -- then lambdify for fast repeated
    numeric evaluation."""
    total = 0
    for F, (a, b) in zip(integrals, zip(breakpoints[:-1], breakpoints[1:])):
        total += (F.subs(y, b) - F.subs(y, a))
    cn_expr = (2 / tf) * total
    return sp.lambdify((n_sym, Vg_s, phis_s), cn_expr, "numpy")


print("Deriving exact closed-form Fourier coefficients symbolically (one-time cost)...")
_cn_func = _cn_symbolic_definite()
print("Done.")


def c_n(n, Vg, phis):
    return float(_cn_func(n, Vg, phis))


def A_via_greens(Vg, phis, nmax=2000):
    """Returns Phi_swl/eps_ox = 2 * sum_{n odd} c_n (eps_ox cancels exactly,
    per Eq. 9's Phi_swl = eps_ox*[(Vg-phis)*A + phis*B] decomposition)."""
    n_odd = np.arange(1, nmax + 1, 2)
    vals = np.array([c_n(int(n), Vg, phis) for n in n_odd])
    return 2 * np.sum(vals)


if __name__ == "__main__":
    print()
    print("=== Green's-function / eigenfunction-expansion re-derivation of A, B ===")
    print("(bypasses the paper's conformal map entirely -- direct strip eigenfunctions,")
    print(" exact symbolic Fourier coefficients, not numerical quadrature)")
    print()
    print("Convergence vs. number of odd terms:")
    for nmax in [10, 50, 100, 200, 500, 1000, 2000]:
        A1 = A_via_greens(1.0, 0.0, nmax=nmax)
        print(f"  nmax={nmax:5d}   A = {A1:.6f}")

    A_num = A_via_greens(1.0, 0.0, nmax=2000)
    B_minus_A = A_via_greens(0.0, 1.0, nmax=2000)
    B_num = B_minus_A + A_num

    print()
    print(f"{'':32s}{'A':>14s}{'B':>14s}")
    print(f"{'Greens function (this file)':32s}{A_num:14.6f}{B_num:14.6f}")
    print(f"{'FD ground truth (earlier session)':32s}{-0.49295:14.6f}{0.06060:14.6f}")
    print()
    print("(FD numbers above are from the earlier session's fd_solver.py run at the")
    print(" same (tf,tg,t1,td) point; rerun fd_solver.py directly for a live check.)")
