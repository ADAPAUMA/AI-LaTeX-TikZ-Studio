from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

pdf_filename = "Student_Testimonial_Adapa_Uma_Siva_Sankar.pdf"

doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=A4,
    rightMargin=55, leftMargin=55,
    topMargin=50, bottomMargin=50
)

# Colors
navy   = colors.HexColor("#0f172a")
royal  = colors.HexColor("#1e3a8a")
brand  = colors.HexColor("#2563eb")
light  = colors.HexColor("#f1f5f9")
border = colors.HexColor("#cbd5e1")
text   = colors.HexColor("#1e293b")
sub    = colors.HexColor("#475569")
eblue  = colors.HexColor("#e8f0fe")

def P(txt, **kw):
    defaults = dict(fontName='Helvetica', fontSize=10.5, leading=16,
                    textColor=text, alignment=TA_LEFT, spaceBefore=0, spaceAfter=6)
    defaults.update(kw)
    return Paragraph(txt, ParagraphStyle('x', **defaults))

story = []

# ── TOP HEADER ────────────────────────────────────────────────────────────────
story.append(P("IBM AICTE INTERNSHIP PROGRAM — BATCH 2026",
               fontName='Helvetica-Bold', fontSize=11, textColor=brand,
               alignment=TA_CENTER, spaceAfter=4))
story.append(P("STUDENT TESTIMONIAL &amp; PROJECT SUBMISSION DOCUMENT",
               fontName='Helvetica-Bold', fontSize=18, textColor=royal,
               alignment=TA_CENTER, spaceAfter=6))
story.append(HRFlowable(width="100%", thickness=2.5, color=brand, spaceBefore=2, spaceAfter=20))

# ── SECTION 1: STUDENT INFO TABLE ────────────────────────────────────────────
story.append(P("1.  Student Information",
               fontName='Helvetica-Bold', fontSize=13, textColor=royal,
               spaceBefore=0, spaceAfter=8))

def lbl(t): return P(f"<b>{t}</b>", fontSize=10, textColor=royal, spaceAfter=0)
def val(t): return P(t, fontSize=10, textColor=text, spaceAfter=0)
def val_red(t): return P(f"<b>{t}</b>", fontSize=10, textColor=colors.HexColor("#dc2626"), spaceAfter=0)

info = [
    [lbl("Student Name"),        val("Adapa Uma Siva Sankar")],
    [lbl("Student ID"),          P("<b>STU67ff0b8cbec7c1744767884</b>", fontSize=10,
                                    textColor=colors.HexColor("#166534"), spaceAfter=0)],
    [lbl("College"),             val("V.S.M. College Of Engineering, Ramachandrapuram")],
    [lbl("Branch &amp; Year"),   val("B.Tech — CSE (Data Science) / 2026")],
    [lbl("Project Domain"),      val("Education &amp; AI Developer Software Tools")],
    [lbl("Project Title"),       val("AI-Powered LaTeX TikZ Diagram Generator &amp; Chatbot Studio")],
    [lbl("Submission Deadline"), val_red("11 September 2026")],
    [lbl("GitHub Repository"),   val("https://github.com/ADAPAUMA/AI-LaTeX-TikZ-Studio")],
]

tbl = Table(info, colWidths=[140, 355])
tbl.setStyle(TableStyle([
    ('BACKGROUND',  (0,0), (-1,-1), light),
    ('BACKGROUND',  (0,0), (0,-1),  eblue),
    ('PADDING',     (0,0), (-1,-1), 9),
    ('LINEBELOW',   (0,0), (-1,-2), 0.5, border),
    ('BOX',         (0,0), (-1,-1), 1.5, brand),
    ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(tbl)
story.append(Spacer(1, 18))

# ── SECTION 2: EXECUTIVE SUMMARY ─────────────────────────────────────────────
story.append(P("2.  Executive Summary",
               fontName='Helvetica-Bold', fontSize=13, textColor=royal,
               spaceBefore=0, spaceAfter=7))
story.append(P(
    "This document serves as the official student testimonial for the "
    "<b>IBM AICTE Internship Program (Batch 2026)</b>. The selected problem statement addresses "
    "the difficulty academic researchers, professors, and engineering students face when manually "
    "authoring complex LaTeX TikZ diagram code for publication-grade figures. The solution, built "
    "<b>entirely with IBM Bob, IBM watsonx.ai, and IBM Watson Assistant</b>, provides an "
    "intelligent, conversational AI-driven diagram generation studio that removes this friction.",
    alignment=TA_JUSTIFY, spaceAfter=18))

# ── SECTION 3: IBM BOB IMPLEMENTATION ────────────────────────────────────────
story.append(P("3.  IBM Bob Project Implementation",
               fontName='Helvetica-Bold', fontSize=13, textColor=royal,
               spaceBefore=0, spaceAfter=7))
story.append(P(
    "The project was built exclusively using the <b>IBM Bob multi-agent orchestration platform</b>, "
    "leveraging the following IBM technologies:",
    alignment=TA_JUSTIFY, spaceAfter=8))

bullets = [
    ("<b>IBM Bob Platform</b>",
     "Designed and orchestrated the multi-agent AI workflow — Chatbot Studio, TikZ Generator, "
     "Syntax Validator, Smart Fallback Engine, and Rendering Studio — using IBM Bob's visual pipeline builder."),
    ("<b>IBM Watson Assistant (WebChat)</b>",
     "Integrated a conversational AI agent (Integration ID: bad150a7-6816-40db-9249-10be96c432f4, "
     "Region: au-syd) into the Streamlit dashboard for natural-language query resolution and diagram guidance."),
    ("<b>IBM Granite LLM</b>",
     "Used ibm/granite-13b-instruct-v2 via IBM watsonx.ai REST API for multi-agent reasoning, "
     "TikZ code synthesis, auto-correction, and diagram explanation generation."),
    ("<b>Streamlit Web Dashboard</b>",
     "Built an interactive 5-tab AI studio with Watson WebChat integration, Granite AI Chatbot, "
     "pdflatex/pdf2svg vector rendering, and a Template Gallery."),
    ("<b>GitHub Repository</b>",
     "All source code, documentation, requirements, and submission PPT are publicly accessible at: "
     "https://github.com/ADAPAUMA/AI-LaTeX-TikZ-Studio"),
]

for title, desc in bullets:
    story.append(P(f"  {title}:   {desc}",
                   fontSize=10.5, leading=15, spaceAfter=7,
                   alignment=TA_JUSTIFY))

story.append(Spacer(1, 10))

# ── SECTION 4: PERSONAL TESTIMONIAL ──────────────────────────────────────────
story.append(P("4.  Personal Testimonial",
               fontName='Helvetica-Bold', fontSize=13, textColor=royal,
               spaceBefore=0, spaceAfter=7))

# Highlight box
box_text = (
    "Working on this IBM AICTE Internship project has been one of the most rewarding and "
    "intellectually stimulating experiences of my academic journey. Building a full-stack AI studio "
    "from scratch — backed by IBM's enterprise-grade cloud infrastructure — has given me immense "
    "confidence and practical understanding of real-world AI application development.<br/><br/>"
    "The experience of working with IBM Bob's visual multi-agent orchestration, IBM Watson "
    "Assistant's NLU-powered WebChat, and IBM Granite's large language model capabilities has been "
    "truly transformative. I am sincerely grateful to IBM and AICTE for providing this incredible "
    "opportunity, and I look forward to continuing to build AI-powered solutions that make a "
    "meaningful difference in the academic community."
)

box = Table([[P(box_text, fontSize=10.5, leading=16, alignment=TA_JUSTIFY,
                textColor=colors.HexColor("#1e3a8a"), spaceAfter=0)]])
box.setStyle(TableStyle([
    ('BACKGROUND',     (0,0), (-1,-1), eblue),
    ('BOX',            (0,0), (-1,-1), 1.5, brand),
    ('PADDING',        (0,0), (-1,-1), 14),
]))
story.append(box)
story.append(Spacer(1, 20))

# ── FOOTER / SIGNATURE ────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=border, spaceAfter=12))

sig = Table([[
    P("<b>Student Signature:</b><br/>Adapa Uma Siva Sankar<br/>STU67ff0b8cbec7c1744767884",
      fontSize=9.5, leading=14, textColor=royal, spaceAfter=0),
    P("<b>Institution:</b><br/>V.S.M. College Of Engineering<br/>Ramachandrapuram",
      fontSize=9.5, leading=14, textColor=text, alignment=TA_CENTER, spaceAfter=0),
    P("<b>Date:</b><br/>10 September 2026<br/>Deadline: 11 Sep 2026",
      fontSize=9.5, leading=14, textColor=text, alignment=TA_RIGHT, spaceAfter=0),
]], colWidths=[175, 200, 125])
sig.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),4)]))
story.append(sig)

story.append(Spacer(1, 10))
story.append(P(
    "This document was prepared in accordance with IBM AICTE Internship Program guidelines.  |  "
    "IBM Watson Assistant  |  IBM watsonx.ai  |  IBM Granite LLM  |  IBM Bob",
    fontSize=8.5, textColor=sub, alignment=TA_CENTER, spaceAfter=0))

doc.build(story)
print("PDF created: " + pdf_filename)
