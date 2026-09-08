"""
prompt_templates.py
-------------------
All prompt templates used to communicate with IBM Granite.

Each function returns a fully assembled prompt string ready for
GraniteClient.generate().  Templates use explicit instructions and
few-shot examples so the model reliably returns raw TikZ code blocks.
"""

# ---------------------------------------------------------------------------
# System context injected at the top of every prompt
# ---------------------------------------------------------------------------
_SYSTEM_CONTEXT = """\
You are an expert academic LaTeX/TikZ diagram engineer.
You ONLY output valid LaTeX/TikZ code — no prose before the code block,
no explanations after it, no markdown prose.
Your diagrams are minimal, professional, and publication-ready (IEEE, ACM, Springer).
Always wrap the complete self-contained tikzpicture inside a LaTeX document skeleton
so it can be compiled with pdflatex immediately.
Use only the TikZ libraries that are actually required.
"""

# ---------------------------------------------------------------------------
# Diagram-type keywords for auto-detection
# ---------------------------------------------------------------------------
DIAGRAM_TYPE_KEYWORDS: dict[str, list[str]] = {
    "flowchart": ["flowchart", "flow chart", "flow diagram", "decision", "process flow"],
    "ml_pipeline": ["machine learning", "ml pipeline", "data pipeline", "training pipeline",
                    "preprocessing", "data ingestion", "model training", "model evaluation"],
    "deep_learning": ["deep learning", "neural network", "layers", "hidden layer",
                      "activation", "backpropagation"],
    "cnn": ["cnn", "convolutional", "conv layer", "pooling", "feature map", "convolution"],
    "rnn_lstm": ["rnn", "lstm", "recurrent", "gru", "sequence", "time step"],
    "transformer": ["transformer", "attention", "self-attention", "encoder", "decoder",
                    "multi-head", "positional encoding"],
    "system_architecture": ["system architecture", "microservice", "api gateway",
                             "service", "database", "client", "server"],
    "block_diagram": ["block diagram", "block", "subsystem", "component", "module"],
    "uml": ["uml", "class diagram", "use case", "inheritance", "association"],
    "sequence_diagram": ["sequence diagram", "actor", "lifeline", "message", "interaction"],
    "state_machine": ["state machine", "state diagram", "transition", "finite state",
                      "initial state", "final state"],
}

# Categorized prompt suggestions for sidebar & UI
CATEGORIZED_PROMPT_SUGGESTIONS: dict[str, list[str]] = {
    "🤖 Machine Learning & Data": [
        "Create a machine learning pipeline with 4 stages: Data Ingestion, Data Preprocessing, IBM Granite Model Training, and Model Evaluation.",
        "Draw a feature engineering pipeline showing Raw Data, Data Cleaning, Feature Extraction, Scaling, and Model Input.",
        "Design a MLOps workflow showing Data Source, Feature Store, Model Registry, Automated Testing, Deployment, and Monitoring."
    ],
    "🧠 Deep Learning & AI": [
        "Draw a CNN architecture with Input Image, Conv Layer (3x3), Max Pooling, Fully Connected Layer, and Softmax Output.",
        "Create a Transformer Encoder diagram showing Input Embedding, Positional Encoding, Multi-Head Attention, and Feed Forward Network.",
        "Draw an unfolded Recurrent Neural Network (RNN) across 3 time steps showing input, hidden states, and outputs."
    ],
    "☁️ System & Cloud Architecture": [
        "Design a microservices system with API Gateway, User Service, Order Service, Payment Gateway, and PostgreSQL Database.",
        "Draw a serverless flow: Client Request -> API Gateway -> Lambda Function -> DynamoDB Database.",
        "Create a high-availability web architecture: Client Browser -> NGINX Load Balancer -> Web Servers -> Redis Cache -> Primary DB."
    ],
    "🔄 Flowcharts & Process": [
        "Draw a decision flowchart for user authentication: Start -> Enter Credentials -> Valid Password? -> Grant Access / Show Error.",
        "Create an e-commerce checkout flowchart: Item Selected -> Checkout -> Process Payment -> Success? -> Send Receipt.",
        "Draw a state machine diagram for a traffic light with Red, Yellow, and Green states."
    ],
    "📊 UML & Sequences": [
        "Design a UML Class Diagram with User, Order, Product, and Payment classes showing inheritance and relationships.",
        "Create a Sequence Diagram showing User, Web Client, Backend API, and Database interaction sequence.",
        "Draw a Use Case diagram for a Library System with Student, Librarian, Borrow Book, and Reserve Book actions."
    ]
}


def detect_diagram_type(description: str) -> str:
    """Return the best-matching diagram type string for *description*."""
    lower = description.lower()
    best_type = "block_diagram"
    best_score = 0
    for dtype, keywords in DIAGRAM_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > best_score:
            best_score = score
            best_type = dtype
    return best_type


# ---------------------------------------------------------------------------
# Generation prompt
# ---------------------------------------------------------------------------

_GENERATION_FEW_SHOT = r"""
### EXAMPLE INPUT
"Create a machine learning data pipeline with four stages: Data Ingestion,
Data Preprocessing, IBM Granite Model Training, and Model Evaluation.
Arrange them horizontally left to right with arrows."

### EXAMPLE OUTPUT
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
    \node[block, right=of train]   (eval)    {Model\\Evaluation};

    \draw[arrow] (ingest)  -- (preproc);
    \draw[arrow] (preproc) -- (train);
    \draw[arrow] (train)   -- (eval);
\end{tikzpicture}
\end{document}
```
"""


def build_generation_prompt(description: str, diagram_type: str) -> str:
    """
    Build the full generation prompt for a new diagram.

    Parameters
    ----------
    description:
        The raw natural-language description from the user.
    diagram_type:
        The auto-detected or user-specified diagram type string.
    """
    return f"""{_SYSTEM_CONTEXT}

DIAGRAM TYPE DETECTED: {diagram_type.replace("_", " ").title()}

TASK:
Generate a complete, compilable LaTeX/TikZ diagram for the following description.
Requirements:
1. Use \\begin{{tikzpicture}} … \\end{{tikzpicture}}.
2. Wrap it in a standalone document class.
3. Declare ALL required \\usetikzlibrary packages.
4. Use professional, consistent node styles.
5. Use clean arrows with arrowheads.
6. Avoid overlapping nodes.
7. Preserve the exact labels from the description.
8. Return ONLY the LaTeX code block — nothing else.

{_GENERATION_FEW_SHOT}

### NEW INPUT
"{description}"

### OUTPUT (LaTeX code only)
"""


# ---------------------------------------------------------------------------
# Refinement prompt
# ---------------------------------------------------------------------------

def build_refinement_prompt(
    original_description: str,
    existing_tikz: str,
    refinement_instruction: str,
) -> str:
    """
    Build a prompt that asks Granite to modify *existing_tikz* according to
    *refinement_instruction* without changing unrelated parts.
    """
    return f"""{_SYSTEM_CONTEXT}

TASK: Modify an EXISTING TikZ diagram according to a refinement instruction.

Rules:
1. Apply ONLY the change described in the refinement instruction.
2. Keep all other nodes, connections, and labels exactly the same.
3. Return the COMPLETE updated LaTeX document — not a diff, not a partial snippet.
4. Return ONLY the LaTeX code block.

ORIGINAL DIAGRAM DESCRIPTION:
"{original_description}"

EXISTING TIKZ CODE:
```latex
{existing_tikz}
```

REFINEMENT INSTRUCTION:
"{refinement_instruction}"

### OUTPUT (complete updated LaTeX code only)
"""


# ---------------------------------------------------------------------------
# Extraction prompt (for structured metadata — not always called)
# ---------------------------------------------------------------------------

def build_extraction_prompt(description: str) -> str:
    """
    Ask Granite to extract structured diagram metadata as JSON.
    Used internally by the validator to cross-check generated code.
    """
    return f"""{_SYSTEM_CONTEXT}

TASK: Extract diagram metadata from the description as a JSON object.
Return ONLY valid JSON — no prose.

JSON schema:
{{
  "diagram_type": "<string>",
  "components": ["<list of node/component names>"],
  "connections": [["<from>", "<to>"]],
  "layout": "<horizontal|vertical|hierarchical|circular>",
  "shape": "<rectangle|rounded_rectangle|circle|diamond|custom>",
  "color_hints": "<any color mentions, or 'default'>",
  "direction": "<left_to_right|top_to_bottom|right_to_left|bottom_to_top>"
}}

DESCRIPTION:
"{description}"

JSON:
"""


# ---------------------------------------------------------------------------
# Correction prompt
# ---------------------------------------------------------------------------

def build_correction_prompt(tikz_code: str, errors: list[str]) -> str:
    """
    Ask Granite to fix *tikz_code* given a list of detected *errors*.
    """
    error_list = "\n".join(f"- {e}" for e in errors)
    return f"""{_SYSTEM_CONTEXT}

TASK: Fix the following TikZ code. The detected issues are listed below.
Apply the minimum necessary changes to make the code valid.
Return ONLY the corrected complete LaTeX code block.

DETECTED ISSUES:
{error_list}

BROKEN TIKZ CODE:
```latex
{tikz_code}
```

### OUTPUT (corrected LaTeX code only)
"""


# ---------------------------------------------------------------------------
# Explanation prompt (optional — used by the UI)
# ---------------------------------------------------------------------------

def build_explanation_prompt(tikz_code: str, description: str) -> str:
    """
    Ask Granite for a short plain-English explanation of the generated diagram.
    Returns 2-4 sentences max.
    """
    return f"""\
You are a helpful academic writing assistant.
In 2–4 concise sentences, explain what the following TikZ diagram represents
and how it is structured.  Do NOT reproduce the LaTeX code.

Original request: "{description}"

TikZ code summary:
{tikz_code[:600]}

Explanation:
"""
