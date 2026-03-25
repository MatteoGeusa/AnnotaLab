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
