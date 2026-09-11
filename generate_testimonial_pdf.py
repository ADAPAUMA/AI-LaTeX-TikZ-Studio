import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from datetime import date

pdf_filename = "Student_Testimonial_Adapa_Uma_Siva_Sankar.pdf"
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=A4,
    rightMargin=50,
    leftMargin=50,
    topMargin=45,
    bottomMargin=45
)

# Color Palette
col_dark_navy = colors.HexColor("#0f172a")
col_royal_blue = colors.HexColor("#1e3a8a")
col_brand_blue = colors.HexColor("#2563eb")
col_light_bg = colors.HexColor("#f1f5f9")
col_border = colors.HexColor("#cbd5e1")
col_text = colors.HexColor("#1e293b")
col_sub_text = colors.HexColor("#475569")
col_green = colors.HexColor("#065f46")
col_light_green = colors.HexColor("#f0fdf4")
col_green_border = colors.HexColor("#16a34a")
col_gold = colors.HexColor("#92400e")
col_light_gold = colors.HexColor("#fffbeb")
col_gold_border = colors.HexColor("#d97706")

styles = getSampleStyleSheet()

def para(text, style): return Paragraph(text, style)

# Define reusable styles
def style(name, font='Helvetica', size=10, color=col_text, align=TA_LEFT, bold=False, spaceBefore=0, spaceAfter=6, leading=None):
    return ParagraphStyle(
        name,
        fontName='Helvetica-Bold' if bold else font,
        fontSize=size,
        leading=leading or (size * 1.45),
        textColor=color,
        alignment=align,
        spaceBefore=spaceBefore,
        spaceAfter=spaceAfter,
    )

title_s     = style('title', size=20, color=col_royal_blue, align=TA_CENTER, bold=True, spaceAfter=3)
subtitle_s  = style('subtitle', size=11, color=col_brand_blue, align=TA_CENTER, spaceAfter=14)
section_s   = style('section', size=13, color=col_royal_blue, bold=True, spaceBefore=14, spaceAfter=5)
body_s      = style('body', size=10.5, color=col_text, align=TA_JUSTIFY, spaceAfter=8, leading=16)
bullet_s    = style('bullet', size=10, color=col_text, spaceAfter=5, leading=15)
label_s     = style('label', size=10, color=col_royal_blue, bold=True)
val_s       = style('val', size=10, color=col_text)
small_s     = style('small', size=9, color=col_sub_text, spaceAfter=4)
footer_s    = style('footer', size=9, color=col_sub_text, align=TA_CENTER)
highlight_s = style('highlight', size=10, color=col_text, align=TA_JUSTIFY, spaceAfter=7, leading=15)
notice_s    = style('notice', size=10, color=col_gold, align=TA_JUSTIFY, spaceAfter=5, leading=15)

story = []

# ── HEADER BLOCK ──────────────────────────────────────────────────────────────
story.append(para("IBM AICTE INTERNSHIP PROGRAM — BATCH 2026", subtitle_s))
story.append(para("STUDENT TESTIMONIAL & PROJECT SUBMISSION DOCUMENT", title_s))
story.append(HRFlowable(width="100%", thickness=2.5, color=col_brand_blue, spaceBefore=4, spaceAfter=18))

# ── NOTICE FROM FACULTY / COORDINATOR ─────────────────────────────────────────
notice_table_data = [[
    Paragraph("📢  Official Notice from Project Coordinator", style('nh', size=11, color=col_gold, bold=True, spaceAfter=0)),
]]
notice_body = [
    [Paragraph(
        "Good evening, Students. Please continue working on your project as it is a crucial evaluation metric for the AICTE Batch — every student must complete it.<br/><br/>"
        "Select <b>any one problem statement</b> from the given document and develop the project <b>using IBM Bob only</b>. "
        "Your presentation must include <b>at least 7–8 screenshots</b> clearly demonstrating the project and its implementation.<br/><br/>"
        "Include a <b>working GitHub link</b> with an accessible repository containing all relevant project files and source code. "
        "Prepare the PPT <b>strictly using the given template</b> — AI-generated PPTs or alternative templates will not be accepted.<br/><br/>"
        "<b>Project Submission Deadline: 11 September 2026.</b> Kindly complete and submit your project on or before the deadline.",
        notice_s
    )]
]

notice_box = Table([[Paragraph(
    "📢  <b>Official Notice from Project Coordinator</b><br/><br/>"
    "Good evening, Students. Please continue working on your project as it is a crucial evaluation metric for the AICTE Batch — every student must complete it.<br/><br/>"
    "Select <b>any one problem statement</b> from the given document and develop the project <b>using IBM Bob only</b>. "
    "Your presentation must include <b>at least 7–8 screenshots</b> clearly demonstrating the project and its implementation.<br/><br/>"
    "Include a <b>working GitHub link</b> with an accessible repository containing all relevant project files and source code. "
    "Prepare the PPT <b>strictly using the provided template</b> — AI-generated PPTs or alternative templates will not be accepted.<br/><br/>"
    "<b>Project Submission Deadline: 11 September 2026.</b> Kindly complete and submit your project on or before the deadline.",
    style('noticeinner', size=10.5, color=col_gold, align=TA_JUSTIFY, spaceAfter=0, leading=16)
)]])
notice_box.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), col_light_gold),
    ('BOX', (0,0), (-1,-1), 1.5, col_gold_border),
    ('PADDING', (0,0), (-1,-1), 14),
    ('BORDERPADDING', (0,0), (-1,-1), 4),
]))
story.append(notice_box)
story.append(Spacer(1, 18))

# ── STUDENT IDENTITY TABLE ────────────────────────────────────────────────────
story.append(para("1.  Student Information", section_s))

info_data = [
    [para("Student Name", label_s),      para("Adapa Uma Siva Sankar", val_s)],
    [para("Student ID", label_s),        para("STU67ff0b8cbec7c1744767884", val_s)],
    [para("College", label_s),           para("V.S.M. College Of Engineering, Ramachandrapuram", val_s)],
    [para("Branch & Year", label_s),     para("B.Tech — CSE (Data Science) / 2026", val_s)],
    [para("Project Domain", label_s),    para("Education & AI Developer Software Tools", val_s)],
    [para("Project Title", label_s),     para("AI-Powered LaTeX TikZ Diagram Generator & Chatbot Studio", val_s)],
    [para("Submission Deadline", label_s), para("11 September 2026", style('deadline', size=10, color=colors.HexColor('#dc2626'), bold=True))],
    [para("GitHub Repository", label_s), para("https://github.com/ADAPAUMA/AI-LaTeX-TikZ-Studio", val_s)],
]

info_table = Table(info_data, colWidths=[130, 370])
info_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), col_light_bg),
    ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#e8f0fe")),
    ('PADDING', (0,0), (-1,-1), 9),
    ('LINEBELOW', (0,0), (-1,-2), 0.5, col_border),
    ('BOX', (0,0), (-1,-1), 1.2, col_brand_blue),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(info_table)
story.append(Spacer(1, 14))

# ── SECTION 2: EXECUTIVE SUMMARY ─────────────────────────────────────────────
story.append(para("2.  Executive Summary", section_s))
story.append(para(
    "This document serves as the official student testimonial for the <b>IBM AICTE Internship Program (Batch 2026)</b>. "
    "The selected problem statement addresses the challenge faced by academic researchers, professors, and engineering students "
    "who spend hours manually authoring complex LaTeX TikZ diagram code for publication-grade academic figures. "
    "The proposed solution, developed entirely using <b>IBM Bob</b>, <b>IBM watsonx.ai</b>, and <b>IBM Watson Assistant</b>, "
    "resolves this friction through an intelligent, conversational AI-driven diagram generation studio.",
    body_s
))

# ── SECTION 3: IBM BOB IMPLEMENTATION ────────────────────────────────────────
story.append(para("3.  IBM Bob Project Implementation", section_s))
story.append(para(
    "The project was built exclusively using the <b>IBM Bob multi-agent orchestration platform</b>, leveraging the following IBM technologies:",
    body_s
))

tech_items = [
    ("IBM Bob Platform", "Designed, visually modeled, and orchestrated the multi-agent AI workflow. All five agents (Chatbot Studio, TikZ Generator, Syntax Validator, Smart Fallback Engine, and Rendering Studio) are coordinated through IBM Bob's visual pipeline builder."),
    ("IBM Watson Assistant (WebChat)", "Integrated a conversational AI agent (Integration ID: bad150a7-6816-40db-9249-10be96c432f4, Region: au-syd) into the Streamlit web dashboard to facilitate natural language query resolution and diagram guidance."),
    ("IBM Granite LLM", "Leveraged ibm/granite-13b-instruct-v2 via IBM watsonx.ai REST API for multi-agent reasoning, LaTeX TikZ code synthesis, context-aware auto-correction, and diagram explanation generation."),
    ("Streamlit Web Dashboard", "Built an interactive 5-tab AI Studio with IBM Watson WebChat integration, Granite AI Chatbot, pdflatex/pdf2svg vector rendering, and a Template Gallery."),
    ("GitHub Repository", "All source code, documentation, requirements, and submission PPT are publicly accessible at: https://github.com/ADAPAUMA/AI-LaTeX-TikZ-Studio"),
]

for title, desc in tech_items:
    story.append(para(f"<b>▸  {title}:</b>  {desc}", bullet_s))

story.append(Spacer(1, 6))

# ── SECTION 4: PPT SCREENSHOTS CHECKLIST ─────────────────────────────────────
story.append(para("4.  PPT Screenshot Coverage (8 Demonstrations)", section_s))

shots = [
    "Screenshot 1 — IBM Bob Multi-Agent Architecture Blueprint",
    "Screenshot 2 — IBM Watson Assistant WebChat Dashboard (Chatbot active on Streamlit)",
    "Screenshot 3 — AI Chatbot Studio: User Query & CNN Architecture Diagram Generation",
    "Screenshot 4 — IBM Bob Agent Workflow Sequence (Conversation Steps in IBM Watson UI)",
    "Screenshot 5 — TikZ Diagram Code Output & LaTeX Validation Report",
    "Screenshot 6 — Streamlit 3D Glassmorphic Dashboard (Header, Cards, Integration Status)",
    "Screenshot 7 — Token Usage & IBM Granite LLM Model Inference Evidence",
    "Screenshot 8 — GitHub Repository: Project Files, README, and Commit History",
]
for s in shots:
    story.append(para(f"  ✅  {s}", bullet_s))

story.append(Spacer(1, 8))

# ── SECTION 5: PERSONAL TESTIMONIAL ──────────────────────────────────────────
story.append(para("5.  Personal Testimonial", section_s))
story.append(para(
    "Working on this IBM AICTE Internship project has been one of the most rewarding and intellectually stimulating experiences of my academic journey. "
    "Being able to design, build, and deploy a full-stack AI studio from scratch — backed by IBM's enterprise-grade cloud infrastructure — has given me immense confidence and practical understanding of real-world AI application development.",
    body_s
))
story.append(para(
    "The experience of working with <b>IBM Bob's visual multi-agent orchestration</b>, <b>IBM Watson Assistant's NLU-powered WebChat</b>, and <b>IBM Granite's large language model capabilities</b> has been transformative. "
    "I am sincerely grateful to IBM and AICTE for providing this incredible opportunity, and I look forward to continuing to build AI-powered solutions that make a meaningful difference in the academic community.",
    body_s
))

# ── FOOTER ────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 16))
story.append(HRFlowable(width="100%", thickness=1, color=col_border, spaceAfter=10))

sig_data = [
    [
        para("<b>Student Signature:</b><br/>Adapa Uma Siva Sankar<br/>STU67ff0b8cbec7c1744767884", style('sig', size=9.5, color=col_royal_blue, spaceAfter=0, leading=14)),
        para("<b>Institution:</b><br/>V.S.M. College Of Engineering<br/>Ramachandrapuram", style('sigm', size=9.5, color=col_text, spaceAfter=0, leading=14, align=TA_CENTER)),
        para(f"<b>Date:</b><br/>10 September 2026<br/>Submission by 11 Sep 2026", style('sigd', size=9.5, color=col_text, spaceAfter=0, leading=14, align=TA_RIGHT)),
    ]
]
sig_table = Table(sig_data, colWidths=[175, 200, 125])
sig_table.setStyle(TableStyle([
    ('PADDING', (0,0), (-1,-1), 4),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
]))
story.append(sig_table)

story.append(Spacer(1, 10))
story.append(para("This document was prepared in accordance with IBM AICTE Internship Program guidelines. | IBM Watson Assistant · IBM watsonx.ai · IBM Granite LLM · IBM Bob", footer_s))

doc.build(story)
print("PDF successfully generated: " + pdf_filename)
