from evaluation.release_gate import failures
import pytest

def test_missing_or_pseudo_metrics_cannot_qualify():
    assert failures({})
    assert failures(dict(pseudo_precision=.999,pseudo_recall=.999,qualified=True))

def test_nan_does_not_qualify():
    assert "critical_hazard_recall_lower95" in failures(dict(critical_hazard_recall_lower95=float("nan")))

@pytest.mark.parametrize("value",[None,True,float("nan"),float("inf"),"100",100.5])
def test_invalid_evidence_counts_fail_closed(value):
    problems=failures(dict(closed_loop_runs=value,tested_devices=value,
        critical_class_counts={k:value for k in ["gap","rock","crusher","projectile"]}))
    assert {"closed_loop_runs","tested_devices","critical_class_coverage"}<=set(problems)

def test_boolean_is_not_a_probability_measurement():
    assert "safe_path_precision_lower95" in failures(dict(safe_path_precision_lower95=True))

def test_non_object_report_is_rejected():
    assert failures([])==["report_format"]
