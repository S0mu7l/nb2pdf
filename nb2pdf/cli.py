"""CLI entry point. 命令行入口。"""

from __future__ import annotations

import argparse
import glob
import os
import sys

from nb2pdf.runtime import setup_frozen

setup_frozen()

# converter is imported lazily inside each command branch: it pulls in the
# heavy nbconvert stack (~seconds), which would delay GUI startup otherwise
# converter 在各命令分支内懒加载：其依赖的 nbconvert 系列导入较慢，避免拖慢 GUI 启动
from nb2pdf._version import __version__


def _expand_notebooks(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for p in patterns:
        if any(ch in p for ch in "*?[]"):
            paths.extend(sorted(glob.glob(p)))
        else:
            paths.append(p)
    return paths


def _launch_gui(initial_files: list[str] | None = None) -> int:
    from nb2pdf.gui import run_gui

    return run_gui(initial_files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nb2pdf",
        description=(
            "Convert Jupyter Notebook to text-based PDF with embedded images. "
            "将 Jupyter Notebook 转为 PDF（文本型、内嵌图片）"
        ),
    )
    parser.add_argument("--version", action="version", version=f"nb2pdf {__version__}")

    sub = parser.add_subparsers(dest="command")

    convert_parser = sub.add_parser(
        "convert",
        help="Convert notebook(s) to PDF / 转换 notebook 为 PDF",
    )
    convert_parser.add_argument(
        "notebooks",
        nargs="+",
        help=".ipynb path(s), globs supported (e.g. *.ipynb) / .ipynb 文件路径，支持通配符",
    )
    convert_parser.add_argument(
        "-o", "--output",
        help="Output PDF path (single file only) / 输出 PDF 路径（仅单文件转换时有效）",
    )
    convert_parser.add_argument(
        "-d", "--output-dir",
        help="Output directory for all PDFs / 所有 PDF 的输出目录（批量转换适用）",
    )

    gui_parser = sub.add_parser(
        "gui",
        help="Open the graphical interface / 打开图形界面",
    )
    gui_parser.add_argument(
        "notebooks",
        nargs="*",
        help="Optional .ipynb files to pre-load / 可选：预先载入的 .ipynb 文件",
    )

    sub.add_parser(
        "install-browser",
        help="Install Playwright Chromium / 安装 Playwright Chromium 浏览器",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        # No arguments (e.g. double-clicked exe): open the GUI; fall back to
        # help when Tk is unavailable (headless environment).
        # 无参数（如双击 exe）时打开图形界面；无 Tk 环境则回退为帮助信息。
        try:
            return _launch_gui()
        except Exception:
            parser.print_help()
            return 0

    if args.command == "gui":
        return _launch_gui(_expand_notebooks(args.notebooks))

    if args.command == "install-browser":
        from nb2pdf.converter import install_browser

        return install_browser()

    if args.command == "convert":
        from nb2pdf.converter import convert

        notebooks = _expand_notebooks(args.notebooks)
        if not notebooks:
            print(
                "错误：未找到匹配的 .ipynb 文件 / Error: no matching .ipynb files found",
                file=sys.stderr,
            )
            return 1

        if args.output and len(notebooks) > 1:
            print(
                "错误：批量转换时不能使用 -o 指定单一输出路径，请改用 -d 输出目录 / "
                "Error: -o cannot be used when converting multiple notebooks; use -d instead",
                file=sys.stderr,
            )
            return 1

        if args.output and args.output_dir:
            print(
                "错误：-o 与 -d 不能同时使用 / Error: -o and -d are mutually exclusive",
                file=sys.stderr,
            )
            return 1

        out_dir = None
        if args.output_dir:
            out_dir = os.path.abspath(args.output_dir)
            os.makedirs(out_dir, exist_ok=True)

        failed = 0
        for nb_path in notebooks:
            try:
                output = args.output
                if out_dir:
                    stem = os.path.splitext(os.path.basename(nb_path))[0]
                    output = os.path.join(out_dir, stem + ".pdf")
                out = convert(nb_path, output)
                print(f"OK  {nb_path} -> {out}")
            except Exception as exc:
                failed += 1
                print(f"FAIL  {nb_path}: {exc}", file=sys.stderr)

        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
