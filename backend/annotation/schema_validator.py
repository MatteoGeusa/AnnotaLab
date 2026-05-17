"""
Annotation Schema Validator
============================
Validates the structure of an annotation_schema dict (parsed from YAML).

Design:
  - Each component type declares its own SPEC (required, optional, forbidden fields).
  - Unknown/forbidden fields on a component raise explicit errors.
  - The validator is called at upload time (admin save_model) before persisting.
  - Returns a list of human-readable error strings; empty list = valid.

Usage:
    from annotation.schema_validator import validate_annotation_schema

    errors = validate_annotation_schema(data)
    if errors:
        raise ValueError("\\n".join(errors))
"""

from typing import Any

# ── Component specifications ─────────────────────────────────────────────────
# Each spec entry:
#   required  – fields that MUST be present
#   optional  – fields that MAY be present
#   (any field not in required ∪ optional is forbidden)

_SPAN_LABEL_SPEC: dict[str, Any] = {
    "required": {"name", "color"},
    "optional": {"hover_hint"},
}

_CLASS_OPTION_SPEC: dict[str, Any] = {
    "required": {"label", "value"},
    "optional": {"hover_hint"},
}

_COMPONENT_SPECS: dict[str, Any] = {
    "span_highlight": {
        "required": {"type", "labels"},
        "optional": set(),
        "children": {
            "labels": _SPAN_LABEL_SPEC,
        },
    },
    "classification": {
        "required": {"type", "options"},
        "optional": {"question", "multi_select"},
        "children": {
            "options": _CLASS_OPTION_SPEC,
        },
    },
}

SUPPORTED_TYPES = set(_COMPONENT_SPECS.keys())


# ── Helpers ──────────────────────────────────────────────────────────────────

def _check_fields(obj: dict[Any, Any], spec: dict[str, Any], path: str) -> list[str]:
    """
    Validate a single dict against required/optional spec.
    Returns a list of error strings.
    """
    errors = []
    allowed = spec["required"] | spec["optional"]

    for field in spec["required"]:
        if field not in obj:
            errors.append(f"[{path}] Missing required field: '{field}'.")

    for field in obj:
        if field not in allowed:
            errors.append(
                f"[{path}] Unknown field '{field}'. "
                f"Allowed: {sorted(allowed)}."
            )

    return errors


def _validate_component(comp: Any, index: int) -> list[str]:
    """Validate a single component entry."""
    errors = []
    path = f"components[{index}]"

    if not isinstance(comp, dict):
        return [f"[{path}] Must be a mapping, got {type(comp).__name__}."]

    comp_type = comp.get("type")
    if not comp_type:
        return [f"[{path}] Missing required field 'type'."]

    if comp_type not in SUPPORTED_TYPES:
        return [
            f"[{path}] Unknown component type '{comp_type}'. "
            f"Supported: {sorted(SUPPORTED_TYPES)}."
        ]

    spec = _COMPONENT_SPECS[comp_type]
    errors += _check_fields(comp, spec, path)

    # Validate children (labels / options)
    for child_key, child_spec in spec.get("children", {}).items():
        children = comp.get(child_key)
        if children is None:
            continue  # already caught as missing required above

        if not isinstance(children, list):
            errors.append(f"[{path}.{child_key}] Must be a list.")
            continue

        if len(children) == 0:
            errors.append(f"[{path}.{child_key}] Must contain at least one entry.")

        for i, child in enumerate(children):
            child_path = f"{path}.{child_key}[{i}]"
            if not isinstance(child, dict):
                errors.append(f"[{child_path}] Must be a mapping.")
                continue
            errors += _check_fields(child, child_spec, child_path)

    return errors


# ── Public API ───────────────────────────────────────────────────────────────

def validate_annotation_schema(data: Any) -> list[str]:
    """
    Validate a parsed annotation_schema dict.

    Returns a list of error strings. Empty list means the schema is valid.

    Checks performed:
      1. Top-level must be a dict with a 'components' list.
      2. No extra root-level keys (span_labels / class_labels are no longer valid).
      3. Each component must match its type's spec exactly (required + optional only).
      4. Child lists (labels / options) validated against their own specs.
    """
    errors = []

    if not isinstance(data, dict):
        return ["Schema must be a YAML mapping at the top level."]

    # 1. Root: only 'components' is allowed
    if "components" not in data:
        errors.append("Missing required root field: 'components'.")

    legacy_keys = {"span_labels", "class_labels"}
    for key in data:
        if key == "components":
            continue
        if key in legacy_keys:
            errors.append(
                f"Root key '{key}' is no longer supported. "
                f"Move it inside the relevant component entry "
                f"(e.g. span_highlight.labels / classification.options)."
            )
        else:
            errors.append(
                f"Unknown root key '{key}'. Only 'components' is allowed at the schema root."
            )

    if errors:
        return errors  # can't go further without a valid components list

    components = data.get("components", [])

    if not isinstance(components, list):
        return ["'components' must be a list."]

    if len(components) == 0:
        return ["'components' must contain at least one entry."]

    for i, comp in enumerate(components):
        errors += _validate_component(comp, i)

    return errors


# ── Gold Solution Validator ───────────────────────────────────────────────────

def _extract_schema_constraints(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Extract validation constraints from a parsed annotation_schema.

    Returns a dict:
        {
            'active_types': {'span_highlight', 'classification'},
            'classification': {'valid_values': {'Yes', 'No', ...}, 'multi_select': False},
            'span_highlight':  {'valid_labels':  {'Actor', 'Action', ...}},
        }
    """
    constraints: dict[str, Any] = {'active_types': set()}

    for comp in schema.get('components', []):
        comp_type = comp.get('type')
        if not comp_type:
            continue
        constraints['active_types'].add(comp_type)

        if comp_type == 'classification':
            constraints['classification'] = {
                'valid_values': {
                    opt.get('value')
                    for opt in comp.get('options', [])
                    if opt.get('value') is not None
                },
                'multi_select': comp.get('multi_select', False),
            }

        elif comp_type == 'span_highlight':
            constraints['span_highlight'] = {
                'valid_labels': {
                    lbl.get('name')
                    for lbl in comp.get('labels', [])
                    if lbl.get('name')
                },
            }

    return constraints


def validate_gold_solution(gold_sol: Any, schema: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Validate a gold_solution dict against the project's annotation_schema.

    The gold_solution format mirrors the result payload exactly:
        {
            "classification": "Yes",
            "span_highlight": [{"start": 12, "end": 28, "label": "Actor", "text": "..."}]
        }
    Keys are component type names; partial solutions (subset of components) are allowed.

    Args:
        gold_sol: The gold solution dict to validate.
        schema:   The parsed annotation_schema dict (from project.annotation_schema).

    Returns:
        (errors, warnings)
        - errors:   Fatal issues → caller should SKIP the gold document.
        - warnings: Non-fatal issues → caller may warn but still accept the document.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(gold_sol, dict):
        return [f"gold_solution must be a dict, got {type(gold_sol).__name__}."], []

    if not gold_sol:
        return ["gold_solution is empty — at least one component key is required."], []

    constraints = _extract_schema_constraints(schema)
    active_types = constraints['active_types']

    # ── 1. Unknown keys (not matching any active component type) ────────────
    for key in gold_sol:
        if key not in active_types:
            if active_types:
                errors.append(
                    f"Unknown key '{key}' in gold_solution. "
                    f"Active component types: {sorted(active_types)}."
                )
            else:
                warnings.append(
                    f"Project has no annotation_schema — cannot validate key '{key}'."
                )

    # ── 2. Classification validation ─────────────────────────────────────────
    if 'classification' in gold_sol and 'classification' in constraints:
        cls_val = gold_sol['classification']
        cls_con = constraints['classification']
        valid_values = cls_con['valid_values']
        multi_select = cls_con['multi_select']

        if multi_select:
            # Must be a list
            if not isinstance(cls_val, list):
                errors.append(
                    f"'classification' must be a list (multi_select=true), "
                    f"got {type(cls_val).__name__}."
                )
            else:
                bad = [v for v in cls_val if v not in valid_values]
                if bad:
                    errors.append(
                        f"'classification' contains invalid value(s) {bad}. "
                        f"Valid: {sorted(v for v in valid_values if v)}."
                    )
        else:
            if not isinstance(cls_val, str):
                errors.append(
                    f"'classification' must be a string, got {type(cls_val).__name__}."
                )
            elif cls_val not in valid_values:
                errors.append(
                    f"'classification' value '{cls_val}' is not a valid option. "
                    f"Valid: {sorted(v for v in valid_values if v)}."
                )

    # ── 3. Span highlight validation ─────────────────────────────────────────
    if 'span_highlight' in gold_sol and 'span_highlight' in constraints:
        spans = gold_sol['span_highlight']
        valid_labels = constraints['span_highlight']['valid_labels']

        if not isinstance(spans, list):
            errors.append(
                f"'span_highlight' must be a list, got {type(spans).__name__}."
            )
        else:
            if len(spans) == 0:
                warnings.append(
                    "'span_highlight' in gold_solution is an empty list — "
                    "any annotator answer (including no spans) will pass this check."
                )
            for i, span_raw in enumerate(spans):

                if not isinstance(span_raw, dict):
                    errors.append(f"span_highlight[{i}] must be a dict.")
                    continue
                
                span: dict[Any, Any] = span_raw

                # Required fields
                for req in ('start', 'end', 'label'):
                    if req not in span:
                        errors.append(
                            f"span_highlight[{i}] missing required field '{req}'."
                        )

                # Label must be valid
                span_label = span.get('label')
                if span_label and valid_labels and span_label not in valid_labels:
                    errors.append(
                        f"span_highlight[{i}] label '{span_label}' is not defined "
                        f"in the schema. Valid labels: {sorted(valid_labels)}."
                    )

                # Sanity: start < end, both non-negative
                start = span.get('start')
                end = span.get('end')
                if (start is not None and end is not None
                        and isinstance(start, int) and isinstance(end, int)):
                    if start < 0:
                        errors.append(f"span_highlight[{i}] 'start' must be >= 0.")
                    if end <= start:
                        errors.append(
                            f"span_highlight[{i}] 'end' ({end}) must be > 'start' ({start})."
                        )

    # ── 4. Component present in gold but not in schema ─────────────────────
    #    (handled above in step 1 — this is a catch-all note)

    # ── 5. Warn if the schema has components with no gold coverage ───────────
    #    (non-fatal: partial gold solutions are allowed)
    for comp_type in active_types:
        if comp_type not in gold_sol:
            warnings.append(
                f"No gold answer provided for component '{comp_type}' "
                f"— only the provided components will be evaluated."
            )

    return errors, warnings

