"""把 docs/export/html/*.html 打印为 PDF（Selenium + Chrome DevTools Protocol）。

为什么不用命令行 --print-to-pdf：当机器上已有 Edge 进程时，新命令行实例可能被
转发到既有进程而静默不产出文件；改用 CDP 的 Page.printToPDF 可直接拿到 PDF 字节流。

用法：
    python scripts/print_pdf.py
产出：
    docs/export/测试计划.pdf、测试用例表.pdf、测试报告.pdf
"""
import base64
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from common.config_util import get_config

ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = ROOT / "docs" / "export" / "html"
OUT_DIR = ROOT / "docs" / "export"

DOCS = ["测试计划", "测试用例表", "测试报告"]


def main() -> int:
    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    browser = webdriver.Edge(service=EdgeService(get_config("web", "driver_path")),
                             options=options)
    try:
        for name in DOCS:
            html_file = HTML_DIR / f"{name}.html"
            if not html_file.exists():
                print("SKIP(无 HTML):", name)
                continue
            browser.get(html_file.as_uri())
            time.sleep(1.5)  # 等字体/样式就绪
            result = browser.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "preferCSSPageSize": True,
            })
            pdf_path = OUT_DIR / f"{name}.pdf"
            pdf_path.write_bytes(base64.b64decode(result["data"]))
            print(f"PDF: {pdf_path.relative_to(ROOT)} ({pdf_path.stat().st_size} bytes)")
    finally:
        browser.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
