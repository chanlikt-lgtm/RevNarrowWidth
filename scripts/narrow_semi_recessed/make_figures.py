"""
Reproduce Figs. 5-12 of Li, Hong, Cheng & Chan (1990), "The Narrow-Channel
Effect in MOSFET's with Semi-Recessed Oxide Structures," IEEE TED 37(3).

Semi-recessed:  t1 = 0.5 um            (Figs. 5-7)
Fully recessed: t1 = tf - tg = 0.685um (Figs. 8-10, Sec. III-B)
Nonrecessed:    t1 -> 0                (Figs. 11-12, Sec. III-C)

All device parameters and sweep values (Vbg, Qss, Na) below were read
directly off the paper's figure legends (see fig5_legend.png etc. in
this folder), not guessed.
"""
import numpy as np
import matplotlib.pyplot as plt
from model import delta_vth, select_case, q

OUT = r"E:\claude\RAG\reports"

tf, tg = 0.7e-6, 0.015e-6
t1_semi = 0.5e-6
t1_full = tf - tg          # 0.685 um (paper rounds to 0.6849)
t1_none = 1e-10            # nonrecessed limit

W_um = np.linspace(0.05, 4.0, 400)
W = W_um * 1e-6

Na_ref = 1e16 * 1e6        # cm^-3 -> m^-3


def to_rho(Css_per_cm2):
    """Qss legend values are already C/cm^2 (q * areal density); -> C/m^2."""
    return Css_per_cm2 * 1e4


def curve(t1, Na, Vbg, rho=0.0):
    case, td = select_case(Na, Vbg, t1)
    y = np.array([delta_vth(w, tf, tg, t1, Na, Vbg, rho_s=rho, rho_f=rho) for w in W])
    return y, case, td


def plot_vbg(t1, title, fname, vbg_list=(0, -1, -2, -4, -6)):
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for vbg in vbg_list:
        y, case, td = curve(t1, Na_ref, vbg)
        ax.plot(W_um, y, label=f"Vbg={vbg} V (Case {case}, td={td*1e6:.3f} um)")
    ax.set_xlabel("Channel width (um)")
    ax.set_ylabel("Vth - Vth(wide)  (V)")
    ax.set_title(title)
    ax.legend(fontsize=7)
    ax.axhline(0, color="k", lw=0.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/{fname}", dpi=150)
    plt.close(fig)


def plot_qss(t1, title, fname, qss_list=(0, 1.6e-9, 8.0e-9, 1.6e-8, 3.2e-8)):
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for qss in qss_list:
        y, case, td = curve(t1, Na_ref, 0.0, rho=to_rho(qss))
        ax.plot(W_um, y, label=f"Qss={qss:.1e} C/cm2 (Case {case})")
    ax.set_xlabel("Channel width (um)")
    ax.set_ylabel("Vth - Vth(wide)  (V)")
    ax.set_title(title)
    ax.legend(fontsize=7)
    ax.axhline(0, color="k", lw=0.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/{fname}", dpi=150)
    plt.close(fig)


def plot_na(t1, title, fname, na_list=(1e14, 1e15, 1e16, 1e17)):
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for na_cm3 in na_list:
        Na = na_cm3 * 1e6
        y, case, td = curve(t1, Na, 0.0)
        ax.plot(W_um, y, label=f"Na={na_cm3:.0e} cm-3 (Case {case})")
    ax.set_xlabel("Channel width (um)")
    ax.set_ylabel("Vth - Vth(wide)  (V)")
    ax.set_title(title)
    ax.legend(fontsize=7)
    ax.axhline(0, color="k", lw=0.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/{fname}", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    plot_vbg(t1_semi, "Fig 5 repro: backgate bias, semi-recessed (t1=0.5um)", "li1990_fig5_repro.png")
    plot_qss(t1_semi, "Fig 6 repro: Qss, semi-recessed (t1=0.5um)", "li1990_fig6_repro.png")
    plot_na(t1_semi, "Fig 7 repro: Na, semi-recessed (t1=0.5um)", "li1990_fig7_repro.png")

    plot_vbg(t1_full, "Fig 8 repro: backgate bias, fully recessed (t1=tf-tg)", "li1990_fig8_repro.png")
    plot_qss(t1_full, "Fig 9 repro: Qss, fully recessed (t1=tf-tg)", "li1990_fig9_repro.png")
    plot_na(t1_full, "Fig 10 repro: Na, fully recessed (t1=tf-tg)", "li1990_fig10_repro.png")

    plot_vbg(t1_none, "Fig 11 repro: backgate bias, nonrecessed (t1->0)", "li1990_fig11_repro.png")
    plot_na(t1_none, "Fig 12 repro: Na, nonrecessed (t1->0)", "li1990_fig12_repro.png")

    print("All 8 figures written to", OUT)
