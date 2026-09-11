"""CI 失败取证助手：用本地只读令牌下载 GitHub Actions 的 Job 日志与 Allure 产物。

用途：CI 失败时快速拿到失败用例清单与上下文（无需手动到网页下载 Artifact）。
令牌从项目根目录 `.gh_token` 读取（已在 .gitignore 中，不会入库）；
需要权限：Actions: Read-only + Contents: Read-only。

用法：
    python scripts/ci_fetch_failures.py                 # 最新一次运行
    python scripts/ci_fetch_failures.py --run 34561270062 --logs --artifacts
产物：
    .ci_downloads/   （已加入 .gitignore）
"""
import argparse
import json
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / ".gh_token"
OWNER, REPO = "Oxob-hue", "auto-test-framework"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
KEYWORDS = ("FAILED", "ERROR", "short test summary", " passed", " failed", "Traceback",
            "Exception", "assert", "Error:")


def read_token() -> str:
    """读取本地只读令牌：支持 `.gh_token` 为文件，或为存放令牌文件的目录。"""
    candidates = []
    if TOKEN_FILE.is_file():
        candidates.append(TOKEN_FILE)
    elif TOKEN_FILE.is_dir():
        candidates += [p for p in sorted(TOKEN_FILE.iterdir()) if p.is_file()]
    for path in candidates:
        token = path.read_text(encoding="utf-8", errors="ignore").strip()
        if token:
            return token
    raise SystemExit("未找到可用令牌：请在 .gh_token 文件（或该目录下的文本文件）中写入只读 PAT")


def api_get(url: str, accept: str = "application/vnd.github+json") -> bytes:
    """带令牌请求 GitHub API（自动跟随到对象存储的签名重定向）。"""
    resp = requests.get(url, headers={
        "Authorization": f"Bearer {read_token()}",
        "Accept": accept,
        "User-Agent": "ci-fetch-failures/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }, timeout=120, allow_redirects=True)
    if resp.status_code >= 400:
        raise SystemExit(f"API 请求失败 {resp.status_code}: {url} -> {resp.text[:200]}")
    return resp.content


def safe_name(text: str) -> str:
    return re.sub(r"[^\w\-.]+", "_", text)[:60]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", help="run id，缺省取最新一次")
    parser.add_argument("--logs", action="store_true", help="下载失败 Job 的日志并打印关键行")
    parser.add_argument("--artifacts", action="store_true", help="下载该运行的全部 Artifact")
    parser.add_argument("--out", default=str(ROOT / ".ci_downloads"))
    args = parser.parse_args()

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    run_id = args.run
    if not run_id:
        runs = json.loads(api_get(f"{API}/actions/runs?per_page=1"))["workflow_runs"]
        run = runs[0]
        run_id = run["id"]
        print(f"最新运行 #{run['run_number']} sha={run['head_sha'][:7]} -> {run['conclusion']}")
        print(run["html_url"])

    jobs = json.loads(api_get(f"{API}/actions/runs/{run_id}/jobs"))["jobs"]
    for job in jobs:
        print(f"\n[{job['name']}] {job['conclusion']} (id={job['id']})")
        if not args.logs or job["conclusion"] not in ("failure", "cancelled", "timed_out"):
            continue
        try:
            raw = api_get(f"{API}/actions/jobs/{job['id']}/logs")
            log = raw.decode("utf-8", "ignore")
            path = outdir / f"job-{job['id']}-{safe_name(job['name'])}.log"
            path.write_text(log, encoding="utf-8")
            print(f"  日志已保存: {path.relative_to(ROOT)} （{len(log)} 字符）")
            hits = [line for line in log.splitlines() if any(k in line for k in KEYWORDS)]
            print("  --- 关键行（尾部 50 行）---")
            for line in hits[-50:]:
                print("   ", line[:200])
        except Exception as exc:  # noqa: BLE001
            print("  日志下载失败:", type(exc).__name__, str(exc)[:120])

    if args.artifacts:
        arts = json.loads(api_get(f"{API}/actions/runs/{run_id}/artifacts"))["artifacts"]
        for art in arts:
            try:
                blob = api_get(art["archive_download_url"])
                target = outdir / f"{safe_name(art['name'])}.zip"
                target.write_bytes(blob)
                print(f"  Artifact 已下载: {target.relative_to(ROOT)} （{len(blob)} bytes）")
            except Exception as exc:  # noqa: BLE001
                print(f"  Artifact {art['name']} 下载失败:", type(exc).__name__, str(exc)[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
