"""Core Jupyter Notebook → PDF conversion. Jupyter Notebook → PDF 转换核心逻辑。"""

import asyncio
import copy
import os
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import nbformat
from nbconvert.exporters.webpdf import WebPDFExporter
from nbconvert.preprocessors import Preprocessor

from nb2pdf.images import embed_local_images

MAX_STREAM_LINES = 40
MAX_TEXT_CHARS = 2500
MAX_TRACEBACK_LINES = 20
# Playwright navigation timeout (ms); networkidle is unreliable with MathJax CDN
# Playwright 导航超时（毫秒）；加载 MathJax CDN 时 networkidle 容易永远等不到
PAGE_GOTO_TIMEOUT_MS = 120_000


class TruncateOutputPreprocessor(Preprocessor):
    """Keep figures/images; truncate long stdout and text/plain output.
    保留图表/图片，截断过长的 stdout 与 text/plain 输出。"""

    enabled = True

    def preprocess_cell(self, cell, resources, cell_index):
        if cell.cell_type != "code" or not cell.get("outputs"):
            return cell, resources

        new_outputs = []
        for output in cell.outputs:
            otype = output.get("output_type")

            if otype == "stream":
                text = output.text if isinstance(output.text, str) else "".join(output.text)
                lines = text.splitlines(keepends=True)
                if len(lines) > MAX_STREAM_LINES:
                    head = "".join(lines[:MAX_STREAM_LINES])
                    note = (
                        f"\n\n… [输出已截断 / output truncated: {len(lines)} lines total, "
                        f"showing first {MAX_STREAM_LINES}; see .ipynb for full content] …\n"
                    )
                    out = copy.copy(output)
                    out["text"] = head + note
                    new_outputs.append(out)
                else:
                    new_outputs.append(output)

            elif otype == "error":
                tb = output.get("traceback", [])
                if len(tb) > MAX_TRACEBACK_LINES:
                    out = copy.copy(output)
                    out["traceback"] = tb[:MAX_TRACEBACK_LINES] + [
                        f"... [traceback 已截断 / traceback truncated: {len(tb)} lines total] ..."
                    ]
                    new_outputs.append(out)
                else:
                    new_outputs.append(output)

            elif otype in ("execute_result", "display_data"):
                data = dict(output.get("data", {}))
                if "image/png" in data or "image/jpeg" in data:
                    data.pop("text/plain", None)
                keep = {
                    k: v
                    for k, v in data.items()
                    if k.startswith("image/") or k in ("text/plain", "text/html")
                }
                if "text/plain" in keep:
                    tp = keep["text/plain"]
                    text = tp if isinstance(tp, str) else "".join(tp)
                    if len(text) > MAX_TEXT_CHARS:
                        keep["text/plain"] = (
                            text[:MAX_TEXT_CHARS]
                            + f"\n… [text/plain 已截断 / text/plain truncated: was {len(text)} chars] …"
                        )
                if keep:
                    out = copy.copy(output)
                    out["data"] = keep
                    new_outputs.append(out)

            else:
                new_outputs.append(output)

        cell.outputs = new_outputs
        return cell, resources


def _font_css() -> str:
    if sys.platform == "win32":
        return """
@font-face {
  font-family: "MSYH";
  src: url("file:///C:/Windows/Fonts/msyh.ttc") format("truetype");
  font-display: block;
}
@font-face {
  font-family: "ConsolasLocal";
  src: url("file:///C:/Windows/Fonts/consola.ttf") format("truetype");
  font-display: block;
}
body, .jp-Notebook, .jp-Cell, .markdown-body, .jp-RenderedHTMLCommon,
div.cell, div.inner_cell, .text_cell_render {
  font-family: "MSYH", "Microsoft YaHei", "SimHei", sans-serif !important;
}
pre, code, .highlight, .highlight pre, .cm-line, .jp-InputArea pre,
div.input_area pre, div.output_area pre {
  font-family: "ConsolasLocal", "Consolas", monospace !important;
}
"""
    return """
body, .jp-Notebook, .jp-Cell, .markdown-body, .jp-RenderedHTMLCommon,
div.cell, div.inner_cell, .text_cell_render {
  font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", sans-serif !important;
}
pre, code, .highlight, .highlight pre, .cm-line, .jp-InputArea pre,
div.input_area pre, div.output_area pre {
  font-family: "DejaVu Sans Mono", "Consolas", monospace !important;
}
"""


PRINT_CSS = (
    """
<style>
"""
    + _font_css()
    + """
body, .jp-Notebook, .jp-Cell, .markdown-body, .jp-RenderedHTMLCommon,
div.cell, div.inner_cell, .text_cell_render {
  font-size: 11pt;
  line-height: 1.55;
}
pre, code, .highlight, .highlight pre, .cm-line, .jp-InputArea pre,
div.input_area pre, div.output_area pre {
  font-size: 9pt !important;
}
.jp-OutputArea-output pre, div.output_area pre {
  font-size: 8.5pt !important;
  color: #444 !important;
  background: #f7f7f7 !important;
  border-left: 3px solid #ccc;
  padding: 6px 10px !important;
  max-height: none !important;
  overflow: visible !important;
}
.jp-Cell, div.cell {
  page-break-inside: auto;
  margin-bottom: 1em;
}
.jp-Cell-inputWrapper, div.input_area {
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 0.4em;
  padding: 4px;
}
.jp-OutputArea, div.output_area { margin-top: 0.3em; }
.nb2pdf-img-stack, .text_cell_render, div.output_area, div.cell {
  overflow: visible !important;
}
.nb2pdf-img-stack {
  display: block !important;
  line-height: 0 !important;
  font-size: 0 !important;
  margin: 0 auto 8px !important;
}
.nb2pdf-img-stack .nb2pdf-strip {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  height: auto !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  vertical-align: top !important;
  object-fit: contain !important;
  page-break-inside: avoid !important;
  break-inside: avoid-page !important;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
img.nb2pdf-img:not(.nb2pdf-strip), .jp-OutputArea img, div.output_area img, .text_cell_render img {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  height: auto !important;
  object-fit: contain !important;
  page-break-inside: avoid !important;
  break-inside: avoid-page !important;
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
  margin: 0 auto 8px !important;
}
h1 { font-size: 20pt; border-bottom: 2px solid #333; padding-bottom: 4px; }
h2 { font-size: 16pt; }
h3 { font-size: 13pt; }
</style>
"""
)

WAIT_JS = """
async () => {
  if (document.fonts && document.fonts.ready) await document.fonts.ready;
  if (typeof MathJax !== 'undefined' && MathJax.Hub) {
    await new Promise(r => MathJax.Hub.Queue(r));
  }
  await Promise.all(
    Array.from(document.images).map(img =>
      img.complete ? Promise.resolve() :
      new Promise(r => { img.onload = img.onerror = r; })
    )
  );

  // Large embedded images not split in Python: detect panels and slice
  // 未在 Python 侧切片的内嵌大图：按常见分辨率识别拼接帧后切片
  function detectPanelHeight(w, h) {
    if (h < 3000) return null;
    const ideal = Math.round(w * 9 / 16);
    const common = [ideal, 1440, 2160, 1080, 1920, 1280, 720].filter((v, i, a) => v > 0 && a.indexOf(v) === i);
    for (const ph of common) {
      if (h % ph === 0) {
        const n = h / ph;
        if (n >= 2 && n <= 30) return ph;
      }
    }
    return null;
  }

  for (const img of Array.from(document.querySelectorAll('img'))) {
    if (img.classList.contains('nb2pdf-strip')) continue;
    const w = img.naturalWidth, h = img.naturalHeight;
    if (!w || !h) continue;

    const panelH = detectPanelHeight(w, h);
    if (!panelH) {
      img.style.display = 'block';
      img.style.width = '100%';
      img.style.maxWidth = '100%';
      img.style.height = 'auto';
      img.style.pageBreakInside = 'avoid';
      img.style.breakInside = 'avoid-page';
      img.style.margin = '0 auto 8px';
      continue;
    }

    const src = img.src;
    const tmp = new Image();
    await new Promise((ok, no) => { tmp.onload = ok; tmp.onerror = no; tmp.src = src; });
    const panelCount = h / panelH;
    const stack = document.createElement('div');
    stack.className = 'nb2pdf-img-stack';
    stack.style.cssText = 'display:block;line-height:0;font-size:0;margin:0 auto 8px;overflow:visible;';
    stack.dataset.nb2pdfPanelH = String(panelH);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    for (let i = 0; i < panelCount; i++) {
      const y = i * panelH;
      canvas.width = w;
      canvas.height = panelH;
      ctx.clearRect(0, 0, w, panelH);
      ctx.drawImage(tmp, 0, y, w, panelH, 0, 0, w, panelH);
      const strip = document.createElement('img');
      strip.src = canvas.toDataURL('image/png');
      strip.className = 'nb2pdf-img nb2pdf-strip';
      strip.dataset.nb2pdfPanelIndex = String(i + 1);
      strip.style.cssText = 'display:block;width:100%;max-width:100%;height:auto;margin:0;padding:0;border:0;vertical-align:top;page-break-inside:avoid;break-inside:avoid-page;';
      stack.appendChild(strip);
    }
    img.replaceWith(stack);
  }

  await new Promise(r => setTimeout(r, 2000));
}
"""


def inject_css(html: str) -> str:
    if "</head>" in html:
        return html.replace("</head>", PRINT_CSS + "</head>", 1)
    return PRINT_CSS + html


def _run_playwright_windows(self, html):
    """Run Playwright on main thread (Windows) for text-based PDF.
    Windows: 主线程运行 Playwright，生成文本型 PDF。"""
    html = inject_css(html)
    html_dir = getattr(self, "notebook_dir", None) or tempfile.gettempdir()

    async def _render(html_path):
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = None
        try:
            args = list(self.browser_args)
            if self.disable_sandbox:
                args.append("--no-sandbox")

            launch = {
                "handle_sigint": False,
                "handle_sigterm": False,
                "handle_sighup": False,
                "args": args,
            }
            if sys.platform == "win32" and os.path.exists(
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            ):
                launch["channel"] = "chrome"

            browser = await pw.chromium.launch(**launch)
            page = await browser.new_page()
            nav_timeout = max(
                getattr(self, "page_render_timeout", 8000) * 15,
                PAGE_GOTO_TIMEOUT_MS,
            )
            page.set_default_navigation_timeout(nav_timeout)
            page.set_default_timeout(nav_timeout)
            await page.emulate_media(media="print")

            file_url = Path(html_path).resolve().as_uri()
            # "load" + WAIT_JS (MathJax/fonts/images); avoid "networkidle" on file:// + CDN
            # 用 load 配合 WAIT_JS 等待渲染；file:// 加载 CDN 时 networkidle 易超时
            await page.goto(file_url, wait_until="load", timeout=nav_timeout)
            await page.evaluate(WAIT_JS)
            await page.wait_for_timeout(max(self.page_render_timeout, 3000))

            pdf_params = {"print_background": True, "tagged": False}
            if not self.paginate:
                dims = await page.evaluate(
                    """() => {
                    const r = document.body.getBoundingClientRect();
                    return { width: Math.ceil(r.width)+1, height: Math.ceil(r.height)+1 };
                }"""
                )
                pdf_params["width"] = min(dims["width"], 200 * 72)
                pdf_params["height"] = min(dims["height"], 200 * 72)

            return await page.pdf(**pdf_params)
        finally:
            if browser is not None:
                await browser.close()
            await pw.stop()

    html_path = os.path.join(html_dir, ".nbconvert_export.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        return asyncio.run(_render(html_path))
    finally:
        try:
            os.unlink(html_path)
        except OSError:
            pass


if sys.platform == "win32":
    WebPDFExporter.run_playwright = _run_playwright_windows


class StudyPDFExporter(WebPDFExporter):
    """PDF exporter tuned for reading/printing. 面向阅读的 PDF 导出。"""

    def _init_preprocessors(self):
        super()._init_preprocessors()
        self.register_preprocessor(TruncateOutputPreprocessor(), enabled=True)

    def from_notebook_node(self, nb, resources=None, **kw):
        html, resources = super(WebPDFExporter, self).from_notebook_node(
            nb, resources=resources, **kw
        )
        nb_dir = getattr(self, "notebook_dir", None)
        if nb_dir:
            html = embed_local_images(html, nb_dir)
        self.log.info("Building PDF")
        pdf_data = self.run_playwright(html)
        self.log.info("PDF successfully created")
        return pdf_data, resources


def prepare_notebook(nb):
    proc = TruncateOutputPreprocessor()
    nb, _ = proc(nb, {})
    return nb


def convert(notebook_path: str, output_path: str | None = None) -> str:
    """Convert notebook to PDF; return output path. 转换 notebook 为 PDF，返回输出文件路径。"""
    notebook_path = os.path.abspath(notebook_path)
    if output_path:
        output_path = os.path.abspath(output_path)
    else:
        base, _ = os.path.splitext(notebook_path)
        output_path = base + ".pdf"

    if not os.path.isfile(notebook_path):
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    with open(notebook_path, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    nb = prepare_notebook(nb)
    nb_dir = os.path.dirname(notebook_path)
    resources = {
        "metadata": {
            "path": nb_dir,
            "name": os.path.basename(notebook_path),
        }
    }

    exporter = StudyPDFExporter()
    exporter.notebook_dir = nb_dir
    exporter.template_name = "classic"
    exporter.embed_images = True
    exporter.mathjax_url = (
        "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/latest.js"
        "?config=TeX-AMS_SVG-full,Safe"
    )
    exporter.page_render_timeout = 15000
    pdf_data, _ = exporter.from_notebook_node(nb, resources=resources)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    tmp = output_path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(pdf_data)
    try:
        os.replace(tmp, output_path)
    except PermissionError:
        output_path = output_path.replace(".pdf", "_new.pdf")
        os.replace(tmp, output_path)

    return output_path


def install_browser() -> int:
    """Install Playwright Chromium browser. 安装 Playwright Chromium 浏览器。"""
    import subprocess

    print("正在安装 Chromium，请稍候… / Installing Chromium, please wait…")
    if getattr(sys, "frozen", False):
        from playwright.__main__ import main as pw_main

        old_argv = sys.argv
        sys.argv = ["playwright", "install", "chromium"]
        try:
            pw_main()
            return 0
        except SystemExit as exc:
            code = exc.code
            return int(code) if isinstance(code, int) else (0 if code is None else 1)
        finally:
            sys.argv = old_argv

    return subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"])
