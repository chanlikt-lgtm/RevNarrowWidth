"""Condensed PDF summary of the Li 1990 conformal-mapping narrow-channel
reproduction -- a short companion to the full 11-page technical report
(narrow_channel_semi_recessed_report.pdf) and the slide deck
(li1990_conformal_mapping_summary.pptx)."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, ListFlowable, ListItem,
)
from reportlab.lib import colors

R = r"E:\claude\RAG\reports"
OUT = f"{R}/li1990_conformal_mapping_summary.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1c", parent=styles["Heading1"], textColor=colors.HexColor("#1a2a5e")))
styles.add(ParagraphStyle("H2c", parent=styles["Heading2"], textColor=colors.HexColor("#1a2a5e")))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14.5))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8.5, leading=11,
                          textColor=colors.HexColor("#444444"), alignment=TA_CENTER))
styles.add(ParagraphStyle("TitleC", parent=styles["Title"], textColor=colors.HexColor("#1a2a5e")))

story = []

def h1(t): story.append(Paragraph(t, styles["H1c"])); story.append(Spacer(1, 6))
def h2(t): story.append(Paragraph(t, styles["H2c"])); story.append(Spacer(1, 4))
def p(t): story.append(Paragraph(t, styles["Body"])); story.append(Spacer(1, 6))
def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(t, styles["Body"]), leftIndent=6) for t in items],
        bulletType="bullet", start="•", leftIndent=14))
    story.append(Spacer(1, 8))
def fig(path, caption, width=5.4*inch):
    img = Image(path, width=width, height=width*0.72)
    story.append(img)
    story.append(Paragraph(caption, styles["Caption"]))
    story.append(Spacer(1, 10))

# ---------------------------------------------------------------- Title
story.append(Spacer(1, 40))
story.append(Paragraph("Conformal-Mapping Summary", styles["TitleC"]))
story.append(Paragraph(
    "The Narrow-Channel Effect in MOSFET's with Semi-Recessed Oxide Structures",
    styles["Heading2"]))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "Li, Hong, Cheng &amp; Chan, <i>IEEE Trans. Electron Devices</i>, vol. 37, no. 3, "
    "pp. 692-701, March 1990 &mdash; condensed companion to the full technical report "
    "(narrow_channel_semi_recessed_report.pdf) and slide deck "
    "(li1990_conformal_mapping_summary.pptx)", styles["Normal"]))
story.append(Spacer(1, 30))

# ---------------------------------------------------------------- 1. Method
h1("1. Method: Conformal Mapping of the Field-Oxide Region")
p("A semi-recessed field-oxide MOSFET's narrow-channel behavior is governed by the 2-D "
  "electrostatics of the field-oxide cross-section next to the gate. Rather than solving "
  "&#8711;&#178;&#966;=0 directly on the awkward corner geometry, the paper maps the "
  "semi-infinite half-strip domain onto the upper half-plane via")
p("<b>u + iv = cos[&#960;(ix &#8722; y)/t<sub>f</sub>]</b>,")
p("turning the problem into a classical Poisson-kernel / Schwarz-integral boundary-value "
  "problem, solvable as a Fourier series in n. The regime depends on whether the channel "
  "depletion depth t<sub>d</sub> is below or above the recess depth t<sub>1</sub>:")
bullets([
    "<b>Case I</b> (t_d &lt; t_1): depletion confined to the sidewall &rarr; inverse "
    "narrow-width effect (&Delta;V_th &lt; 0).",
    "<b>Case II</b> (t_d &gt; t_1): depletion spills laterally under the field oxide "
    "(quarter-circle wing, radius W_c=t_d&minus;t_1) &rarr; conventional effect "
    "(&Delta;V_th &gt; 0).",
    "Fully-recessed (t_1=t_f&minus;t_g) and non-recessed (t_1&rarr;0) structures fall out "
    "of the same formulas at limiting t_1 &mdash; no separate model needed.",
])
p("The resulting series coefficients A,B (Case I) or A&prime;,B&prime; (Case II) feed "
  "V<sub>th</sub>(W) = &#966;<sub>ms</sub> + 2&#966;<sub>f</sub>(1+a/W)/(1+b/W) + "
  "(Q&prime;/C<sub>ox</sub>)/(1+b/W), with a=2t<sub>g</sub>(B&minus;A), b=&minus;2t<sub>g</sub>A.")

# ---------------------------------------------------------------- 2. Verification
h1("2. Verification: Beyond Dimensional Analysis")
p("Dimensional analysis alone caught two real transcription issues in the paper's printed "
  "series (Eq. 11): a unit-inconsistent prefactor in A, and a missing &#189; factor in "
  "sin(nkt<sub>g</sub>). <b>Both fixes together were still not sufficient</b> &mdash; an "
  "independent finite-difference (FD) solve of the actual boundary-value problem (5-point "
  "Laplacian, sparse direct solve) disagreed with the corrected series, including in B, "
  "whose prefactor was never ambiguous.")
p("The FD solver was validated two ways that do not depend on the paper's series at all:")
bullets([
    "<b>Sharp-step analytic limit</b> (t_d,t_g&rarr;0): the FD solution converges to a "
    "hand-derived closed form as the boundary condition simplifies to a step function "
    "(-0.4930 &rarr; -0.4659 vs. analytic -0.4652).",
    "<b>Case I/II boundary continuity</b> (t_d&rarr;t_1): two independently-coded BVPs "
    "must agree in the shared limit &mdash; this check caught and fixed a real bug in the "
    "Case II lateral-wing flux integration bound.",
])
p("Given this, the FD solve &mdash; not the literal Eq. 11/17 series &mdash; is used as "
  "the verified ground truth throughout. The remaining series discrepancy's exact root "
  "cause is <b>reported as unresolved</b>, not forced to a clean fix.")

story.append(PageBreak())

# ---------------------------------------------------------------- 3. Results
h1("3. Reproduced Result (Fig. 5)")
fig(f"{R}/li1990_fig5_repro.png",
    "Backgate-bias sweep, semi-recessed (t1=0.5 &#181;m). Case I (Vbg=0,-1V) shows the "
    "inverse effect; Case II (Vbg=-2,-4,-6V) shows the conventional effect &mdash; matches "
    "the paper's own Case grouping exactly.")

h1("4. Cross-Check vs. Akers (1986)")
fig(f"{R}/li1990_vs_akers1986.png",
    "Left: Li's fully-recessed Case I limit vs. Akers' single-regime model &mdash; same "
    "order-of-magnitude length scale (a=42.3 nm, b=71.8 nm vs. F=91 nm) from independent "
    "derivations. Right: Li's model additionally predicts a bias-driven Case I&rarr;Case II "
    "sign reversal that Akers' model cannot represent.")

h1("5. Bottom Line")
bullets([
    "All 8 paper figures (Figs. 5-12) reproduced, matching qualitative trends and Case "
    "groupings.",
    "Fully-recessed length scales revised, post-FD-verification, from a=103 nm/b=124 nm "
    "(flawed series) to <b>a=42.3 nm, b=71.8 nm</b>.",
    "Full technical detail in narrow_channel_semi_recessed_report.pdf; slide-deck version "
    "in li1990_conformal_mapping_summary.pptx.",
])

doc = SimpleDocTemplate(OUT, pagesize=letter,
                         topMargin=0.7*inch, bottomMargin=0.7*inch,
                         leftMargin=0.75*inch, rightMargin=0.75*inch)
doc.build(story)
print("Wrote", OUT)
