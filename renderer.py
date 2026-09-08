"""
renderer.py
-----------
Optional PDF and SVG rendering of generated TikZ/LaTeX code.

The renderer requires a LaTeX distribution (pdflatex or lualatex) and,
for SVG output, pdf2svg or Inkscape to be installed on the system.
These are OPTIONAL dependencies: if they are absent the functions return
a RenderResult with success=False and an appropriate message, rather than
raising an exception, so the Streamlit UI can degrade gracefully.

Public API
----------
render_pdf(tikz_code: str) -> RenderResult
    Compile to PDF and return the bytes.

render_svg(tikz_code: str) -> RenderResult
    Compile to PDF then convert to SVG; return the SVG string.

is_latex_available() -> bool
    True if pdflatex is on PATH.

is_pdf2svg_available() -> bool
    True if pdf2svg is on PATH.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class RenderResult:
    success: bool
    message: str
    pdf_bytes: bytes | None = None
    svg_content: str | None = None
    log_output: str = ""


# ---------------------------------------------------------------------------
# Availability checks
# ---------------------------------------------------------------------------

def is_latex_available() -> bool:
    """Return True if pdflatex can be found on PATH."""
    return shutil.which("pdflatex") is not None


def is_pdf2svg_available() -> bool:
    """Return True if pdf2svg can be found on PATH."""
    return shutil.which("pdf2svg") is not None


def is_inkscape_available() -> bool:
    """Return True if inkscape can be found on PATH."""
    return shutil.which("inkscape") is not None


# ---------------------------------------------------------------------------
# PDF rendering
# ---------------------------------------------------------------------------

def render_pdf(tikz_code: str, timeout: int = 60) -> RenderResult:
    """
    Compile *tikz_code* with pdflatex and return the PDF bytes.

    Parameters
    ----------
    tikz_code:
        Complete LaTeX document (including \\documentclass).
    timeout:
        Seconds to wait for pdflatex before aborting.

    Returns
    -------
    RenderResult
        .pdf_bytes contains the compiled PDF on success.
    """
    if not is_latex_available():
        return RenderResult(
            success=False,
            message=(
                "pdflatex not found. Install a TeX distribution "
                "(TeX Live, MiKTeX, or MacTeX) to enable PDF rendering."
            ),
        )

    with tempfile.TemporaryDirectory(prefix="tikz_render_") as tmpdir:
        tex_path = Path(tmpdir) / "diagram.tex"
        pdf_path = Path(tmpdir) / "diagram.pdf"
        log_path = Path(tmpdir) / "diagram.log"

        tex_path.write_text(tikz_code, encoding="utf-8")

        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory", tmpdir,
            str(tex_path),
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                message=f"pdflatex compilation timed out after {timeout}s.",
            )
        except FileNotFoundError:
            return RenderResult(
                success=False,
                message="pdflatex binary not found on PATH.",
            )

        log_text = ""
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")

        if not pdf_path.exists() or proc.returncode != 0:
            # Extract the relevant error from the log
            error_snippet = _extract_latex_error(log_text)
            return RenderResult(
                success=False,
                message=f"pdflatex failed: {error_snippet}",
                log_output=log_text,
            )

        pdf_bytes = pdf_path.read_bytes()
        return RenderResult(
            success=True,
            message="PDF compiled successfully.",
            pdf_bytes=pdf_bytes,
            log_output=log_text,
        )


# ---------------------------------------------------------------------------
# SVG rendering
# ---------------------------------------------------------------------------

def render_svg(tikz_code: str, timeout: int = 90) -> RenderResult:
    """
    Compile *tikz_code* to PDF then convert it to SVG.

    Tries pdf2svg first; falls back to Inkscape if available.

    Returns
    -------
    RenderResult
        .svg_content contains the SVG XML string on success.
    """
    # Step 1: get PDF
    pdf_result = render_pdf(tikz_code, timeout=timeout - 30)
    if not pdf_result.success:
        return pdf_result

    assert pdf_result.pdf_bytes is not None

    with tempfile.TemporaryDirectory(prefix="tikz_svg_") as tmpdir:
        pdf_path = Path(tmpdir) / "diagram.pdf"
        svg_path = Path(tmpdir) / "diagram.svg"

        pdf_path.write_bytes(pdf_result.pdf_bytes)

        # Try pdf2svg
        if is_pdf2svg_available():
            success, log = _run_pdf2svg(pdf_path, svg_path, timeout=30)
        elif is_inkscape_available():
            success, log = _run_inkscape(pdf_path, svg_path, timeout=30)
        else:
            return RenderResult(
                success=False,
                message=(
                    "Neither pdf2svg nor Inkscape found. "
                    "Install one to enable SVG export. "
                    "The PDF is still available above."
                ),
                pdf_bytes=pdf_result.pdf_bytes,
            )

        if not success or not svg_path.exists():
            return RenderResult(
                success=False,
                message=f"SVG conversion failed: {log}",
                pdf_bytes=pdf_result.pdf_bytes,
                log_output=log,
            )

        svg_content = svg_path.read_text(encoding="utf-8")
        return RenderResult(
            success=True,
            message="SVG generated successfully.",
            pdf_bytes=pdf_result.pdf_bytes,
            svg_content=svg_content,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_pdf2svg(pdf_path: Path, svg_path: Path, timeout: int) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["pdf2svg", str(pdf_path), str(svg_path), "1"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode == 0, proc.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return False, str(exc)


def _run_inkscape(pdf_path: Path, svg_path: Path, timeout: int) -> tuple[bool, str]:
    # Inkscape ≥ 1.0 CLI syntax
    try:
        proc = subprocess.run(
            [
                "inkscape",
                "--pdf-poppler",
                str(pdf_path),
                f"--export-filename={svg_path}",
                "--export-type=svg",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode == 0, proc.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return False, str(exc)


def _extract_latex_error(log_text: str) -> str:
    """Return a concise error summary from a pdflatex log."""
    lines = log_text.splitlines()
    error_lines = [ln for ln in lines if ln.startswith("!")]
    if error_lines:
        return " | ".join(error_lines[:3])
    # Fall back to last 10 lines of log
    tail = "\n".join(lines[-10:])
    return f"See log for details:\n{tail}"
