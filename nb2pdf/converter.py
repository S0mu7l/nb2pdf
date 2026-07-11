"""Core Jupyter Notebook → PDF conversion. Jupyter Notebook → PDF 转换核心逻辑。"""

import asyncio
import copy
import os
import re
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
# Of MAX_STREAM_LINES, lines kept from the end (final loss/summary lives there)
# MAX_STREAM_LINES 中留给结尾的行数（最终 loss / 总结通常在结尾）
STREAM_TAIL_LINES = 12
MAX_TEXT_CHARS = 2500
# Of MAX_TEXT_CHARS, chars kept from the end (e.g. DataFrame shape footer)
# MAX_TEXT_CHARS 中留给结尾的字符数（如 DataFrame 的形状信息在结尾）
TEXT_TAIL_CHARS = 400
MAX_TRACEBACK_LINES = 20
# Of MAX_TRACEBACK_LINES, lines kept from the end (error message is at the end)
# MAX_TRACEBACK_LINES 中留给结尾的行数（错误类型与消息在最后）
TRACEBACK_TAIL_LINES = 12
# Collapse runs of >= N consecutive similar lines (e.g. "Batch 3/500, Loss: 0.1")
# 连续 ≥N 行同模式输出（如训练循环的 Batch/Loss 行）折叠为首尾几行
RUN_COLLAPSE_MIN = 8
# Key lines kept from suppressed install logs / 压缩安装日志时保留的关键行数上限
INSTALL_LOG_KEEP_LINES = 10
# Playwright navigation timeout (ms); networkidle is unreliable with MathJax CDN
# Playwright 导航超时（毫秒）；加载 MathJax CDN 时 networkidle 容易永远等不到
PAGE_GOTO_TIMEOUT_MS = 120_000


_TRUNC_NOTE_MARK = "output truncated"
_SHAPE_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_SHAPE_BAR_RE = re.compile(r"[█▉▊▋▌▍▎▏]+|[=>\-.]{4,}")
_SHAPE_WS_RE = re.compile(r"\s+")


def _apply_carriage_returns(text: str) -> str:
    """Emulate terminal \\r overwrite: keep only the final frame of each line.
    模拟终端 \\r 覆盖行为：进度条（tqdm/keras 等）每行只保留最后一帧。"""
    if "\r" not in text:
        return text
    text = text.replace("\r\n", "\n")
    lines = []
    for line in text.split("\n"):
        if "\r" in line:
            segs = [s for s in line.split("\r") if s]
            line = segs[-1] if segs else ""
        lines.append(line)
    return "\n".join(lines)


def _line_shape(line: str) -> str:
    """Mask numbers/bars/whitespace so repeated log lines share one shape.
    屏蔽数字、进度条字符与空白，使同模式日志行归一为相同形状。"""
    s = _SHAPE_NUM_RE.sub("#", line)
    s = _SHAPE_BAR_RE.sub("#", s)
    return _SHAPE_WS_RE.sub(" ", s).strip()


def _collapse_repeated_lines(lines: list) -> list:
    """Collapse runs of >= RUN_COLLAPSE_MIN similar lines to first 2 + last 1.
    连续 ≥RUN_COLLAPSE_MIN 行同模式输出折叠为前 2 行 + 末 1 行 + 省略提示。"""
    out: list = []
    i, n = 0, len(lines)
    while i < n:
        shape = _line_shape(lines[i])
        j = i + 1
        while j < n and _line_shape(lines[j]) == shape:
            j += 1
        run = j - i
        if run >= RUN_COLLAPSE_MIN:
            omitted = run - 3
            out.extend(lines[i : i + 2])
            out.append(
                f"    … [省略 {omitted} 行相似输出 / {omitted} similar lines omitted] …"
            )
            out.append(lines[j - 1])
        else:
            out.extend(lines[i:j])
        i = j
    return out


# Install-command cells (%pip install / !conda install …) produce pages of
# useless download logs in the PDF; their stream output is collapsed to a
# one-line summary keeping only "Successfully installed" / "ERROR:" lines.
# 安装命令单元格（%pip install / !conda install 等）的下载日志在 PDF 里占多页且无价值；
# 其 stream 输出压缩为一行摘要，仅保留 "Successfully installed" / "ERROR:" 等关键行。
_INSTALL_LINE_RE = re.compile(
    r"^\s*[%!]\s*(?:"
    r"(?:pip3?|conda|mamba|uv)\s+(?:[\w-]+\s+)*(?:un)?install\b"
    r"|apt(?:-get)?\s+(?:[\w-]+\s+)*install\b"
    r"|python[\d.]*\s+-m\s+pip\s+(?:un)?install\b"
    r")"
)
_INSTALL_KEEP_RE = re.compile(r"^\s*(?:Successfully (?:un)?installed\b|ERROR[: ])")
_INSTALL_NOTE_MARK = "install log omitted"


def _is_install_cell(source: str) -> bool:
    return any(_INSTALL_LINE_RE.match(line) for line in source.splitlines())


def _summarize_install_streams(outputs: list) -> list:
    """Collapse stream outputs of an install cell into one short summary.
    将安装单元格的 stream 输出合并压缩为一条简短摘要。"""
    text = "".join(
        o.text if isinstance(o.text, str) else "".join(o.text)
        for o in outputs
    )
    # Already summarized (preprocessor may run more than once): keep as-is
    # 已经压缩过（预处理器可能被多次执行）：原样保留
    if _INSTALL_NOTE_MARK in text:
        return outputs
    text = _apply_carriage_returns(text)

    lines = text.splitlines()
    kept = [ln for ln in lines if _INSTALL_KEEP_RE.match(ln)]
    kept = kept[:INSTALL_LOG_KEEP_LINES]

    summary = "\n".join(kept)
    note = (
        f"… [安装日志已省略 / install log omitted: {len(lines)} lines; "
        f"see .ipynb for full content] …"
    )
    out = copy.copy(outputs[0])
    out["text"] = (summary + "\n" if summary else "") + note + "\n"
    return [out]


class TruncateOutputPreprocessor(Preprocessor):
    """Keep figures/images; truncate long stdout and text/plain output.
    保留图表/图片，截断过长的 stdout 与 text/plain 输出。"""

    enabled = True

    def preprocess_cell(self, cell, resources, cell_index):
        if cell.cell_type != "code" or not cell.get("outputs"):
            return cell, resources

        install_cell = _is_install_cell(cell.get("source", ""))
        install_streams: list = []

        # Merge consecutive stream outputs first: interleaved logging + tqdm
        # produces dozens of small chunks that would each dodge the line cap
        # 先合并相邻的 stream 输出：logging 与 tqdm 交替写入会产生几十个小块，
        # 每块都不超过行数上限，导致整体截断失效
        merged: list = []
        for output in cell.outputs:
            if (
                output.get("output_type") == "stream"
                and merged
                and merged[-1].get("output_type") == "stream"
            ):
                prev = merged[-1]
                prev_text = prev.text if isinstance(prev.text, str) else "".join(prev.text)
                cur_text = output.text if isinstance(output.text, str) else "".join(output.text)
                prev["text"] = prev_text + cur_text
            else:
                out = copy.copy(output) if output.get("output_type") == "stream" else output
                merged.append(out)

        new_outputs = []
        for output in merged:
            otype = output.get("output_type")

            if otype == "stream" and install_cell:
                install_streams.append(output)

            elif otype == "stream":
                raw = output.text if isinstance(output.text, str) else "".join(output.text)
                # Already truncated (guard against reprocessing) / 已截断过则原样保留
                if _TRUNC_NOTE_MARK in raw:
                    new_outputs.append(output)
                    continue
                text = _apply_carriage_returns(raw)
                lines = text.splitlines()
                total = len(lines)
                lines = _collapse_repeated_lines(lines)
                if len(lines) > MAX_STREAM_LINES:
                    head_n = MAX_STREAM_LINES - STREAM_TAIL_LINES
                    note = (
                        f"\n… [输出已截断 / output truncated: {total} lines total, "
                        f"showing first {head_n} and last {STREAM_TAIL_LINES}; "
                        f"see .ipynb for full content] …\n"
                    )
                    lines = lines[:head_n] + [note] + lines[-STREAM_TAIL_LINES:]
                new_text = "\n".join(lines) + ("\n" if lines else "")
                if new_text.rstrip("\n") != raw.rstrip("\n"):
                    out = copy.copy(output)
                    out["text"] = new_text
                    new_outputs.append(out)
                else:
                    new_outputs.append(output)

            elif otype == "error":
                tb = output.get("traceback", [])
                already = any("traceback truncated" in str(ln) for ln in tb)
                if len(tb) > MAX_TRACEBACK_LINES and not already:
                    # Keep head + tail: the error type/message is on the LAST lines
                    # 头尾都保留：错误类型与消息在最后几行
                    head_n = MAX_TRACEBACK_LINES - TRACEBACK_TAIL_LINES
                    out = copy.copy(output)
                    out["traceback"] = (
                        tb[:head_n]
                        + [f"... [traceback 已截断 / traceback truncated: {len(tb)} lines total] ..."]
                        + tb[-TRACEBACK_TAIL_LINES:]
                    )
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
                    if len(text) > MAX_TEXT_CHARS and "text/plain truncated" not in text:
                        # Keep head + tail: repr footers (DataFrame shape etc.) are at the end
                        # 头尾都保留：repr 的尾部（如 DataFrame 形状信息）在结尾
                        head_n = MAX_TEXT_CHARS - TEXT_TAIL_CHARS
                        keep["text/plain"] = (
                            text[:head_n]
                            + f"\n… [text/plain 已截断 / text/plain truncated: was {len(text)} chars] …\n"
                            + text[-TEXT_TAIL_CHARS:]
                        )
                if keep:
                    out = copy.copy(output)
                    out["data"] = keep
                    new_outputs.append(out)

            else:
                new_outputs.append(output)

        if install_streams:
            new_outputs.extend(_summarize_install_streams(install_streams))

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
            # Some Chrome builds show a blank window even in headless mode;
            # park any browser window far off-screen so it can never appear
            # over (or behind) the GUI and confuse the user
            # 部分 Chrome 版本 headless 模式仍会弹出空白窗口；把浏览器窗口
            # 定位到屏幕外，确保任何情况下都不会出现在界面上干扰用户
            args.append("--window-position=-32000,-32000")

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

    # Truncation runs via the exporter-registered TruncateOutputPreprocessor;
    # do not run it here as well, or line counts in the notes go wrong.
    # 截断由导出器注册的 TruncateOutputPreprocessor 执行；此处不可再跑一遍，
    # 否则截断提示中的行数统计会被二次截断改错。
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
