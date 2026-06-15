"""CLI entry point. 命令行入口。"""

from __future__ import annotations

import argparse
import glob
import sys

from nb2pdf.runtime import setup_frozen

setup_frozen()

from nb2pdf._version import __version__
from nb2pdf.converter import convert, install_browser


def _expand_notebooks(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for p in patterns:
        if any(ch in p for ch in "*?[]"):
            paths.extend(sorted(glob.glob(p)))
        else:
            paths.append(p)
    return paths


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

    sub.add_parser(
        "install-browser",
        help="Install Playwright Chromium / 安装 Playwright Chromium 浏览器",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "install-browser":
        return install_browser()

    if args.command == "convert":
        notebooks = _expand_notebooks(args.notebooks)
        if not notebooks:
            print(
                "错误：未找到匹配的 .ipynb 文件 / Error: no matching .ipynb files found",
                file=sys.stderr,
            )
            return 1

        if args.output and len(notebooks) > 1:
            print(
                "错误：批量转换时不能使用 -o 指定单一输出路径 / "
                "Error: -o cannot be used when converting multiple notebooks",
                file=sys.stderr,
            )
            return 1

        failed = 0
        for nb_path in notebooks:
            try:
                out = convert(nb_path, args.output)
                print(f"OK  {nb_path} -> {out}")
            except Exception as exc:
                failed += 1
                print(f"FAIL  {nb_path}: {exc}", file=sys.stderr)

        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
