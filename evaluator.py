def score_results(results):
    total = 0
    ok = 0

    for r in results:
        for bit, right in r["correct"].items():
            total += 1
            if right:
                ok += 1

    return ok / total if total > 0 else 0.0