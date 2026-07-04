"""UI language layer. 界面语言层。

Language resolution order / 语言优先级:
1. NB2PDF_LANG environment variable ("zh" / "en") / 环境变量
2. Build-time baked default in nb2pdf._buildlang (written by build script)
   构建期由打包脚本写入的默认语言
3. Fallback "zh" / 默认简体中文
"""

from __future__ import annotations

import os

AUTHOR = "s0mu7l"
GITHUB_URL = "https://github.com/S0mu7l/nb2pdf"


def _detect_lang() -> str:
    lang = os.environ.get("NB2PDF_LANG", "").strip().lower()
    if lang in ("zh", "en"):
        return lang
    try:
        from nb2pdf._buildlang import BUILD_LANG  # generated at build time / 构建期生成

        if BUILD_LANG in ("zh", "en"):
            return BUILD_LANG
    except ImportError:
        pass
    return "zh"


LANG = _detect_lang()

_STRINGS: dict[str, dict[str, str]] = {
    "window_title": {
        "zh": "nb2pdf {version} — Jupyter Notebook 转 PDF",
        "en": "nb2pdf {version} — Jupyter Notebook to PDF",
    },
    "add_files": {"zh": "添加文件…", "en": "Add files…"},
    "remove_selected": {"zh": "移除选中", "en": "Remove"},
    "clear": {"zh": "清空", "en": "Clear"},
    "file_count": {"zh": "{n} 个文件", "en": "{n} file(s)"},
    "output_dir": {"zh": "输出目录:", "en": "Output dir:"},
    "browse": {"zh": "浏览…", "en": "Browse…"},
    "output_hint": {
        "zh": "留空则 PDF 输出到各 notebook 所在目录",
        "en": "Leave empty to save each PDF next to its notebook",
    },
    "convert": {"zh": "开始转换", "en": "Convert"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "install_browser": {"zh": "安装浏览器内核", "en": "Install browser"},
    "ready": {"zh": "就绪", "en": "Ready"},
    "select_files_title": {
        "zh": "选择 .ipynb 文件（可多选）",
        "en": "Select .ipynb files (multi-select)",
    },
    "select_outdir_title": {"zh": "选择输出目录", "en": "Select output directory"},
    "need_files": {
        "zh": "请先添加至少一个 .ipynb 文件",
        "en": "Please add at least one .ipynb file",
    },
    "outdir_error": {
        "zh": "无法创建输出目录:\n{err}",
        "en": "Cannot create output directory:\n{err}",
    },
    "cancelling": {
        "zh": "正在取消（完成当前文件后停止）…",
        "en": "Cancelling after the current file…",
    },
    "cancelled_skip": {
        "zh": "已取消，跳过剩余 {n} 个文件",
        "en": "Cancelled, skipping remaining {n} file(s)",
    },
    "converting": {"zh": "[{i}/{total}] 正在转换: {name}", "en": "[{i}/{total}] Converting: {name}"},
    "done_summary": {
        "zh": "完成 — 成功 {ok}，失败 {fail}",
        "en": "Done — {ok} OK, {fail} failed",
    },
    "install_confirm": {
        "zh": "将下载 Playwright Chromium（约 150 MB，仅需一次）。继续？",
        "en": "This downloads Playwright Chromium (~150 MB, one-time). Continue?",
    },
    "installing": {"zh": "正在安装 Chromium…", "en": "Installing Chromium…"},
    "install_ok": {"zh": "浏览器内核安装完成", "en": "Browser installed"},
    "install_fail_code": {
        "zh": "安装失败，退出码 {code}",
        "en": "Install failed (exit code {code})",
    },
    "install_fail": {"zh": "安装失败: {err}", "en": "Install failed: {err}"},
    "author": {"zh": "作者", "en": "Author"},
}


def tr(key: str, **kwargs) -> str:
    """Translate a UI string. 取当前语言的界面文案。"""
    entry = _STRINGS[key]
    text = entry.get(LANG) or entry["zh"]
    return text.format(**kwargs) if kwargs else text
