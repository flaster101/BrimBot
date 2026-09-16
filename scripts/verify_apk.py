"""Check that the signed release contains the tested model and honest preview status."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("apk",type=Path)
    args=parser.parse_args()
    expected=json.loads(Path("models/release/manifest.json").read_text())
    with ZipFile(args.apk) as archive:
        model=archive.read("assets/path-candidate.onnx")
        status=json.loads(archive.read("assets/release-status.json"))
        digest=hashlib.sha256(model).hexdigest()
        if digest!=expected["sha256"] or digest!=status["model_sha256"]:
            raise SystemExit("APK model differs from tested model")
        if status["qualified"] is not False or expected["qualified"] is not False:
            raise SystemExit("This preview cannot claim gameplay qualification")
        names=archive.namelist()
        if any(n.lower().endswith((".jks",".keystore",".pt")) or "parity.json" in n for n in names):
            raise SystemExit("Unexpected private/training/test artifact in release")
        for name in ["Apache-2.0.txt","ONNX-Runtime-LICENSE.txt","ONNX-Runtime-ThirdPartyNotices.txt"]:
            if not archive.read("assets/licenses/"+name): raise SystemExit("Missing license")
    report=dict(apk=args.apk.name,version=status["version"],bytes=args.apk.stat().st_size,
        sha256=hashlib.sha256(args.apk.read_bytes()).hexdigest(),model_sha256=digest,
        model_bytes=len(model),qualified=False,packaged_model_matches=True)
    Path("docs/experiments/apk.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
