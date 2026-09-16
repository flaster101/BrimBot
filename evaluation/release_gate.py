"""Fail-closed qualification, distinct from research model agreement."""
import argparse
import json
from pathlib import Path

def failures(report: dict) -> list[str]:
    if not isinstance(report,dict): return ["report_format"]
    issues=[]
    for flag in ["independent_ground_truth", "test_untouched_before_final_evaluation", "android_parity_passed", "device_lifecycle_passed"]:
        if report.get(flag) is not True: issues.append(flag)
    for metric,minimum in [("critical_hazard_recall_lower95",.98),("safe_path_precision_lower95",.995),("state_precision_lower95",.995)]:
        value=report.get(metric)
        if type(value) not in (int,float) or not minimum<=value<=1: issues.append(metric)
    for metric,minimum in [("closed_loop_runs",20),("tested_devices",2)]:
        value=report.get(metric)
        if type(value) is not int or value<minimum: issues.append(metric)
    value=report.get("gesture_outside_gameplay")
    if type(value) is not int or value!=0: issues.append("gesture_outside_gameplay")
    counts=report.get("critical_class_counts")
    if not isinstance(counts,dict) or any(type(counts.get(k)) is not int or counts[k]<100 for k in ["gap","rock","crusher","projectile"]):
        issues.append("critical_class_coverage")
    return issues

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("report",type=Path);a=p.parse_args()
    problems=failures(json.loads(a.report.read_text()))
    print(json.dumps(dict(qualified=not problems,failed=problems),indent=2))
    raise SystemExit(bool(problems))
