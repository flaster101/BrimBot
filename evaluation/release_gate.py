"""Fail-closed qualification, distinct from research model agreement."""
import argparse
import json
from pathlib import Path

def failures(report: dict) -> list[str]:
    issues=[]
    for flag in ["independent_ground_truth", "test_untouched_before_final_evaluation", "android_parity_passed", "device_lifecycle_passed"]:
        if report.get(flag) is not True: issues.append(flag)
    for metric,minimum in [("critical_hazard_recall_lower95",.98),("safe_path_precision_lower95",.995),("state_precision_lower95",.995)]:
        value=report.get(metric)
        if not isinstance(value,(int,float)) or not minimum<=value<=1: issues.append(metric)
    if report.get("closed_loop_runs",0)<20: issues.append("closed_loop_runs")
    if report.get("tested_devices",0)<2: issues.append("tested_devices")
    if report.get("gesture_outside_gameplay",None)!=0: issues.append("gesture_outside_gameplay")
    if not isinstance(report.get("critical_class_counts"),dict) or any(report.get("critical_class_counts",{}).get(k,0)<100 for k in ["gap","rock","crusher","projectile"]):
        issues.append("critical_class_coverage")
    return issues

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("report",type=Path);a=p.parse_args()
    problems=failures(json.loads(a.report.read_text()))
    print(json.dumps(dict(qualified=not problems,failed=problems),indent=2))
    raise SystemExit(bool(problems))
