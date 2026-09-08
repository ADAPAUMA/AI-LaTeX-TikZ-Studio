# AI-Powered LaTeX TikZ Diagram Generator

> Convert natural-language descriptions into publication-ready LaTeX / TikZ diagrams using IBM Granite.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [File Descriptions](#3-file-descriptions)
4. [Prerequisites](#4-prerequisites)
5. [IBM Watson Studio / watsonx.ai Setup](#5-ibm-watson-studio--watsonxai-setup)
6. [Installation](#6-installation)
7. [Running the Application](#7-running-the-application)
8. [Example Prompts](#8-example-prompts)
9. [Example Generated TikZ Output](#9-example-generated-tikz-output)
10. [Testing Procedure](#10-testing-procedure)
11. [Error-Handling Strategy](#11-error-handling-strategy)
12. [Future Enhancements](#12-future-enhancements)

---

## 1. Project Overview

This application provides a **Streamlit web interface** that accepts a plain-English description of any academic diagram and produces clean, compilable **LaTeX / TikZ code** ready for insertion into research papers, theses, and conference submissions (IEEE, ACM, Springer, Elsevier).

### Workflow

```
Natural Language Description
         ↓
  Prompt Engineering
  (prompt_templates.py)
         ↓
  IBM Granite LLM
  (granite_client.py)
         ↓
  LaTeX / TikZ Extraction
  (tikz_generator.py)
         ↓
  Static Validation
  (validator.py)
         ↓
  Auto-Correction (if needed)
  (tikz_generator.py → granite_client.py)
         ↓
  Optional PDF / SVG Rendering
  (renderer.py)
         ↓
  Publication-Ready Output
  (Streamlit UI — app.py)
```

---

## 2. Architecture

```
tikz_generator_app/
│
├── app.py                  ← Streamlit UI (entry point)
├── granite_client.py       ← IBM watsonx.ai REST API wrapper
├── tikz_generator.py       ← Generation / refinement orchestrator
├── prompt_templates.py     ← All LLM prompt templates
├── validator.py            ← Heuristic TikZ code validator
├── renderer.py             ← Optional pdflatex / SVG renderer
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable template
└── README.md               ← This file
```

---

## 3. File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit front-end. Manages session state, renders all UI sections (generate, output tabs, refinement, history). |
| `granite_client.py` | Authenticates against IBM Cloud IAM, exchanges the API key for a bearer token, and sends generation requests to the watsonx.ai `/ml/v1/text/generation` endpoint. Handles 401 token expiry with automatic retry. |
| `tikz_generator.py` | Orchestrates the pipeline: calls `prompt_templates`, sends requests via `granite_client`, extracts code from model output, runs `validator`, and optionally sends a correction prompt. |
| `prompt_templates.py` | Contains all prompt templates: generation, refinement, extraction, correction, and explanation. Includes few-shot examples and a diagram-type auto-detector. |
| `validator.py` | Statically checks TikZ code for: empty output, unbalanced braces, missing `tikzpicture` environment, duplicate node names, undefined node references, missing TikZ libraries, semicolon issues. Returns a `ValidationResult` with errors and warnings. |
| `renderer.py` | Optionally compiles generated code with `pdflatex` in a temporary directory and converts the PDF to SVG using `pdf2svg` or `Inkscape`. Degrades gracefully when these tools are absent. |
| `requirements.txt` | Minimal Python package list: `streamlit`, `requests`, `python-dotenv`. |
| `.env.example` | Template for the three required environment variables plus the optional model override. |

---

## 4. Prerequisites

### Python

- Python **3.10+** (type annotations use `X | Y` union syntax)

### Python packages

```bash
pip install -r requirements.txt
```

### Optional — local PDF/SVG rendering

| Tool | Install |
|------|---------|
| pdflatex | [TeX Live](https://tug.org/texlive/) · [MiKTeX](https://miktex.org/) · [MacTeX](https://tug.org/mactex/) |
| pdf2svg | `sudo apt install pdf2svg` (Debian/Ubuntu) |
| Inkscape | [inkscape.org](https://inkscape.org) (fallback SVG converter) |

> **Without these tools**, the application still works fully — you simply compile the generated `.tex` file using [Overleaf](https://overleaf.com) or a local LaTeX editor.

---

## 5. IBM Watson Studio / watsonx.ai Setup

### Step 1 — Create an IBM Cloud account

1. Go to <https://cloud.ibm.com> and create a free account.

### Step 2 — Provision Watson Studio

1. In IBM Cloud → Catalog, search for **Watson Studio**.
2. Select the **Lite** (free) plan and click **Create**.

### Step 3 — Provision watsonx.ai Runtime

1. In IBM Cloud → Catalog, search for **Watson Machine Learning** (the watsonx.ai runtime).
2. Select your region (e.g. `us-south`) and create an instance.

### Step 4 — Create a watsonx.ai Project

1. Open <https://dataplatform.cloud.ibm.com> (Watson Studio).
2. Click **New project → Create an empty project**.
3. Associate the **Watson Machine Learning** service you just created.
4. Copy the **Project ID** from Manage → General.

### Step 5 — Generate an IBM Cloud API key

1. IBM Cloud → Manage → Access (IAM) → API keys.
2. Click **Create an IBM Cloud API key**, copy it immediately.

### Step 6 — Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```
WATSONX_API_KEY=<your api key>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=<your project id>
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

---

## 6. Installation

```bash
# Clone or download the project
cd tikz_generator_app

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your IBM credentials
```

---

## 7. Running the Application

```bash
streamlit run app.py
```

Open the URL printed by Streamlit (typically <http://localhost:8501>).

---

## 8. Example Prompts

### Machine Learning Pipeline (horizontal)

```
Create a machine learning data pipeline with four stages: Data Ingestion,
Data Preprocessing, IBM Granite Model Training, and Model Evaluation and
Deployment. Arrange them horizontally from left to right with arrows.
```

### CNN Architecture (vertical)

```
Draw a convolutional neural network with the following layers arranged
vertically: Input Image (224×224), Conv Layer 1 (64 filters), Max Pooling,
Conv Layer 2 (128 filters), Global Average Pooling, Fully Connected (512),
Softmax Output (10 classes). Connect each layer with a downward arrow.
```

### Transformer Architecture

```
Create a Transformer architecture diagram showing Encoder on the left and
Decoder on the right. The Encoder contains: Input Embedding, Positional
Encoding, Multi-Head Self-Attention, Add & Norm, Feed-Forward Network,
Add & Norm. The Decoder mirrors this and adds a cross-attention layer.
Use a professional academic style.
```

### UML Class Diagram

```
Design a UML class diagram with three classes: User, Order, and Product.
User has attributes: id, name, email. Order has: id, date, total.
Product has: id, name, price. User places many Orders (1-to-many).
Order contains many Products (many-to-many). Use standard UML notation.
```

### State Machine

```
Draw a finite state machine for a traffic light controller.
States: Red, Green, Yellow. Transitions:
Red → Green (timer expires),
Green → Yellow (timer expires),
Yellow → Red (timer expires).
Mark Red as the initial state with an arrow. Use circular nodes.
```

### Refinement Examples

After any generation, you can use the refinement box:

- `"Change the node fill colour to light blue (#dbeafe)"`
- `"Make all arrows dashed instead of solid"`
- `"Convert the layout from horizontal to vertical"`
- `"Increase the node distance to 2.5cm"`
- `"Add rounded corners with radius 6pt"`
- `"Make the diagram suitable for an IEEE two-column paper (smaller fonts)"`

---

## 9. Example Generated TikZ Output

**Prompt:** *"Create a machine learning data pipeline with four stages: Data Ingestion, Data Preprocessing, IBM Granite Model Training, and Model Evaluation and Deployment. Horizontal layout with arrows."*

```latex
\documentclass[tikz,border=10pt]{standalone}
\usepackage{tikz}
\usetikzlibrary{positioning,arrows.meta,shapes.geometric}

\begin{document}
\begin{tikzpicture}[
    node distance=1.6cm,
    block/.style={
        rectangle, rounded corners=4pt,
        draw=black!70, fill=blue!8,
        text width=3.2cm, align=center,
        minimum height=1.1cm, font=\small\sffamily
    },
    arrow/.style={-{Stealth[length=6pt]}, thick}
]
    \node[block] (ingest)  {Data\\Ingestion};
    \node[block, right=of ingest]  (preproc) {Data\\Preprocessing};
    \node[block, right=of preproc] (train)   {IBM Granite\\Model Training};
    \node[block, right=of train]   (eval)    {Model Evaluation\\and Deployment};

    \draw[arrow] (ingest)  -- (preproc);
    \draw[arrow] (preproc) -- (train);
    \draw[arrow] (train)   -- (eval);
\end{tikzpicture}
\end{document}
```

**Compile:** `pdflatex diagram.tex` or paste into [Overleaf](https://overleaf.com).

---

## 10. Testing Procedure

### Unit tests (no IBM credentials required)

```bash
python -m pytest tests/ -v
```

Manual test checklist:

| Test | Expected result |
|------|----------------|
| Empty prompt → Generate | Warning message shown, no API call made |
| Valid ML pipeline prompt | TikZ code produced with 4 nodes, 3 arrows |
| Refinement: change colour | `fill=...` colour value updated, node count unchanged |
| Missing `WATSONX_API_KEY` | Clear error message shown in UI, no crash |
| Invalid TikZ from model | Auto-correction triggered; corrected code shown |
| pdflatex not installed | Render tab shows graceful info message |

### Smoke test with real credentials

```bash
python - <<'EOF'
from dotenv import load_dotenv; load_dotenv()
from granite_client import GraniteClient
c = GraniteClient()
print(c.generate("Say: IBM Granite is ready.", max_new_tokens=20))
EOF
```

Expected: a short affirmative response from the model.

---

## 11. Error-Handling Strategy

| Error scenario | Handling |
|----------------|---------|
| Missing env variable | `GraniteClientError` raised at startup; UI shows config guide |
| Network / connection failure | `GraniteClientError` with user-friendly message; no stack trace in UI |
| IAM token expired | Automatic single retry with refreshed token |
| API rate limit / 429 | Error message with suggestion to wait and retry |
| Model returns no TikZ code | `ValueError` caught; user asked to rephrase description |
| TikZ validation errors | One auto-correction pass via Granite; if still invalid, code shown with warnings |
| pdflatex compilation error | Relevant log lines extracted and shown; raw `.tex` still available to download |
| Empty refinement instruction | Warning shown; no API call made |
| All errors | Credentials / API keys are **never** included in any error message |

---

## 12. Future Enhancements

| Enhancement | Description |
|-------------|-------------|
| **Direct SVG preview in browser** | Render TikZ to SVG server-side and display inline without a download step |
| **Diagram version diff** | Show a side-by-side diff of TikZ code before and after refinement |
| **Template library** | Pre-built templates for common diagram types (ResNet, BERT, GAN, etc.) |
| **Multi-page export** | Bundle multiple diagrams into a single `.tex` project |
| **Colour palette picker** | Let users select an IEEE / ACM / Springer colour scheme from a dropdown |
| **Real-time Overleaf sync** | Push generated `.tex` directly to an Overleaf project via the Overleaf API |
| **Fine-tuned Granite model** | Fine-tune IBM Granite on a corpus of academic TikZ diagrams for higher accuracy |
| **LaTeX error feedback loop** | Feed pdflatex error logs back to Granite for a second correction attempt |
| **Diagram search & reuse** | Store generated diagrams in a vector DB for semantic retrieval |
| **Watson Studio Notebook integration** | Run the generator inside a Watson Studio Jupyter notebook environment |
