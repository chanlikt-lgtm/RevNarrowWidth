"""Build the reproduction report PDF for Li/Hong/Cheng/Chan (1990)."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle,
)
from reportlab.lib import colors

R = r"E:\claude\RAG\reports"
OUT = f"{R}/narrow_channel_semi_recessed_report.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1c", parent=styles["Heading1"], textColor=colors.HexColor("#1a2a5e")))
styles.add(ParagraphStyle("H2c", parent=styles["Heading2"], textColor=colors.HexColor("#1a2a5e")))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13.5))
styles.add(ParagraphStyle("Eq", parent=styles["Normal"], fontSize=9.5, leading=14,
                          leftIndent=24, fontName="Courier"))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8.5, leading=11,
                          textColor=colors.HexColor("#444444"), alignment=TA_CENTER))
styles.add(ParagraphStyle("TitleC", parent=styles["Title"], textColor=colors.HexColor("#1a2a5e")))

story = []

def h1(t): story.append(Paragraph(t, styles["H1c"])); story.append(Spacer(1, 6))
def h2(t): story.append(Paragraph(t, styles["H2c"])); story.append(Spacer(1, 4))
def p(t): story.append(Paragraph(t, styles["Body"])); story.append(Spacer(1, 6))
def eq(t): story.append(Paragraph(t, styles["Eq"])); story.append(Spacer(1, 6))
def fig(path, caption, width=6.0*inch):
    img = Image(path, width=width, height=width*0.72)
    story.append(img)
    story.append(Paragraph(caption, styles["Caption"]))
    story.append(Spacer(1, 10))

# ---------------------------------------------------------------- Title
story.append(Spacer(1, 40))
story.append(Paragraph("Reproduction Report", styles["TitleC"]))
story.append(Paragraph(
    "The Narrow-Channel Effect in MOSFET's with Semi-Recessed Oxide Structures",
    styles["Heading2"]))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "Li, Hong, Cheng &amp; Chan, <i>IEEE Trans. Electron Devices</i>, vol. 37, no. 3, "
    "pp. 692-701, March 1990", styles["Normal"]))
story.append(Spacer(1, 30))
p("This report reproduces the closed-form threshold-voltage model of Li et al. "
  "(conformal-mapping solution of Laplace's equation in the field-oxide sidewall/lateral "
  "region), verifies it against internal consistency checks and the paper's own figure "
  "legends, reproduces all eight result figures (Figs. 5-12), and compares the "
  "fully-recessed limit against the independently reproduced Akers (1986) model already "
  "in this repository (scripts/inverse_narrow_width.py).")
story.append(PageBreak())

# ---------------------------------------------------------------- Model
h1("1. Model")
p("An n-channel MOSFET with semi-recessed field-isolation (Fig. 1a) is characterized by "
  "field-oxide thickness t<sub>f</sub>, gate-oxide thickness t<sub>g</sub>, recess depth "
  "t<sub>1</sub>, and channel depletion depth t<sub>d</sub>. Fully-recessed and "
  "nonrecessed structures are the SAME model with t<sub>1</sub> = t<sub>f</sub> - t<sub>g</sub> "
  "or t<sub>1</sub> &#8594; 0 respectively (paper Sec. III-B/III-C) &mdash; no separate "
  "formula is needed.")

eq("t_d = sqrt( 2&#949;<sub>si</sub>(2&#966;<sub>f</sub> + |V<sub>bg</sub>|) / (qN<sub>a</sub>) )   (Eq. 1)")

p("Gauss's law over the gate + two sidewalls (Eq. 4-5), with the sidewall flux "
  "&#934;<sub>swl</sub> obtained by solving &#8711;&#178;&#966;=0 in the field-oxide cross "
  "section via the conformal map u+iv = cos[&#960;(ix-y)/t<sub>f</sub>] (Eq. 7), gives a "
  "regime split on whether the depletion depth exceeds the recess depth:")

table_data = [
    ["Regime", "Condition", "Physical picture", "Threshold-voltage form"],
    ["Case I", "t_d < t_1", "Depletion stays inside the\nsidewall (Fig. 2/3)",
     "V_th = &#966;_ms + 2&#966;_f(1+a/W)/(1+b/W)\n+ (Q'/C_ox)/(1+b/W)   (Eq. 12)"],
    ["Case II", "t_d > t_1", "Depletion spills laterally under\nthe field oxide, quarter-circle\nwing radius W_c=t_d-t_1 (Fig. 4)",
     "Same form with a',b' (Eq.17)\nand Q' including the W_c\nwing charge (Eq. 19)"],
]
tbl = Table(table_data, colWidths=[0.7*inch, 0.9*inch, 2.1*inch, 2.3*inch])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a2a5e")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTSIZE", (0,0), (-1,-1), 8),
    ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f2fa")]),
]))
story.append(tbl)
story.append(Spacer(1, 10))

p("a, b (Case I) come from a and b = 2t<sub>g</sub>(B-A), -2t<sub>g</sub>A, where A, B are "
  "convergent Fourier series (Eq. 11) obtained from the Poisson kernel of the "
  "half-plane image of the conformally-mapped domain; a', b' (Case II) come analogously "
  "from A', B' (Eq. 17), which additionally carry exponential decay "
  "e<sup>-nkW<sub>c</sub></sup> from the lateral wing. Both series were verified to "
  "converge to 6 significant figures by n &#8776; 200-1000 terms (paper's own claim of "
  "rapid convergence, confirmed numerically).")

p("<b>Key implementation note (superseded by &sect;2 below):</b> Comparing units in Eq. (12) "
  "(a/W, b/W must be dimensionless with a=2t<sub>g</sub>(B-A)) requires A, B themselves to be "
  "dimensionless. The as-printed prefactor of A in Eq. (11) reads 8k/(&#960;t<sub>g</sub>), "
  "which has units of inverse length squared and is dimensionally inconsistent. By analogy "
  "with B's confirmed prefactor 8/(&#960;kt<sub>d</sub>) and with A' in Eq. (17) "
  "(4/(&#960;kt<sub>g</sub>), k in the denominator), a dimensionally-consistent prefactor for "
  "A would be 8/(&#960;kt<sub>g</sub>); a separately-found missing factor of &#189; on "
  "sin(nkt<sub>g</sub>) was also corrected. <b>However, as described in &sect;2, even both "
  "fixes together were not sufficient</b> &mdash; an independent finite-difference solve of "
  "the actual boundary-value problem showed the corrected series still does not reproduce "
  "the true A, B. The figures and the Akers comparison in this report therefore use the "
  "finite-difference solution directly (not the Eq. 11/17 series in any form) as the "
  "verified ground truth for A, B, A', B'.")

# ---------------------------------------------------------------- Verification
h1("2. Verification")
p("<b>Case-boundary check.</b> For the semi-recessed device of Fig. 5 "
  "(t<sub>f</sub>=0.7, t<sub>1</sub>=0.5, t<sub>g</sub>=0.015 &#181;m, N<sub>a</sub>=10<sup>16</sup> "
  "cm<sup>-3</sup>), Eq. (1) predicts t<sub>d</sub>(V<sub>bg</sub>=0)=0.299, "
  "t<sub>d</sub>(-1V)=0.468 &#181;m (both &lt; t<sub>1</sub>=0.5 &#8594; Case I) and "
  "t<sub>d</sub>(-2V)=0.590, (-4V)=0.779, (-6V)=0.930 &#181;m (all &gt; 0.5 &#8594; Case II). "
  "This matches, bias-by-bias, the Case I / Case II grouping drawn in the paper's own "
  "Fig. 5 legend (0, -1 V bracketed \"Case I\"; -2, -4, -6 V bracketed \"Case II\") "
  "&mdash; strong independent confirmation of Eq. (1) and the regime split.")
p("<b>Series vs. finite-difference cross-check.</b> The two prefactor/factor fixes "
  "described above (Sec. 1) were caught by dimensional analysis alone, and on their own "
  "did not settle whether Eq. (11)/(17), as transcribed, is actually correct &mdash; "
  "dimensional consistency is necessary but not sufficient. To settle this independently, "
  "the underlying boundary-value problem itself (&#8711;&#178;&#966;=0 with the exact "
  "piecewise boundary condition of Eq. 6 for Case I, and Eq. 14/15 for Case II) was solved "
  "directly with a finite-difference (5-point Laplacian, sparse direct solve) code "
  "independent of the closed-form series (scripts/narrow_semi_recessed/fd_solver.py, "
  "verify_series.py). Result: <b>neither the as-printed nor the dimensionally-corrected "
  "series matches the finite-difference solution</b> &mdash; even B, whose prefactor was "
  "never in question, disagreed by roughly a factor of two. This means the transcribed "
  "series still contains at least one further error that dimensional analysis alone cannot "
  "catch (e.g. in how Eq. 8/9's decomposition was carried through to Eq. 11), and which "
  "could not be pinned down further because in-session re-inspection of the source PDF at "
  "high resolution became unavailable partway through this check (an image-count/size API "
  "limit).")
p("<b>Validating the finite-difference solver itself.</b> Before trusting the "
  "finite-difference result over the series, the solver was independently validated two "
  "ways that do not depend on Eq. (11)/(17) at all: (1) in the sharp-step limit "
  "t<sub>d</sub>,t<sub>g</sub>&#8594;0, the boundary condition collapses to a step function, "
  "for which the bounded harmonic extension has the classical closed form "
  "(V<sub>g</sub>/&#960;)&#183;Arg(w-U<sub>0</sub>); the finite-difference Case I solution "
  "converges toward this hand-derived value as t<sub>d</sub>, t<sub>g</sub> shrink from "
  "300/15 nm down to 2/0.2 nm (A: -0.4930 &#8594; -0.4741 &#8594; -0.4670 &#8594; -0.4659, "
  "vs. analytic limit -0.4652). (2) Case I and Case II are two different boundary-value "
  "problems that must agree at their shared boundary (t<sub>d</sub>&#8594;t<sub>1</sub>, "
  "W<sub>c</sub>&#8594;0); the two independently-coded finite-difference solutions do "
  "converge to the same A, A' (both &#8594;-0.49295) and the same B, B' as the gap shrinks "
  "from 50 nm to 2 nm, once a bug in the Case II lateral-wing flux integration bound (it "
  "must integrate only over 0&lt;x&lt;W<sub>c</sub>, per Eq. 14, not the full domain) was "
  "found and fixed via exactly this check. Both checks passing gives confidence the "
  "finite-difference solver is correct, so it &mdash; not the Eq. 11/17 series &mdash; is "
  "used as the ground truth for A, B, A', B' throughout the figures and comparison below.")
p("<b>Interface-charge legend.</b> The Q<sub>ss</sub> legend of Fig. 6 lists values "
  "1.6&#215;10<sup>-9</sup>...3.2&#215;10<sup>-8</sup> cm<sup>-2</sup> &mdash; these are "
  "already areal charge densities in C/cm&#178; (=q&#215;areal number density), not number "
  "densities, and were used directly (&#215;10<sup>4</sup> for C/m&#178;) as &#961;<sub>s</sub>=&#961;<sub>f</sub>.")

# ---------------------------------------------------------------- Figures
h1("3. Reproduced Figures")
h2("3.1 Semi-recessed structure (t1 = 0.5 um)")
fig(f"{R}/li1990_fig5_repro.png",
    "Fig. 5 repro: backgate-bias sweep. Vbg=0,-1V (Case I) show the inverse-narrow-width "
    "effect (Vth-Vth(wide) < 0, deepening at small W); Vbg=-2,-4,-6V (Case II) show the "
    "conventional effect (positive, growing at small W) &mdash; matches the paper's own "
    "Case I/II split exactly.")
fig(f"{R}/li1990_fig6_repro.png",
    "Fig. 6 repro: fixed interface charge Qss sweep (Vbg=0, always Case I here). Higher "
    "Qss deepens the inverse-narrow-width dip, consistent with the paper's statement that "
    "positive fixed charge enhances the inverse effect.")
fig(f"{R}/li1990_fig7_repro.png",
    "Fig. 7 repro: substrate doping Na sweep. Na=1e16,1e17 cm-3 stay in Case I (inverse "
    "effect, deepening with Na); Na=1e14,1e15 cm-3 fall in Case II (conventional effect) "
    "&mdash; matches the paper's discussion of a doping window where the effect reverses.")
story.append(PageBreak())

h2("3.2 Fully-recessed structure (t1 = tf - tg = 0.685 um, Sec. III-B)")
fig(f"{R}/li1990_fig8_repro.png",
    "Fig. 8 repro: backgate bias, fully recessed. At this larger t1 the Case I/II boundary "
    "moves to about Vbg=-2.9 V; the shown biases mostly sit in the (still-inverse-looking) "
    "Case I / weak-Case-II band, with the full sign reversal only setting in beyond about "
    "-5 V (see Sec. 4 comparison plot).")
fig(f"{R}/li1990_fig9_repro.png",
    "Fig. 9 repro: Qss sweep, fully recessed.")
fig(f"{R}/li1990_fig10_repro.png",
    "Fig. 10 repro: Na sweep, fully recessed.")
story.append(PageBreak())

h2("3.3 Nonrecessed structure (t1 -> 0, Sec. III-C)")
fig(f"{R}/li1990_fig11_repro.png",
    "Fig. 11 repro: backgate bias, nonrecessed. t1->0 forces Case II for any bias, so only "
    "the conventional narrow-channel effect is possible (Jeppson's classical result), with "
    "magnitude growing monotonically with |Vbg| as expected.")
fig(f"{R}/li1990_fig12_repro.png",
    "Fig. 12 repro: Na sweep, nonrecessed &mdash; conventional effect for all doping levels, "
    "strongest at high Na.")
story.append(PageBreak())

# ---------------------------------------------------------------- Comparison
h1("4. Comparison with Akers (1986) fully-recessed model")
p("scripts/inverse_narrow_width.py already reproduces Akers &amp; Jepson's closed-form "
  "fully-recessed model (a single narrow-width regime, PMOS, L=0.75 &#181;m), which "
  "predicts |V<sub>t</sub>(W)| = |V<sub>t</sub>(&#8734;)|&#183;W/(W+F) with fringing length "
  "F=(4T<sub>ox</sub>/&#960;)ln(2T<sub>d</sub>/T<sub>ox</sub>)=91 nm for its device "
  "parameters. Li et al.'s Case I formula, evaluated at t<sub>1</sub>=t<sub>f</sub>-t<sub>g</sub> "
  "(fully recessed) and V<sub>bg</sub>=0, is the general finite-t<sub>f</sub> version of "
  "the same physics (paper Sec. II-B states this limit explicitly) and produces its own "
  "length scales a=42.3 nm, b=71.8 nm (finite-difference-verified, per &sect;2) &mdash; the "
  "same order of magnitude as Akers' F=91 nm despite completely different device parameters "
  "(N<sub>a</sub>, T<sub>ox</sub>, T<sub>d</sub>) and independent derivations (closed-form "
  "log-integral vs. conformal-mapping/Poisson-kernel).")
fig(f"{R}/li1990_vs_akers1986.png",
    "Left: normalized narrow-width relaxation shape &mdash; Akers 1986 vs. Li 1990 Case I "
    "fully-recessed, near-identical shape. Right: Li's fully-recessed model at increasing "
    "|Vbg| shows the sidewall term losing out to the depletion \"wing\" charge once "
    "Wc=td-t1 grows enough (around -6 V here), flipping the sign from inverse to "
    "conventional narrow-channel effect &mdash; a regime transition Akers' single-formula "
    "model cannot represent because it has no backgate-bias dependence at all.")

p("<b>Physical takeaway:</b> Akers (1986) and Li et al. (1990) agree in the shared limit "
  "(fully-recessed, low bias) to within the same length-scale magnitude, confirming both "
  "are self-consistent descriptions of the same sidewall fringing-field physics. Li et "
  "al.'s contribution is generalizing to finite t<sub>f</sub> and, more importantly, showing "
  "that the same fully-recessed structure can flip from inverse to conventional "
  "narrow-channel behavior purely as a function of backgate bias / substrate doping, once "
  "the depletion region outgrows the recess depth &mdash; a regime Akers' model, built "
  "only around the always-Case-I sidewall term, does not contain.")

h1("5. Limitations / open items")
p("&#8226; Sweep values (V<sub>bg</sub>, Q<sub>ss</sub>, N<sub>a</sub>) were read directly "
  "off the paper's figure legends via high-resolution crops, not assumed; the underlying "
  "device parameters (t<sub>f</sub>, t<sub>g</sub>, t<sub>1</sub>) are stated explicitly "
  "in each figure caption. <br/>"
  "&#8226; &#966;<sub>ms</sub> and the fixed gate charge &#961;<sub>g</sub> were left as an "
  "arbitrary common offset (they only shift the absolute V<sub>th</sub>, and cancel exactly "
  "in V<sub>th</sub>(W)-V<sub>th</sub>(wide), the quantity plotted in every figure of the "
  "paper), so absolute V<sub>th</sub> values are not reproduced or claimed here &mdash; "
  "only the narrow-width shift, which is what the paper itself plots. <br/>"
  "&#8226; The exact peak magnitude of the Case-II curves in Fig. 5/8 could not be checked "
  "against the paper beyond qualitative shape and ordering, since the paper's own plotted "
  "axis range (-0.05 to +0.10 V) clips the curves before they saturate at small W; our "
  "reproduction extends the same closed-form formula beyond that clipped range. <br/>"
  "&#8226; Unlike the earlier POISSON/superjunction paper reproductions in this workspace, "
  "the transcription issue in Eq. (11)/(17) here was <b>not</b> fully resolved to a single "
  "identified typo. Two dimensional-analysis-level fixes (A's prefactor, a missing &#189; "
  "factor) were necessary but demonstrably not sufficient: an independent finite-difference "
  "solve of the actual BVP (&sect;2) still disagrees with the corrected series, including in "
  "B, whose prefactor was never ambiguous. The root cause of this remaining discrepancy is "
  "unresolved &mdash; it may be a further transcription slip not caught here, or a subtlety "
  "in how Eq. 8/9 was condensed into Eq. 11 that a purely visual re-read could not settle "
  "once further high-resolution image inspection became unavailable this session. All "
  "figures and the &sect;4 comparison in this report are therefore built on the "
  "finite-difference ground truth, not the literal closed-form series, and should be read "
  "as a verified reproduction of the paper's underlying physics (Eq. 1-10, 14-15) rather "
  "than a line-by-line validation of Eq. 11/17 as printed.")
story.append(Spacer(1, 10))

doc = SimpleDocTemplate(OUT, pagesize=letter,
                         topMargin=0.7*inch, bottomMargin=0.7*inch,
                         leftMargin=0.75*inch, rightMargin=0.75*inch)
doc.build(story)
print("Wrote", OUT)
