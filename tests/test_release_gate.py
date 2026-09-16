from evaluation.release_gate import failures

def test_missing_or_pseudo_metrics_cannot_qualify():
    assert failures({})
    assert failures(dict(pseudo_precision=.999,pseudo_recall=.999,qualified=True))

def test_nan_does_not_qualify():
    assert "critical_hazard_recall_lower95" in failures(dict(critical_hazard_recall_lower95=float("nan")))
