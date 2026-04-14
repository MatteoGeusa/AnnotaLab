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


def check_gold_correctness(annotation_result, gold_solution):
    """
    Compares the annotator's result against the gold solution.

    Gold solutions are **partial**: only the component keys present in the
    gold are evaluated. This means a gold with only 'classification' skips
    span evaluation entirely, and vice versa.

    Supports both result formats:
      - New (component-based):  {"classification": "Yes", "span_highlight": [...]}
      - Legacy (flat):          {"classification": "Yes", "spans": [...]}

    Returns: bool -- True if ALL evaluated components are correct.
    """
    if not gold_solution:
        return False

    # Guard: annotation_result may be None if not yet submitted
    if not annotation_result or not isinstance(annotation_result, dict):
        return False

    # -- Classification check (only if gold provides it) ---------------------
    if 'classification' in gold_solution:
        gold_class = gold_solution['classification']
        user_class = annotation_result.get('classification')
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

