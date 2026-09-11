"""CI/报告状态核查脚本（无需鉴权）。

用法：python scripts/check_ci_status.py
功能：
  1. 检查 GitHub Pages 上的 Allure 在线报告是否可访问；
  2. 抓取最新一次 Actions 运行页面，统计关键信息（通过/失败/跳过）；
  3. 若 GitHub API 配额可用，额外输出各 Check Run 的失败摘要（失败用例清单）。
"""
import json
import re
import sys
import urllib.request

OWNER, REPO = "Oxob-hue", "auto-test-framework"
PAGES_URL = f"https://{OWNER}.github.io/{REPO}/"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
BADGE = f"https://github.com/{OWNER}/{REPO}/actions/workflows/ci.yml/badge.svg"


def get(url: str, timeout: int = 25):
    """用标准库发请求（避免额外依赖），返回 (status, headers, text)。"""
    req = urllib.request.Request(url, headers={"User-Agent": "ci-check/1.0",
                                              "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return resp.status, dict(resp.headers), raw.decode("utf-8", "ignore")


def main() -> int:
    print("=== 1) Allure 在线报告（GitHub Pages） ===")
    for url in (PAGES_URL, PAGES_URL + "index.html"):
        try:
            status, _, text = get(url)
            title = re.search(r"<title>(.*?)</title>", text)
            print(f"  {url} -> HTTP {status} | len={len(text)} | allure={'allure' in text.lower()} "
                  f"| title={title.group(1) if title else '?'}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {url} -> ERR {type(exc).__name__}: {str(exc)[:80]}")

    print("=== 2) CI 徽章状态 ===")
    try:
        _, _, svg = get(BADGE)
        title = re.search(r"<title>(.*?)</title>", svg)
        print("  ", title.group(1) if title else "无法解析")
    except Exception as exc:  # noqa: BLE001
        print("   ERR", type(exc).__name__, str(exc)[:80])

    print("=== 3) 最新运行概况（API，可能受匿名配额限制） ===")
    try:
        _, _, body = get(f"{API}/actions/runs?per_page=1")
        run = json.loads(body)["workflow_runs"][0]
        print(f"  run #{run['run_number']} sha={run['head_sha'][:7]} {run['status']}/{run['conclusion']}")
        print("  ", run["html_url"])
        _, _, jobs_body = get(run["jobs_url"])
        for job in json.loads(jobs_body).get("jobs", []):
            print(f"   - {job['name']}: {job['conclusion']}")
        _, _, checks_body = get(f"{API}/commits/{run['head_sha']}/check-runs")
        for check in json.loads(checks_body).get("check_runs", []):
            summary = (check.get("output") or {}).get("summary") or ""
            if summary:
                print(f"   [summary] {check['name']}:")
                print("   " + "\n   ".join(summary.splitlines()[:20]))
    except Exception as exc:  # noqa: BLE001
        print("   API 不可用（可能配额用尽）:", type(exc).__name__, str(exc)[:100])
    return 0


if __name__ == "__main__":
    sys.exit(main())
