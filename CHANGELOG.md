# Changelog / 更新日志

## 1.2.0 — 2026-07-04

### Added / 新增

- **GUI / 图形界面**：Tkinter GUI with multi-file batch selection, output-directory picker, progress bar, log panel and cancel; double-click the exe (or run `nb2pdf` / `nb2pdf gui`) to open / 图形界面支持批量多选 `.ipynb`、指定输出目录、进度与日志显示、取消转换；双击 exe 或运行 `nb2pdf gui` 即可打开
- **App icon / 应用图标**：Custom PDF-document icon for the exe and the GUI window (`assets/nb2pdf.ico`, generated from `icons.png`) / exe 与窗口使用自定义 PDF 文档图标
- **Two language builds / 中英双版本**：Separate `nb2pdf-zh.exe` (简体中文界面) and `nb2pdf-en.exe` (English UI); **both** fully support Chinese/CJK file paths / 分别打包中文与英文界面版本，两者均完整支持中文路径；源码运行可用 `NB2PDF_LANG=zh|en` 切换
- **About / 作者信息**：Author `s0mu7l` with clickable GitHub link (bottom-right of the GUI) / 界面右下角显示作者与 GitHub 链接（<https://github.com/S0mu7l/nb2pdf>）
- **`-d/--output-dir`**：CLI batch conversion into one directory / 命令行批量转换统一输出目录
- Notebooks from **different directories** can be mixed in one batch (GUI & CLI) / 支持一次转换位于不同目录下的多个 notebook

### Changed / 变更

- **Packaging / 打包**：Switched from PyInstaller to **Nuitka** onefile (`scripts/build_exe_nuitka.ps1`); console attaches when run from a terminal, hidden when double-clicked / 打包方案由 PyInstaller 改为 Nuitka 单文件；终端运行有输出，双击运行不闪黑框
- Onefile runtime extracts to ASCII cache dir and is **cached across runs** (faster startup) / 运行时解压到英文缓存目录并跨运行复用，启动更快
- `runtime.py` now supports both Nuitka and PyInstaller frozen modes (bundled nbconvert templates located via `JUPYTER_PATH`) / 冻结运行时同时兼容 Nuitka 与 PyInstaller

---

## 1.1.2 — 2026-06-15

### Fixed / 修复

- **Large `_internal` folder (~385 MB) after unzip / 解压后 `_internal` 过大**：Switched back to **lean onefile** build; excluded Playwright browser archives, JupyterLab static assets, Babel locales, etc. / 恢复精简单文件打包，剔除 Playwright 浏览器包、JupyterLab、Babel 等冗余

### Changed / 变更

- Runtime extraction: `%LOCALAPPDATA%\nb2pdf\_pyi` (ASCII-only; fixes DLL load on Chinese cwd without `_internal` beside exe) / 运行时解压到纯英文路径，修复中文路径下 DLL 错误
- Release bundle: `nb2pdf.exe` + `README.md` (~61 MB exe) / 发布物为单 exe + 说明文件

---

## 1.1.1 — 2026-06-13

### Fixed / 修复

- **`Failed to load Python DLL python312.dll`** on non-ASCII (Chinese) cwd: temporary **onedir** layout (`nb2pdf.exe` + `_internal/`), UPX disabled / 中文路径下 DLL 加载失败，改为目录版打包

### Changed / 变更

- Release bundle became a folder instead of a single exe / 发布物由单文件改为文件夹

---

## 1.1.0 — 2026-06-13

### Fixed / 修复

- **PDF conversion timeout / 转换超时**：Replaced `wait_until="networkidle"` with `"load"` for MathJax CDN pages / 页面加载策略改为 `load`
- **Chinese file paths / 中文路径**：`Path.as_uri()` for correct `file://` URLs on Windows

### Improved / 优化

- Navigation timeout **120s** (`PAGE_GOTO_TIMEOUT_MS`) / 导航超时 120 秒
- Post-load render wait **15s** (`page_render_timeout`) / 渲染等待 15 秒
- Browser cleanup in `try/finally` / 改进浏览器关闭逻辑
- Bilingual code comments, docstrings, CLI messages / 代码与 CLI 中英双语

### Changed / 变更

- Build scripts in `scripts/`; `release/` as sole exe output / 打包脚本迁入 `scripts/`

---

## 1.0.0 — 2026-06-13

### Added / 新增

- Jupyter Notebook → text-based PDF with embedded images / 文本型 PDF、内嵌图片
- Truncate long stdout / text/plain / traceback / 截断冗长 output
- Embed local Markdown images; auto-slice tall stitched images / 本地图片内嵌与长图切片
- Windows onefile exe via PyInstaller / Windows exe 打包
- CLI: `convert`, `install-browser`, globs, `-o` / 命令行与批量转换
