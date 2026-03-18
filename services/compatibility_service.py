def compatibility_score(distance, max_distance):
    """
    BUG 3 FIX: the original formula 1/(1+distance)*100 never produces a
    meaningful 0–100 range in practice:

        distance=0  → 100   (only for an exact clone)
        distance=1  →  50
        distance=10 →   9
        distance=100→   1

    For real spec vectors the distances are in the hundreds or thousands
    (squared L2), so every alternative scored near-zero — even genuinely
    close matches looked bad.

    Fix: normalise against the worst distance in the current result set
    so the closest neighbour maps to 100 and the farthest maps to 0.
    This gives a proper relative ranking on a 0–100 scale.

    Args:
        distance:     L2 distance of this result
        max_distance: largest distance across all results in this search
    """

    if max_distance == 0:
        # all candidates are identical clones → all score 100
        return 100.0

    score = (1.0 - distance / max_distance) * 100.0

    return round(max(0.0, score), 2)