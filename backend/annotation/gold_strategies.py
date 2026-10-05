"""
Gold Unit Evaluation Strategies
================================
Implements the Strategy pattern for evaluating annotator quality
based on their gold unit performance.

Each strategy is a pure function:
    (enrollment, gold_config, is_correct) -> (should_exclude, reason)

The system ships with default strategies but researchers can configure
which one to use per-project via `gold_config.evaluation_strategy`.
"""


def evaluate_percentage(enrollment, gold_config, is_correct):
    """
    Percentage-based evaluation.
    Excludes the annotator if their cumulative gold accuracy drops
    below `min_accuracy_required` after at least `min_gold_before_eval` gold tasks.
    
    Config keys used:
        - min_accuracy_required: float (default 0.6)
        - min_gold_before_eval: int (default 3)
    """
    min_accuracy = gold_config.get('min_accuracy_required', 0.6)
    min_gold = gold_config.get('min_gold_before_eval', 3)

    # Update cumulative accuracy
    total = enrollment.gold_tasks_completed
    prev_acc = enrollment.gold_accuracy or 0.0
    prev_correct = prev_acc * (total - 1) if total > 1 else 0
    current_correct = prev_correct + (1 if is_correct else 0)
    new_acc = current_correct / total if total > 0 else 0.0

    enrollment.gold_accuracy = new_acc

    # Evaluate: Always exclude if below threshold after min gold tasks
    if total >= min_gold and new_acc < min_accuracy:
        return True, f"Accuracy {new_acc:.1%} below threshold {min_accuracy:.0%} after {total} gold tasks."
    
    return False, None


# --- STRATEGY REGISTRY ---

STRATEGIES = {
    'percentage': evaluate_percentage,
}


def get_strategy(strategy_name='percentage'):
    """
    Returns the evaluation function for the given strategy name.
    Now only supports 'percentage'.
    
    Usage:
        strategy = get_strategy()
        should_exclude, reason = strategy(enrollment, gold_config, is_correct)
    """
    return evaluate_percentage


def check_gold_correctness(annotation_result, gold_solution, schema=None):
    """
    Compares the annotator's result against the gold solution.

    Gold solutions are **partial**: only the component keys present in the
    gold are evaluated. This means a gold with only 'classification' skips
    span evaluation entirely, and vice versa.

    Supports both result formats:
      - New (component-based):  {"classification": "Yes", "span_highlight": [...]}
      - Legacy (flat):          {"classification": "Yes", "spans": [...]}

    If `schema` (the project's annotation_schema) is given, classification
    answers are compared by option value: a gold solution written with the
    display label (e.g. "Conspiracy" instead of "Yes") is mapped to its value
    first. Gold units that bypassed upload validation (uploaded before the
    schema was set, edited in the admin, or left over after a schema change)
    would otherwise fail every annotator who answers them correctly.

    Returns: bool -- True if ALL evaluated components are correct.
    """
    if not gold_solution:
        return False

    # Guard: annotation_result may be None if not yet submitted
    if not annotation_result or not isinstance(annotation_result, dict):
        return False

    # -- Classification check (only if gold provides it) ---------------------
    if 'classification' in gold_solution:
        label_to_value, valid_values = _classification_options(schema)
        gold_class = _normalize_classification(
            gold_solution['classification'], label_to_value, valid_values
        )
        user_class = _normalize_classification(
            annotation_result.get('classification'), label_to_value, valid_values
        )
        if user_class != gold_class:
            return False

    # -- Span highlight check (only if gold provides it) ---------------------
    if 'span_highlight' in gold_solution or 'spans' in gold_solution:
        # Accept both new key (span_highlight) and legacy key (spans)
        gold_spans = gold_solution.get('span_highlight') or gold_solution.get('spans', [])
        user_spans = (
            annotation_result.get('span_highlight')
            or annotation_result.get('spans', [])
        )
        if gold_spans and not _spans_match(user_spans, gold_spans):
            return False

    return True


def _classification_options(schema):
    """
    Returns (label_to_value, valid_values) for the schema's classification
    component, or empty mappings if there is no schema / no such component.
    """
    if not isinstance(schema, dict):
        return {}, set()
    for comp in schema.get('components') or []:
        if isinstance(comp, dict) and comp.get('type') == 'classification':
            options = [o for o in comp.get('options') or [] if isinstance(o, dict)]
            valid_values = {o.get('value') for o in options if o.get('value') is not None}
            label_to_value = {
                o.get('label'): o.get('value')
                for o in options
                if o.get('label') is not None and o.get('value') is not None
            }
            return label_to_value, valid_values
    return {}, set()


def _normalize_classification(answer, label_to_value, valid_values):
    """
    Maps a classification answer to option values so that label and value
    spellings compare equal. A string that is already a valid value is kept
    as is (a value takes precedence over a label with the same text).
    Multi-select answers (lists) become sets, so option order is irrelevant.
    """
    def to_value(item):
        if item in valid_values:
            return item
        return label_to_value.get(item, item)

    if isinstance(answer, (list, tuple)):
        try:
            return frozenset(to_value(a) for a in answer)
        except TypeError:  # unhashable items: fall back to an ordered list
            return [to_value(a) for a in answer]
    try:
        return to_value(answer)
    except TypeError:
        return answer


def _spans_match(user_spans, gold_spans, tolerance=5):
    """
    Checks that every gold span has a matching user span within `tolerance` chars.
    Does NOT require user spans to be a perfect superset (extra spans are allowed).
    """
    for gs in gold_spans:
        found = any(
            s.get('label') == gs.get('label') and
            abs(s.get('start', -999) - gs.get('start', 0)) <= tolerance and
            abs(s.get('end', -999) - gs.get('end', 0)) <= tolerance
            for s in user_spans
        )
        if not found:
            return False
    return True

