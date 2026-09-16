"""Publish the already reviewed preview APK using the existing Git credential helper.

No credentials are printed, written to disk, or sent to another host.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import requests

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--tag",required=True);p.add_argument("--notes",type=Path,required=True)
    p.add_argument("--apk",type=Path,required=True);p.add_argument("--commit",required=True)
    a=p.parse_args()
    if a.apk.name!="BrimBot.apk" or not a.apk.is_file(): raise SystemExit("Expected reviewed BrimBot.apk")
    credential=subprocess.run(["git","credential","fill"],input="protocol=https\nhost=github.com\nusername=flaster101\n\n",
                              text=True,capture_output=True,check=True)
    fields=dict(line.split("=",1) for line in credential.stdout.splitlines() if "=" in line)
    token=fields.get("password")
    if not token: raise SystemExit("No authenticated GitHub credential available")
    session=requests.Session();session.headers.update({"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
    base="https://api.github.com/repos/flaster101/BrimBot"
    response=session.get(f"{base}/releases/tags/{a.tag}",timeout=30)
    if response.status_code==404:
        response=session.post(f"{base}/releases",json=dict(tag_name=a.tag,target_commitish=a.commit,
            name=f"BrimBot {a.tag} — observation preview",body=a.notes.read_text(encoding="utf-8"),draft=False,prerelease=True),timeout=30)
    response.raise_for_status(); release=response.json()
    if release.get("prerelease") is not True: raise SystemExit("Observation preview must be a prerelease")
    existing=next((asset for asset in release["assets"] if asset["name"]=="BrimBot.apk"),None)
    if existing:
        asset=existing  # Resume an uncertain upload only after verifying identical content.
    else:
        with a.apk.open("rb") as stream:
            uploaded=session.post(f'https://uploads.github.com/repos/flaster101/BrimBot/releases/{release["id"]}/assets',
                params={"name":"BrimBot.apk"},headers={"Content-Type":"application/vnd.android.package-archive"},data=stream,timeout=180)
        uploaded.raise_for_status(); asset=uploaded.json()
    if asset["size"]!=a.apk.stat().st_size: raise SystemExit("Uploaded asset size mismatch")
    digest=hashlib.sha256(a.apk.read_bytes()).hexdigest()
    if asset.get("digest"):
        if asset["digest"]!="sha256:"+digest: raise SystemExit("GitHub asset digest mismatch; refusing to replace it")
    else:
        # Public download verification has no authenticated session or token.
        with requests.get(asset["browser_download_url"],stream=True,timeout=180) as download:
            download.raise_for_status(); check=hashlib.sha256()
            for chunk in download.iter_content(1024*1024): check.update(chunk)
        if check.hexdigest()!=digest: raise SystemExit("Published download digest mismatch")
    result=dict(release=release["html_url"],apk=asset["browser_download_url"],bytes=asset["size"],
        sha256=digest,tag=a.tag,prerelease=True,remote_digest_verified=True)
    Path("artifacts/published-release.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
