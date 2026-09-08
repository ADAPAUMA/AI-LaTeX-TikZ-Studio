"""
tikz_generator.py
-----------------
Orchestrates the full diagram generation pipeline:

    1. Detect diagram type from user description
    2. Build a Granite prompt via prompt_templates (or use smart template fallback)
    3. Call GraniteClient.generate()
    4. Extract TikZ code from the raw response
    5. Run validator.validate_tikz()
    6. If errors found → ask Granite to auto-correct (one attempt)
    7. Return a DiagramResult dataclass

This module contains pure business logic layer that can be tested independently.
"""

import re
import logging
from dataclasses import dataclass, field

from granite_client import GraniteClient, GraniteClientError
from prompt_templates import (
    detect_diagram_type,
    build_generation_prompt,
    build_refinement_prompt,
    build_correction_prompt,
    build_explanation_prompt,
)
from validator import validate_tikz, ValidationResult, format_validation_report

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DiagramResult:
    """Returned by TikZGenerator for every successful generation / refinement."""
    description: str
    diagram_type: str
    tikz_code: str
    preamble: str
    explanation: str
    validation: ValidationResult
    auto_corrected: bool = False
    raw_model_output: str = ""
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex helpers for extracting code from model output
# ---------------------------------------------------------------------------

_FENCED_BLOCK = re.compile(
    r"```(?:latex|tex|LaTeX)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

_BARE_DOCUMENT = re.compile(
    r"(\\documentclass.*?\\end\{document\})",
    re.DOTALL,
)

_BARE_TIKZ = re.compile(
    r"(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})",
    re.DOTALL,
)


def _extract_tikz_code(raw: str) -> str:
    """
    Extract LaTeX/TikZ code from *raw* model output.
    """
    m = _FENCED_BLOCK.search(raw)
    if m:
        return m.group(1).strip()

    m = _BARE_DOCUMENT.search(raw)
    if m:
        return m.group(1).strip()

    m = _BARE_TIKZ.search(raw)
    if m:
        tikz = m.group(1).strip()
        return _wrap_in_document(tikz)

    raise ValueError(
        "The model did not return recognisable LaTeX/TikZ code. "
        "Try a more specific description."
    )


def _wrap_in_document(tikz_body: str, libraries: str = "positioning,arrows.meta,shapes.geometric") -> str:
    """Wrap a bare tikzpicture in a minimal standalone LaTeX document."""
    return (
        "\\documentclass[tikz,border=10pt]{standalone}\n"
        "\\usepackage{tikz}\n"
        f"\\usetikzlibrary{{{libraries}}}\n"
        "\n"
        "\\begin{document}\n"
        f"{tikz_body}\n"
        "\\end{document}"
    )


def _extract_preamble(code: str) -> str:
    """Return the preamble lines (packages + libraries) from *code*."""
    lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith(("\\documentclass", "\\usepackage", "\\usetikzlibrary")):
            lines.append(stripped)
        elif stripped.startswith("\\begin{document}"):
            break
    return "\n".join(lines) if lines else "% No preamble detected"


# ---------------------------------------------------------------------------
# Fallback generator for Offline / Unconfigured mode
# ---------------------------------------------------------------------------

def _generate_fallback_diagram(description: str, diagram_type: str) -> tuple[str, str]:
    """Generate high-quality static TikZ diagram when Granite is unreachable/unconfigured."""
    dt = diagram_type.lower()
    desc_lower = description.lower()

    if "cnn" in desc_lower or dt == "cnn":
        code = (
            "\\documentclass[tikz,border=10pt]{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\usetikzlibrary{positioning,arrows.meta}\n\n"
            "\\begin{document}\n"
            "\\begin{tikzpicture}[\n"
            "    node distance=1.4cm,\n"
            "    layer/.style={rectangle, draw=blue!80!black, fill=blue!10, text width=2.2cm, align=center, minimum height=2.6cm, font=\\small\\sffamily},\n"
            "    conv/.style={rectangle, draw=teal!80!black, fill=teal!15, text width=2.0cm, align=center, minimum height=2.0cm, font=\\small\\sffamily},\n"
            "    pool/.style={rectangle, draw=orange!80!black, fill=orange!15, text width=1.6cm, align=center, minimum height=1.5cm, font=\\small\\sffamily},\n"
            "    dense/.style={rectangle, draw=purple!80!black, fill=purple!15, text width=1.5cm, align=center, minimum height=1.2cm, font=\\small\\sffamily},\n"
            "    arrow/.style={-{Stealth[length=6pt]}, thick, draw=gray!70}\n"
            "]\n"
            "    \\node[layer] (input) {Input Image\\\\32x32x3};\n"
            "    \\node[conv, right=of input] (conv1) {Conv 3x3\\\\Feature Maps};\n"
            "    \\node[pool, right=of conv1] (pool1) {Max Pooling\\\\16x16};\n"
            "    \\node[dense, right=of pool1] (fc) {Dense FC\\\\128 units};\n"
            "    \\node[dense, right=of fc, fill=red!15, draw=red!80] (out) {Softmax\\\\Classes};\n\n"
            "    \\draw[arrow] (input) -- (conv1);\n"
            "    \\draw[arrow] (conv1) -- (pool1);\n"
            "    \\draw[arrow] (pool1) -- (fc);\n"
            "    \\draw[arrow] (fc) -- (out);\n"
            "\\end{tikzpicture}\n"
            "\\end{document}"
        )
        exp = "A Convolutional Neural Network (CNN) architecture with input image, convolutional feature extraction layer, max pooling layer, dense fully connected layer, and softmax classification output."

    elif "transformer" in desc_lower or dt == "transformer":
        code = (
            "\\documentclass[tikz,border=10pt]{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\usetikzlibrary{positioning,arrows.meta}\n\n"
            "\\begin{document}\n"
            "\\begin{tikzpicture}[\n"
            "    node distance=1.2cm,\n"
            "    box/.style={rectangle, rounded corners=4pt, draw=blue!70!black, fill=blue!10, text width=3.6cm, align=center, minimum height=1cm, font=\\small\\sffamily},\n"
            "    mha/.style={rectangle, rounded corners=4pt, draw=orange!80!black, fill=orange!15, text width=3.6cm, align=center, minimum height=1.1cm, font=\\small\\sffamily\\bfseries},\n"
            "    norm/.style={rectangle, rounded corners=4pt, draw=teal!80!black, fill=teal!15, text width=3.6cm, align=center, minimum height=0.8cm, font=\\small\\sffamily},\n"
            "    arrow/.style={-{Stealth[length=6pt]}, thick}\n"
            "]\n"
            "    \\node[box] (emb) {Input Embedding + Positional Encoding};\n"
            "    \\node[mha, above=of emb] (mha) {Multi-Head Attention};\n"
            "    \\node[norm, above=of mha] (norm1) {Add \\& Norm};\n"
            "    \\node[box, above=of norm1] (ffn) {Feed Forward Network};\n"
            "    \\node[norm, above=of ffn] (norm2) {Add \\& Norm};\n\n"
            "    \\draw[arrow] (emb) -- (mha);\n"
            "    \\draw[arrow] (mha) -- (norm1);\n"
            "    \\draw[arrow] (norm1) -- (ffn);\n"
            "    \\draw[arrow] (ffn) -- (norm2);\n"
            "\\end{tikzpicture}\n"
            "\\end{document}"
        )
        exp = "A Transformer Encoder layer component showing input embeddings with positional encodings, multi-head attention mechanism, residual connections (Add & Norm), and feed-forward neural sublayer."

    elif "microservice" in desc_lower or "system" in desc_lower or dt == "system_architecture":
        code = (
            "\\documentclass[tikz,border=10pt]{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\usetikzlibrary{positioning,arrows.meta,shapes.geometric}\n\n"
            "\\begin{document}\n"
            "\\begin{tikzpicture}[\n"
            "    node distance=1.5cm and 2.0cm,\n"
            "    client/.style={rectangle, rounded corners=6pt, draw=purple!80, fill=purple!10, text width=2.4cm, align=center, minimum height=1cm, font=\\small\\sffamily\\bfseries},\n"
            "    gateway/.style={rectangle, rounded corners=6pt, draw=teal!80, fill=teal!15, text width=2.6cm, align=center, minimum height=1.2cm, font=\\small\\sffamily\\bfseries},\n"
            "    service/.style={rectangle, rounded corners=4pt, draw=blue!80, fill=blue!10, text width=2.4cm, align=center, minimum height=1cm, font=\\small\\sffamily},\n"
            "    db/.style={cylinder, cylinder fill=amber!20, cylinder end fill=amber!40, draw=amber!80!black, shape border rotate=90, text width=1.8cm, align=center, minimum height=1.2cm, font=\\small\\sffamily},\n"
            "    arrow/.style={<->, {Stealth[length=6pt]}-{Stealth[length=6pt]}, thick, draw=gray!70}\n"
            "]\n"
            "    \\node[client] (client) {Client App};\n"
            "    \\node[gateway, right=of client] (gw) {API Gateway};\n"
            "    \\node[service, above right=0.4cm and 1.5cm of gw] (user) {User Service};\n"
            "    \\node[service, right=1.5cm of gw] (order) {Order Service};\n"
            "    \\node[service, below right=0.4cm and 1.5cm of gw] (pay) {Payment Service};\n"
            "    \\node[db, right=of order] (db) {Database Cluster};\n\n"
            "    \\draw[arrow] (client) -- (gw);\n"
            "    \\draw[arrow] (gw) -- (user);\n"
            "    \\draw[arrow] (gw) -- (order);\n"
            "    \\draw[arrow] (gw) -- (pay);\n"
            "    \\draw[arrow] (order) -- (db);\n"
            "\\end{tikzpicture}\n"
            "\\end{document}"
        )
        exp = "A microservices system architecture diagram featuring a client front-end, central API gateway, independent domain services (User, Order, Payment), and persistent database cluster."

    elif "state" in desc_lower or dt == "state_machine":
        code = (
            "\\documentclass[tikz,border=10pt]{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\usetikzlibrary{positioning,arrows.meta}\n\n"
            "\\begin{document}\n"
            "\\begin{tikzpicture}[\n"
            "    node distance=2.2cm,\n"
            "    state/.style={circle, draw=blue!80!black, fill=blue!10, thick, minimum size=1.5cm, font=\\small\\sffamily\\bfseries},\n"
            "    arrow/.style={-{Stealth[length=6pt]}, thick, bend left=20}\n"
            "]\n"
            "    \\node[state, fill=red!20, draw=red!80] (red) {Red};\n"
            "    \\node[state, fill=green!20, draw=green!80, right=of red] (green) {Green};\n"
            "    \\node[state, fill=yellow!20, draw=yellow!80, right=of green] (yellow) {Yellow};\n\n"
            "    \\draw[arrow] (red) to node[above, font=\\scriptsize] {Timer 40s} (green);\n"
            "    \\draw[arrow] (green) to node[above, font=\\scriptsize] {Timer 30s} (yellow);\n"
            "    \\draw[arrow] (yellow) to node[below, font=\\scriptsize] {Timer 5s} (red);\n"
            "\\end{tikzpicture}\n"
            "\\end{document}"
        )
        exp = "A finite state machine diagram representing a traffic light controller with Red, Green, and Yellow state transitions."

    elif "flowchart" in desc_lower or "decision" in desc_lower or dt == "flowchart":
        code = (
            "\\documentclass[tikz,border=10pt]{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\usetikzlibrary{positioning,arrows.meta,shapes.geometric}\n\n"
            "\\begin{document}\n"
            "\\begin{tikzpicture}[\n"
            "    node distance=1.4cm,\n"
            "    start/.style={ellipse, draw=emerald!80!black, fill=emerald!15, minimum height=0.9cm, font=\\small\\sffamily\\bfseries},\n"
            "    proc/.style={rectangle, rounded corners=4pt, draw=blue!70!black, fill=blue!10, text width=2.8cm, align=center, minimum height=1cm, font=\\small\\sffamily},\n"
            "    dec/.style={diamond, aspect=2, draw=amber!80!black, fill=amber!15, align=center, font=\\small\\sffamily},\n"
            "    arrow/.style={-{Stealth[length=6pt]}, thick}\n"
            "]\n"
            "    \\node[start] (start) {Start Process};\n"
            "    \\node[proc, below=of start] (input) {Enter Credentials};\n"
            "    \\node[dec, below=of input] (check) {Credentials\\\\Valid?};\n"
            "    \\node[proc, right=1.6cm of check] (success) {Grant Access};\n"
            "    \\node[proc, below=of check] (fail) {Display Error};\n\n"
            "    \\draw[arrow] (start) -- (input);\n"
            "    \\draw[arrow] (input) -- (check);\n"
            "    \\draw[arrow] (check) -- node[above, font=\\scriptsize] {Yes} (success);\n"
            "    \\draw[arrow] (check) -- node[right, font=\\scriptsize] {No} (fail);\n"
            "\\end{tikzpicture}\n"
            "\\end{document}"
        )
        exp = "A decision flowchart diagram illustrating user authentication process flow with input, validation decision branch, success, and error paths."

    else:
        # Default ML Data Pipeline
        code = (
            "\\documentclass[tikz,border=10pt]{standalone}\n"
            "\\usepackage{tikz}\n"
            "\\usetikzlibrary{positioning,arrows.meta,shapes.geometric}\n\n"
            "\\begin{document}\n"
            "\\begin{tikzpicture}[\n"
            "    node distance=1.6cm,\n"
            "    block/.style={\n"
            "        rectangle, rounded corners=5pt,\n"
            "        draw=blue!70!black, fill=blue!8,\n"
            "        text width=3.2cm, align=center,\n"
            "        minimum height=1.1cm, font=\\small\\sffamily\\bfseries\n"
            "    },\n"
            "    arrow/.style={-{Stealth[length=6pt]}, thick, draw=blue!80!black}\n"
            "]\n"
            "    \\node[block] (ingest)  {Data\\\\Ingestion};\n"
            "    \\node[block, right=of ingest]  (preproc) {Data\\\\Preprocessing};\n"
            "    \\node[block, right=of preproc] (train)   {IBM Granite\\\\Model Training};\n"
            "    \\node[block, right=of train]   (eval)    {Model\\\\Evaluation};\n\n"
            "    \\draw[arrow] (ingest)  -- (preproc);\n"
            "    \\draw[arrow] (preproc) -- (train);\n"
            "    \\draw[arrow] (train)   -- (eval);\n"
            "\\end{tikzpicture}\n"
            "\\end{document}"
        )
        exp = "A machine learning pipeline block diagram showing four sequential processing stages: Data Ingestion, Data Preprocessing, IBM Granite Model Training, and Model Evaluation."

    return code, exp


# ---------------------------------------------------------------------------
# Main generator class
# ---------------------------------------------------------------------------

class TikZGenerator:
    """
    High-level diagram generator.
    """

    def __init__(self, client: GraniteClient | None = None, auto_correct: bool = True):
        self._client = client or GraniteClient()
        self._auto_correct = auto_correct

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def generate(self, description: str) -> DiagramResult:
        """
        Generate a new TikZ diagram from a natural-language *description*.
        """
        description = description.strip()
        if not description:
            raise ValueError("Diagram description cannot be empty.")

        diagram_type = detect_diagram_type(description)

        # Try IBM Granite if configured, otherwise fallback to smart template generator
        if self._client.is_configured():
            try:
                prompt = build_generation_prompt(description, diagram_type)
                logger.info("Calling Granite for generation (type=%s)", diagram_type)
                raw_output = self._client.generate(prompt, max_new_tokens=2048, temperature=0.2)
                tikz_code = _extract_tikz_code(raw_output)
                preamble = _extract_preamble(tikz_code)
                validation = validate_tikz(tikz_code)
                auto_corrected = False

                if not validation.is_valid and self._auto_correct:
                    logger.info("Validation failed; attempting auto-correction.")
                    tikz_code, validation, auto_corrected = self._attempt_correction(
                        tikz_code, validation
                    )

                explanation = self._generate_explanation(tikz_code, description)

                return DiagramResult(
                    description=description,
                    diagram_type=diagram_type,
                    tikz_code=tikz_code,
                    preamble=preamble,
                    explanation=explanation,
                    validation=validation,
                    auto_corrected=auto_corrected,
                    raw_model_output=raw_output,
                )
            except GraniteClientError as exc:
                logger.warning("Granite API call failed (%s); using smart generator fallback.", exc)
                warnings = [f"watsonx API Notice: {exc} — generated using AI Diagram Engine fallback."]
        else:
            warnings = ["watsonx API Key unconfigured — generated using Smart AI Diagram Engine fallback."]

        # Offline / Demo Fallback Mode
        tikz_code, explanation = _generate_fallback_diagram(description, diagram_type)
        preamble = _extract_preamble(tikz_code)
        validation = validate_tikz(tikz_code)

        return DiagramResult(
            description=description,
            diagram_type=diagram_type,
            tikz_code=tikz_code,
            preamble=preamble,
            explanation=explanation,
            validation=validation,
            auto_corrected=False,
            raw_model_output=tikz_code,
            warnings=warnings if 'warnings' in locals() else [],
        )

    def refine(self, result: DiagramResult, refinement_instruction: str) -> DiagramResult:
        """
        Refine an existing diagram using a natural-language instruction.
        """
        refinement_instruction = refinement_instruction.strip()
        if not refinement_instruction:
            raise ValueError("Refinement instruction cannot be empty.")

        if self._client.is_configured():
            try:
                prompt = build_refinement_prompt(
                    original_description=result.description,
                    existing_tikz=result.tikz_code,
                    refinement_instruction=refinement_instruction,
                )
                logger.info("Calling Granite for refinement.")
                raw_output = self._client.generate(prompt, max_new_tokens=2048, temperature=0.1)

                tikz_code = _extract_tikz_code(raw_output)
                preamble = _extract_preamble(tikz_code)
                validation = validate_tikz(tikz_code)
                auto_corrected = False

                if not validation.is_valid and self._auto_correct:
                    tikz_code, validation, auto_corrected = self._attempt_correction(
                        tikz_code, validation
                    )

                explanation = self._generate_explanation(tikz_code, result.description)

                return DiagramResult(
                    description=result.description,
                    diagram_type=result.diagram_type,
                    tikz_code=tikz_code,
                    preamble=preamble,
                    explanation=explanation,
                    validation=validation,
                    auto_corrected=auto_corrected,
                    raw_model_output=raw_output,
                    warnings=[f'Applied refinement: “{refinement_instruction}”'],
                )
            except GraniteClientError as exc:
                logger.warning("Granite refinement failed (%s); applying rule-based refinement.", exc)

        # Fallback refinement modification (e.g. color tweak or simple text replacement)
        updated_code = result.tikz_code
        rule_applied = refinement_instruction.lower()

        if "blue" in rule_applied:
            updated_code = re.sub(r'fill=\w+!\d+', 'fill=blue!15', updated_code)
            updated_code = re.sub(r'draw=\w+!\d+', 'draw=blue!80', updated_code)
        elif "green" in rule_applied or "emerald" in rule_applied:
            updated_code = re.sub(r'fill=\w+!\d+', 'fill=emerald!15', updated_code)
            updated_code = re.sub(r'draw=\w+!\d+', 'draw=emerald!80', updated_code)
        elif "red" in rule_applied:
            updated_code = re.sub(r'fill=\w+!\d+', 'fill=red!15', updated_code)
            updated_code = re.sub(r'draw=\w+!\d+', 'draw=red!80', updated_code)
        elif "dashed" in rule_applied:
            updated_code = updated_code.replace("arrow/.style={", "arrow/.style={dashed, ")
        elif "thick" in rule_applied:
            updated_code = updated_code.replace("arrow/.style={", "arrow/.style={very thick, ")

        preamble = _extract_preamble(updated_code)
        validation = validate_tikz(updated_code)

        return DiagramResult(
            description=result.description,
            diagram_type=result.diagram_type,
            tikz_code=updated_code,
            preamble=preamble,
            explanation=result.explanation + f" (Refined: {refinement_instruction})",
            validation=validation,
            auto_corrected=False,
            raw_model_output=updated_code,
            warnings=[f'Applied refinement: “{refinement_instruction}”'],
        )

    def _attempt_correction(
        self,
        tikz_code: str,
        validation: ValidationResult,
    ) -> tuple[str, ValidationResult, bool]:
        """Run one correction pass with Granite and re-validate."""
        if not self._client.is_configured():
            return tikz_code, validation, False
        prompt = build_correction_prompt(tikz_code, validation.errors)
        try:
            raw = self._client.generate(prompt, max_new_tokens=2048, temperature=0.1)
            corrected = _extract_tikz_code(raw)
            new_validation = validate_tikz(corrected)
            return corrected, new_validation, True
        except (GraniteClientError, ValueError) as exc:
            logger.warning("Auto-correction failed: %s", exc)
            return tikz_code, validation, False

    def _generate_explanation(self, tikz_code: str, description: str) -> str:
        """Return a short plain-English explanation of the diagram."""
        if not self._client.is_configured():
            return f"Diagram for '{description}' generated successfully."
        prompt = build_explanation_prompt(tikz_code, description)
        try:
            return self._client.generate(prompt, max_new_tokens=200, temperature=0.3)
        except GraniteClientError as exc:
            logger.warning("Explanation generation failed: %s", exc)
            return f"Diagram for '{description}' generated successfully."


def format_output(result: DiagramResult) -> dict:
    """
    Convert a DiagramResult into a flat dict suitable for the Streamlit UI.
    """
    val_report = format_validation_report(result.validation)

    compile_instructions = (
        "1. Copy the LaTeX code into a .tex file (e.g. diagram.tex).\n"
        "2. Compile with:  pdflatex diagram.tex\n"
        "   Or use an online editor such as Overleaf (overleaf.com).\n"
        "3. The document class is 'standalone', so the PDF output "
        "will be cropped to the diagram automatically.\n"
        "4. To include in a paper, copy the tikzpicture block "
        "into a \\figure environment in your main document."
    )

    return {
        "title": f"{result.diagram_type.replace('_', ' ').title()} Diagram",
        "explanation": result.explanation,
        "preamble_check": result.preamble,
        "tikz_code": result.tikz_code,
        "diagram_type": result.diagram_type,
        "auto_corrected": result.auto_corrected,
        "validation_report": val_report,
        "compile_instructions": compile_instructions,
        "warnings": result.warnings,
    }
