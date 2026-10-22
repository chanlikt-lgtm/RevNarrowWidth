"""Build the deep-verification report PDF: theory, algorithm, independent
verification methods (FD + Green's function), per-term error diagnosis,
and pixel-calibrated accuracy comparison against the paper's own Fig. 10.

Companion to narrow_channel_semi_recessed_report.pdf (the original
reproduction report) -- this report documents the SECOND, deeper round of
verification requested after that report was delivered."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle,
    ListFlowable, ListItem,
)
from reportlab.lib import colors

R = r"E:\claude\RAG\reports"
OUT = f"{R}/li1990_deep_verification_report.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1c", parent=styles["Heading1"], textColor=colors.HexColor("#1a2a5e")))
styles.add(ParagraphStyle("H2c", parent=styles["Heading2"], textColor=colors.HexColor("#1a2a5e")))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13.5))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8.5, leading=11,
                          textColor=colors.HexColor("#444444"), alignment=TA_CENTER))
styles.add(ParagraphStyle("TitleC", parent=styles["Title"], textColor=colors.HexColor("#1a2a5e")))
styles.add(ParagraphStyle("TCell", parent=styles["Normal"], fontSize=8, leading=10))
styles.add(ParagraphStyle("TCellHdr", parent=styles["Normal"], fontSize=8.2, leading=10.2,
                          textColor=colors.white, fontName="Helvetica-Bold"))


def cell(text, header=False):
    return Paragraph(text, styles["TCellHdr"] if header else styles["TCell"])


def table_row(cells, header=False):
    return [cell(c, header=header) for c in cells]


story = []

def h1(t): story.append(Paragraph(t, styles["H1c"])); story.append(Spacer(1, 6))
def h2(t): story.append(Paragraph(t, styles["H2c"])); story.append(Spacer(1, 4))
def p(t): story.append(Paragraph(t, styles["Body"])); story.append(Spacer(1, 6))
def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles["Body"]), leftIndent=6) for t in items],
        bulletType="bullet", start="•", leftIndent=14))
    story.append(Spacer(1, 8))
def fig(path, caption, width=6.2*inch, ratio=0.5):
    img = Image(path, width=width, height=width*ratio)
    story.append(img)
    story.append(Paragraph(caption, styles["Caption"]))
    story.append(Spacer(1, 10))

# ================================================================== Title
story.append(Spacer(1, 40))
story.append(Paragraph("Deep Verification Report", styles["TitleC"]))
story.append(Paragraph(
    "The Narrow-Channel Effect in MOSFET's with Semi-Recessed Oxide Structures",
    styles["Heading2"]))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "Li, Hong, Cheng &amp; Chan, <i>IEEE Trans. Electron Devices</i>, vol. 37, no. 3, "
    "pp. 692-701, March 1990 &mdash; companion to narrow_channel_semi_recessed_report.pdf",
    styles["Normal"]))
story.append(Spacer(1, 30))
p("This report documents a second, deeper round of verification of the Case I "
  "closed-form series (Eq. 11), beyond what the original reproduction report covered. "
  "Three questions are answered here with concrete evidence, not just argument: "
  "(1) can independent methods beyond finite-difference (FD) confirm or refute Eq. 11 -- "
  "yes, a from-scratch Green's-function/eigenfunction derivation agrees with FD to "
  "&lt;0.1% while disagreeing with Eq. 11; (2) can the specific error in Eq. 11 be "
  "localized -- partially, to an argument/phase-level issue, via a per-term diagnostic; "
  "(3) does matching the paper's own published Fig. 10 mean the paper is correct -- "
  "no, and this report shows concretely why: the paper's own Eq. 11 formula reproduces "
  "the paper's own published curve almost exactly, meaning the figure and the formula "
  "are the same piece of evidence, not two independent ones.")
story.append(PageBreak())

# ================================================================== 1. Theory
h1("1. Theory (Recap)")
p("A semi-recessed field-oxide MOSFET's narrow-channel behavior is governed by "
  "Laplace's equation in the field-oxide sidewall cross-section, solved via the "
  "conformal map u+iv = cos[&#960;(ix&minus;y)/t<sub>f</sub>], which turns the "
  "semi-infinite half-strip domain into a half-plane Poisson-kernel problem. Two "
  "regimes depend on the channel depletion depth t<sub>d</sub> vs. the recess depth "
  "t<sub>1</sub>:")
bullets([
    "<b>Case I</b> (t<sub>d</sub> &lt; t<sub>1</sub>): depletion confined to the "
    "sidewall &rarr; inverse narrow-width effect (&Delta;V<sub>th</sub> &lt; 0).",
    "<b>Case II</b> (t<sub>d</sub> &gt; t<sub>1</sub>): depletion spills laterally "
    "under the field oxide &rarr; typically the conventional effect, though the sign "
    "is not guaranteed by the Case label alone -- see Section 5.",
])
p("The series coefficients A, B (Case I, Eq. 11) feed "
  "V<sub>th</sub>(W) = &#966;<sub>ms</sub> + 2&#966;<sub>f</sub>(1+a/W)/(1+b/W) + "
  "(Q&prime;/C<sub>ox</sub>)/(1+b/W), with a=2t<sub>g</sub>(B&minus;A), "
  "b=&minus;2t<sub>g</sub>A. This report is entirely about whether the transcribed "
  "Eq. 11 correctly gives A, B.")

# ================================================================== 2. Algorithm
h1("2. Algorithm")
p("Two computational paths exist for A, B (Case I):")
table_data = [
    table_row(["Path", "Method", "Status"], header=True),
    table_row(["(a) Closed-form series",
               "Direct evaluation of the paper's Eq. 11 as transcribed (with two "
               "dimensional-analysis fixes: A's prefactor, a missing 1/2 factor)",
               "Cheap, but shown broken (Sec. 3-4)"]),
    table_row(["(b) Finite-difference (FD)",
               "5-point Laplacian discretization of Eq. 6's boundary-value problem, "
               "sparse direct solve (scipy.sparse.linalg.spsolve), A/B isolated via two "
               "linear solves (Vg=1,&#966;s=0 and Vg=0,&#966;s=1)",
               "Ground truth used by model.py"]),
    table_row(["(c) Green's function (this report)",
               "Direct eigenfunction expansion (sin(n&#960;y/t<sub>f</sub>)) for the "
               "same strip BVP, bypassing the conformal map entirely; exact symbolic "
               "Fourier coefficients via sympy",
               "New: independent 2nd confirmation of (b)"]),
]
tbl = Table(table_data, colWidths=[1.5*inch, 3.8*inch, 1.3*inch])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a2a5e")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f2fa")]),
]))
story.append(tbl)
story.append(Spacer(1, 10))

# ================================================================== 3. Green's function derivation
h1("3. Independent Re-derivation via Green's Function / Eigenfunction Expansion")
p("Subtracting the far-field profile, &psi; = &#966; &minus; V<sub>g</sub>y/t<sub>f</sub> "
  "solves homogeneous Laplace with &psi;(x,0)=&psi;(x,t<sub>f</sub>)=0, "
  "&psi;(0,y)=g(y):=h(y)&minus;V<sub>g</sub>y/t<sub>f</sub>. Since y is bounded with "
  "homogeneous Dirichlet ends, the natural eigenfunctions are sin(n&#960;y/t<sub>f</sub>) "
  "&mdash; no conformal map, no Poisson kernel, a completely different derivation path:")
story.append(Paragraph(
    "&psi;(x,y) = &Sigma;<sub>n</sub> c<sub>n</sub>&#183;e<sup>&minus;n&#960;x/t<sub>f</sub></sup>"
    "&#183;sin(n&#960;y/t<sub>f</sub>),&nbsp;&nbsp;&nbsp;"
    "c<sub>n</sub> = (2/t<sub>f</sub>)&#8747;<sub>0</sub><sup>t<sub>f</sub></sup> g(y)sin(n&#960;y/t<sub>f</sub>)dy",
    styles["Body"]))
story.append(Spacer(1, 6))
p("Integrating for the sidewall flux &Phi;<sub>swl</sub> (which gives A, B) collapses "
  "cleanly: &#8747;sin(n&#960;y/t<sub>f</sub>)dy vanishes for even n, giving "
  "&Phi;<sub>swl</sub> = 2&#949;<sub>ox</sub>&Sigma;<sub>n odd</sub>c<sub>n</sub>. Since "
  "g(y) is exactly piecewise-polynomial (Eq. 6's linear/quadratic/constant pieces), "
  "c<sub>n</sub> was computed via EXACT symbolic integration (sympy), not numerical "
  "quadrature &mdash; a first attempt using scipy.integrate.quad degraded badly above "
  "n&asymp;100 due to unresolved oscillation at high n, a useful reminder that closed-form "
  "does not automatically mean numerically robust.")
fig(f"{R}/deepverif_convergence.png",
    "Fig. 1: FD (left) and Green's-function (right) both converge to A &asymp; -0.4931 "
    "&mdash; agreement to &lt;0.1% between two derivations sharing no code, no "
    "conformal map, and no common assumption beyond the stated Eq. 6 boundary condition.")
p("At the exact matching design point (t<sub>f</sub>=0.7, t<sub>g</sub>=0.015, "
  "t<sub>1</sub>=0.5, t<sub>d</sub>=0.2994 &#181;m): FD gives A=-0.49304, B=-0.15046; "
  "Green's function gives A=-0.49310, B=-0.15048. The paper's own Eq. 11 (k-fixed) "
  "gives A=-1.33621, B=-0.33607 at the same point &mdash; off by ~2.7&times; (A) and "
  "~2.2&times; (B).")

story.append(PageBreak())

# ================================================================== 4. Per-term diagnostic
h1("4. Diagnosing the Discrepancy: Per-Term Analysis")
p("Comparing the paper's individual n-th series term against the exact Green's-function "
  "term (2c<sub>n</sub>) for the SAME n reveals a striking pattern: the ratio is wildly "
  "inconsistent in both sign and magnitude, EXCEPT at n=7, 21, 35... (exact multiples of 7) "
  "where it hits exactly 1.0.")
fig(f"{R}/deepverif_perterm_ratio.png",
    "Fig. 2: Per-term ratio of paper's T_n to the exact value, for n=1..31. Perfect "
    "agreement only at n=7,21 &mdash; not a coincidence: for this device, "
    "t<sub>1</sub>/t<sub>f</sub> = 0.5/0.7 = 5/7 exactly, so n&#183;k&#183;t<sub>1</sub> "
    "only lands on a multiple of &#960; when n is a multiple of 7.")
p("This is the signature of a wrong argument/phase inside one of the trig terms "
  "(a combination of t<sub>1</sub>, t<sub>g</sub>, t<sub>d</sub> that's slightly off), "
  "NOT a missing scalar prefactor or an even/odd-n restriction issue &mdash; those "
  "hypotheses were tested directly (swapping t<sub>1</sub>&plusmn;t<sub>g</sub>/2 and "
  "t<sub>1</sub>&plusmn;t<sub>d</sub>/2 combinations in the cos/sin arguments) and none "
  "produced a consistently-1 ratio across all n. Fully localizing the exact error would "
  "require re-deriving Eq. 7&rarr;11 from the stated Poisson-kernel/Schwarz-integral "
  "construction step by step &mdash; a substantially larger undertaking than pattern-"
  "matching candidate sign flips, and not completed here. What IS established: the "
  "error is structural (argument-level), not a simple typo with an obvious single fix.")

# ================================================================== 5. Fig 10 accuracy
h1("5. Accuracy vs. the Published Paper: Fig. 10 Pixel-Calibrated Comparison")
p("The actual Fig. 10 was cropped from the source PDF and digitized by calibrating "
  "pixel coordinates against the visible axis gridlines (y: 0.2/0/-0.2; x: 0/1), then "
  "reading curve positions at several matching channel widths.")
summary_data = [
    table_row(["W(&#181;m)", "Na=1e14\n(paper/ours)", "Na=1e15\n(paper/ours)",
               "Na=1e16\n(paper/ours)", "Na=1e17\n(paper/ours)"], header=True),
    table_row(["0.15", "0.179 / 0.015", "-0.035 / -0.032", "-0.129 / -0.160", "(off-scale)"]),
    table_row(["0.20", "0.153 / 0.012", "-0.028 / -0.027", "-0.105 / -0.130", "-0.173 / -0.320"]),
    table_row(["0.30", "0.121 / 0.010", "-0.021 / -0.019", "-0.077 / -0.095", "-0.124 / -0.234"]),
    table_row(["0.50", "0.084 / 0.007", "-0.014 / -0.013", "-0.050 / -0.062", "-0.078 / -0.152"]),
    table_row(["1.20", "0.039 / 0.003", "-0.006 / -0.006", "-0.022 / -0.028", "-0.034 / -0.068"]),
]
stbl = Table(summary_data, colWidths=[0.6*inch, 1.35*inch, 1.35*inch, 1.35*inch, 1.35*inch])
stbl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a2a5e")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f2fa")]),
]))
story.append(stbl)
story.append(Spacer(1, 10))
p("<b>Na=1e15</b>: excellent match, within 5-12% everywhere (normal graph-reading "
  "precision). <b>Na=1e16</b>: our values consistently ~24-25% larger in magnitude than "
  "the paper's own curve, at every W tested. <b>Na=1e17</b>: consistently ~85-100% "
  "larger (roughly double), same direction, growing with doping. <b>Na=1e14</b>: our "
  "curve saturates near +0.03V while the paper's reaches +0.18V &mdash; ~12&times; too "
  "small, the opposite direction, likely because W<sub>c</sub>=t<sub>d</sub>&minus;t<sub>1</sub>"
  " &asymp; 1.74&#181;m here exceeds t<sub>f</sub>=0.7&#181;m, probably outside the "
  "Case II lateral-wing model's intended validity range (not independently verified the "
  "way Case I was in this report).")
story.append(PageBreak())

h2("5.1 The smoking gun: the paper's own formula reproduces its own figure")
p("Recomputing Fig. 10's Case I curves (Na=1e16, 1e17) using the paper's OWN Eq. 11 "
  "series (not our FD/Green's-function values) reproduces the digitized paper curve "
  "almost exactly &mdash; far better than our independently-verified numbers do:")
fig(f"{R}/deepverif_fig10_3way.png",
    "Fig. 3: Digitized points from the paper's own Fig. 10 (black) sit almost exactly "
    "on the curve computed from the paper's own Eq. 11 formula (orange dashed) &mdash; "
    "not on our FD/Green's-function curve (blue solid).")
p("This is the direct answer to \"does matching the paper mean the paper is right\": "
  "<b>no</b>. The published figure and Eq. 11 are not two independent pieces of "
  "evidence &mdash; the figure was (almost certainly) computed FROM Eq. 11, so matching "
  "one is just matching the other. The genuinely independent comparison is FD vs. "
  "Green's function (Section 3), which share no code, no conformal map, and no common "
  "derivation step beyond the stated physics in Eq. 6 &mdash; and those two agree with "
  "each other to &lt;0.1% while disagreeing with Eq. 11 by the same ~2-2.7&times; factor "
  "seen again here in the Fig. 10 comparison (1.24&times; at Na=1e16, up to ~2&times; at "
  "Na=1e17, growing with t<sub>d</sub> consistent with the per-term analysis in Sec. 4).")
p("<b>Epistemic structure:</b>")
bullets([
    "Paper's Eq. 11 &harr; Paper's Fig. 10: mutually self-consistent (one formula, "
    "drawn twice) &mdash; NOT independent confirmation of each other.",
    "FD solve &harr; Green's function: mutually self-consistent, from genuinely "
    "independent derivations &mdash; this IS meaningful corroboration.",
    "Group 1 vs. Group 2: disagree consistently, in the same direction, growing with "
    "t<sub>d</sub>, across every test point checked in this report.",
])
p("This does not prove Eq. 11 is wrong with absolute certainty (both independent "
  "methods could in principle share an undetected common flaw), but it substantially "
  "shifts the burden of proof: it is no longer \"our reproduction disagrees with the "
  "paper,\" it is \"two independent methods agree with each other and disagree with a "
  "single-source formula that, unsurprisingly, also agrees with its own plot.\"")

# ================================================================== 6. Conclusions
h1("6. Conclusions")
bullets([
    "A second, fully independent derivation (Green's function/eigenfunction expansion) "
    "confirms the FD ground truth to &lt;0.1% agreement, using no conformal map and no "
    "shared code with the FD solver.",
    "The paper's Eq. 11, even after two dimensional-analysis fixes, disagrees with BOTH "
    "independent methods by a consistent, doping-dependent factor (~1.24-2.7&times; in "
    "the cases checked).",
    "A per-term diagnostic localizes the error to an argument/phase-level issue (not a "
    "scalar prefactor, not an even/odd-n restriction) &mdash; confirmed via a resonance "
    "at n=multiples-of-7 tied to this device's t1/tf=5/7 ratio &mdash; but the exact "
    "term-by-term fix was not found; doing so would require re-deriving Eq. 7-11 from "
    "the stated Poisson-kernel construction from scratch.",
    "Pixel-calibrated digitization of the paper's own Fig. 10 shows the paper's "
    "published curve is reproduced almost exactly by the paper's OWN Eq. 11 formula "
    "&mdash; meaning the figure is not independent validation of that formula, just a "
    "second rendering of it. The genuinely independent cross-check (FD vs. Green's "
    "function) points the other way.",
    "Practical takeaway: this codebase's A, B (Case I) values should be trusted over "
    "the paper's literal Eq. 11 for any quantitative use, on the strength of two "
    "independent confirmations rather than one method alone.",
])

doc = SimpleDocTemplate(OUT, pagesize=letter,
                         topMargin=0.7*inch, bottomMargin=0.7*inch,
                         leftMargin=0.75*inch, rightMargin=0.75*inch)
doc.build(story)
print("Wrote", OUT)
