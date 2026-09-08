"""
validator.py
------------
Static TikZ / LaTeX code validator.

Performs a set of deterministic heuristic checks on generated TikZ code
*before* it reaches the user.  The checks intentionally avoid spawning a
full LaTeX process (so they work in environments without a TeX installation)
while still catching the most common model-generated mistakes.

Public API
----------
validate_tikz(code: str) -> ValidationResult
    Run all checks and return a ValidationResult dataclass.
"""

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Container returned by validate_tikz()."""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ---------------------------------------------------------------------------
# Known TikZ libraries referenced in generated code
# ---------------------------------------------------------------------------
_LIBRARY_PATTERN = re.compile(
    r"\\usetikzlibrary\s*\{([^}]+)\}"
)
_NODE_NAME_PATTERN = re.compile(
    r"\\node\s*(?:\[[^\]]*\])?\s*\((\w+)\)"
)
_NODE_REF_PATTERN = re.compile(
    r"\((\w+)(?:\.[a-z\s]+)?\)"
)
_DRAW_REF_PATTERN = re.compile(
    r"\\draw[^;]*\((\w+)(?:\.[a-z\s]+)?\)[^;]*\((\w+)(?:\.[a-z\s]+)?\)"
)
_BEGIN_TIKZ = re.compile(r"\\begin\s*\{tikzpicture\}")
_END_TIKZ = re.compile(r"\\end\s*\{tikzpicture\}")
_BEGIN_DOC = re.compile(r"\\begin\s*\{document\}")
_END_DOC = re.compile(r"\\end\s*\{document\}")

# Libraries implied by certain commands
_IMPLIES: dict[str, str] = {
    "arrows.meta": r"Stealth|LaTeX|Circle|Diamond",
    "positioning": r"right=of|left=of|above=of|below=of",
    "shapes.geometric": r"diamond|ellipse|trapezium|regular polygon|cloud",
    "shapes.arrows": r"single arrow|double arrow|arrow box",
    "matrix": r"\\matrix",
    "calc": r"\$\(",
    "fit": r"\\node.*fit=",
    "decorations.pathreplacing": r"decorate.*brace",
    "backgrounds": r"\\begin\{pgfonlayer\}\{background\}",
}


def validate_tikz(code: str) -> ValidationResult:
    """
    Validate *code* with heuristic checks.

    Returns a ValidationResult with is_valid=True if no errors are found.
    Warnings do not affect is_valid.
    """
    result = ValidationResult(is_valid=True)

    # 1. Non-empty
    if not code or not code.strip():
        result.add_error("Generated code is empty.")
        return result

    # 2. Balanced braces
    _check_balanced_braces(code, result)

    # 3. tikzpicture environment present and matched
    begins = len(_BEGIN_TIKZ.findall(code))
    ends = len(_END_TIKZ.findall(code))
    if begins == 0:
        result.add_error("Missing \\begin{tikzpicture}.")
    if ends == 0:
        result.add_error("Missing \\end{tikzpicture}.")
    if begins > 0 and ends > 0 and begins != ends:
        result.add_error(
            f"Mismatched tikzpicture environments: "
            f"{begins} begin vs {ends} end."
        )

    # 4. document environment
    doc_begins = len(_BEGIN_DOC.findall(code))
    doc_ends = len(_END_DOC.findall(code))
    if doc_begins == 0 or doc_ends == 0:
        result.add_warning(
            "Code does not contain a full \\begin{document}…\\end{document}. "
            "It may not compile as a standalone file."
        )

    # 5. Duplicate node names
    node_names = _NODE_NAME_PATTERN.findall(code)
    seen: set[str] = set()
    for name in node_names:
        if name in seen:
            result.add_error(f"Duplicate node name: ({name}).")
        seen.add(name)

    # 6. References to undefined node names
    # Collect all draw-command references and check against declared nodes
    draw_refs = set()
    for m in _DRAW_REF_PATTERN.finditer(code):
        draw_refs.add(m.group(1))
        draw_refs.add(m.group(2))

    reserved = {"current page", "current bounding box"}
    for ref in draw_refs:
        if ref not in seen and ref not in reserved:
            result.add_warning(
                f"Arrow references node '({ref})' which was not found "
                "among declared \\node definitions."
            )

    # 7. Missing implied TikZ libraries
    declared_libs: set[str] = set()
    for m in _LIBRARY_PATTERN.finditer(code):
        for lib in m.group(1).split(","):
            declared_libs.add(lib.strip())

    for lib, pattern in _IMPLIES.items():
        if lib not in declared_libs and re.search(pattern, code):
            result.add_warning(
                f"Code uses features that suggest the '{lib}' library "
                "but it is not declared in \\usetikzlibrary{{}}."
            )

    # 8. Basic \draw syntax — each \draw must end with semicolon
    draw_stmts = re.findall(r"\\draw[^;\\]*(?:\\[a-zA-Z]+[^;\\]*)*;", code)
    raw_draws = code.count("\\draw")
    if raw_draws > 0 and len(draw_stmts) < raw_draws:
        result.add_warning(
            "Some \\draw commands may be missing their terminating semicolon."
        )

    # 9. No empty node labels (common model mistake)
    empty_labels = re.findall(r"\\node\s*(?:\[[^\]]*\])?\s*\(\w+\)\s*\{\s*\}", code)
    if empty_labels:
        result.add_warning(
            f"Found {len(empty_labels)} node(s) with empty label {{}}. "
            "Consider adding descriptive labels."
        )

    # 10. Detect hard-coded absolute coordinates without units (can cause layout issues)
    bare_coords = re.findall(r"at\s*\(\s*-?\d+\s*,\s*-?\d+\s*\)", code)
    if len(bare_coords) > 6:
        result.add_warning(
            "Many bare integer coordinates detected. "
            "Using the 'positioning' library with relative placement "
            "produces more maintainable diagrams."
        )

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_balanced_braces(code: str, result: ValidationResult) -> None:
    """Check that curly braces are balanced, ignoring commented-out lines."""
    depth = 0
    in_comment = False
    for i, ch in enumerate(code):
        if ch == "\n":
            in_comment = False
            continue
        if ch == "%" and not in_comment:
            in_comment = True
            continue
        if in_comment:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                result.add_error(
                    f"Unexpected closing brace '}}' at character position {i}."
                )
                depth = 0  # reset to continue scanning
    if depth != 0:
        result.add_error(
            f"Unbalanced braces: {depth} more '{{' than '}}' in the document."
        )


def format_validation_report(vr: ValidationResult) -> str:
    """Return a human-readable validation report string."""
    lines = []
    if vr.is_valid and not vr.warnings:
        lines.append("✅ TikZ code passed all validation checks.")
    elif vr.is_valid:
        lines.append("✅ TikZ code is valid (with minor warnings).")
    else:
        lines.append("❌ TikZ code has errors that need correction.")

    for err in vr.errors:
        lines.append(f"  ERROR   : {err}")
    for warn in vr.warnings:
        lines.append(f"  WARNING : {warn}")

    return "\n".join(lines)
