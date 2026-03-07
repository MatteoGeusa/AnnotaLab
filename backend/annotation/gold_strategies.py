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
    Percentage-based evaluation (DEFAULT).
    Excludes the annotator if their cumulative gold accuracy drops
    below `min_accuracy_required` after at least `min_gold_before_eval` gold tasks.
    
    Config keys used:
        - min_accuracy_required: float (default 0.6)
        - min_gold_before_eval: int (default 3)
        - continuous_exclusion: bool (default False) — if False, only logs but doesn't exclude
    """
    min_accuracy = gold_config.get('min_accuracy_required', 0.6)
    min_gold = gold_config.get('min_gold_before_eval', 3)
    continuous = gold_config.get('continuous_exclusion', False)

    # Update cumulative accuracy
    total = enrollment.gold_tasks_completed
    prev_acc = enrollment.gold_accuracy or 0.0
    prev_correct = prev_acc * (total - 1) if total > 1 else 0
    current_correct = prev_correct + (1 if is_correct else 0)
    new_acc = current_correct / total if total > 0 else 0.0

    enrollment.gold_accuracy = new_acc

    # Evaluate
    if continuous and total >= min_gold and new_acc < min_accuracy:
        return True, f"Accuracy {new_acc:.1%} below threshold {min_accuracy:.0%} after {total} gold tasks."
    
    return False, None


def evaluate_strikes(enrollment, gold_config, is_correct):
    """
    Strike-based evaluation.
    Excludes the annotator after `max_strikes` consecutive wrong answers.
    A correct answer resets the strike counter to 0.
    
    Config keys used:
        - max_strikes: int (default 3)
        - continuous_exclusion: bool (default False)
    """
    max_strikes = gold_config.get('max_strikes', 3)
    continuous = gold_config.get('continuous_exclusion', False)

    # Update accuracy (always tracked for reporting)
    total = enrollment.gold_tasks_completed
    prev_acc = enrollment.gold_accuracy or 0.0
    prev_correct = prev_acc * (total - 1) if total > 1 else 0
    current_correct = prev_correct + (1 if is_correct else 0)
    new_acc = current_correct / total if total > 0 else 0.0
    enrollment.gold_accuracy = new_acc

    # Strike logic
    if is_correct:
        enrollment.gold_strikes = 0
    else:
        enrollment.gold_strikes += 1

    if continuous and enrollment.gold_strikes >= max_strikes:
        return True, f"{enrollment.gold_strikes} consecutive wrong answers (max: {max_strikes})."

    return False, None


def evaluate_hybrid(enrollment, gold_config, is_correct):
    """
    Hybrid evaluation: combines percentage AND strikes.
    Excludes if EITHER condition is met:
    - Accuracy below threshold after min_gold_before_eval
    - max_strikes consecutive wrong answers
    
    Config keys used: all from percentage + strikes.
    """
    excluded_pct, reason_pct = evaluate_percentage(enrollment, gold_config, is_correct)
    
    # We need to handle strikes separately since evaluate_percentage already updated accuracy
    max_strikes = gold_config.get('max_strikes', 3)
    continuous = gold_config.get('continuous_exclusion', False)

    if is_correct:
        enrollment.gold_strikes = 0
    else:
        enrollment.gold_strikes += 1

    excluded_strikes = continuous and enrollment.gold_strikes >= max_strikes
    reason_strikes = f"{enrollment.gold_strikes} consecutive wrong (max: {max_strikes})." if excluded_strikes else None

    if excluded_pct:
        return True, reason_pct
    if excluded_strikes:
        return True, reason_strikes
    return False, None


# --- STRATEGY REGISTRY ---

STRATEGIES = {
    'percentage': evaluate_percentage,
    'strikes': evaluate_strikes,
    'hybrid': evaluate_hybrid,
}


def get_strategy(strategy_name):
    """
    Returns the evaluation function for the given strategy name.
    Falls back to 'percentage' if the name is not recognized.
    
    Usage:
        strategy = get_strategy(gold_config.get('evaluation_strategy', 'percentage'))
        should_exclude, reason = strategy(enrollment, gold_config, is_correct)
    """
    return STRATEGIES.get(strategy_name, evaluate_percentage)


def check_gold_correctness(annotation_result, gold_solution):
    """
    Compares the annotator's result against the gold solution.
    Currently checks classification match. Can be extended for span-level evaluation.
    
    Returns: bool (True if correct)
    """
    if not gold_solution:
        return False
    
    user_class = annotation_result.get('classification')
    gold_class = gold_solution.get('classification')
    
    if user_class is None or gold_class is None:
        return False
    
    return user_class == gold_class
