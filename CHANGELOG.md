# Changelog

English | [中文](#更新日志)

## 1.3.0 — 2026-07-11

### Added

- **Install-log suppression**: `%pip install` / `!pip install` / `conda|mamba|uv|apt install` cells collapse their download logs (often pages long) to a one-line note, keeping only `Successfully installed …` and `ERROR:` lines
- **Log compression**: merge consecutive stream chunks within a cell (interleaved logging + tqdm used to dodge the per-output cap — measured 93 chunks / 2796 lines → 43 lines); keep only the final frame of `\r` progress bars (tqdm/keras); collapse runs of ≥8 similar lines (e.g. `Batch 3/500, Loss: 0.11`)
- **Head + tail truncation**: long stream output, `text/plain` and tracebacks now keep the tail too — the final loss, the DataFrame shape footer and the actual error message survive truncation

### Changed

- **GUI**: completion notice now shows inside the window (status bar turns green/red, taskbar flashes) instead of a popup dialog; the log panel wraps long lines to the window width; any stray browser window during conversion is parked off-screen so it can never appear over the GUI

### Fixed

- **Double truncation**: the truncation preprocessor ran twice, corrupting the "N lines total" count in truncation notes (e.g. 5000 lines reported as 43)

---

## 1.2.0 — 2026-07-04

### Added

- **GUI**: Tkinter GUI with multi-file batch selection, output-directory picker, progress bar, log panel and cancel; double-click the exe (or run `nb2pdf` / `nb2pdf gui`) to open
- **App icon**: custom PDF-document icon for the exe and the GUI window (`assets/nb2pdf.ico`, generated from `icons.png`)
- **Two language builds**: separate `nb2pdf-zh.exe` (Simplified Chinese UI) and `nb2pdf-en.exe` (English UI); **both** fully support Chinese/CJK file paths; source mode switches via `NB2PDF_LANG=zh|en`
- **About**: author `s0mu7l` with clickable GitHub link (bottom-right of the GUI)
- **`-d/--output-dir`**: CLI batch conversion into one directory
- Notebooks from **different directories** can be mixed in one batch (GUI & CLI)

### Changed

- **Packaging**: switched from PyInstaller to **Nuitka** onefile (`scripts/build_exe_nuitka.ps1`); console attaches when run from a terminal, hidden when double-clicked
- Onefile runtime extracts to an ASCII cache dir and is **cached across runs** (faster startup)
- `runtime.py` now supports both Nuitka and PyInstaller frozen modes (bundled nbconvert templates located via `JUPYTER_PATH`)

---

## 1.1.2 — 2026-06-15

### Fixed

- **Large `_internal` folder (~385 MB) after unzip**: switched back to a **lean onefile** build; excluded Playwright browser archives, JupyterLab static assets, Babel locales, etc.

### Changed

- Runtime extraction: `%LOCALAPPDATA%\nb2pdf\_pyi` (ASCII-only; fixes DLL load on Chinese cwd without `_internal` beside the exe)
- Release bundle: `nb2pdf.exe` + `README.md` (~61 MB exe)

---

## 1.1.1 — 2026-06-13

### Fixed

- **`Failed to load Python DLL python312.dll`** on non-ASCII (Chinese) cwd: temporary **onedir** layout (`nb2pdf.exe` + `_internal/`), UPX disabled

### Changed

- Release bundle became a folder instead of a single exe

---

## 1.1.0 — 2026-06-13

### Fixed

- **PDF conversion timeout**: replaced `wait_until="networkidle"` with `"load"` for MathJax CDN pages
- **Chinese file paths**: `Path.as_uri()` for correct `file://` URLs on Windows

### Improved

- Navigation timeout **120s** (`PAGE_GOTO_TIMEOUT_MS`)
- Post-load render wait **15s** (`page_render_timeout`)
- Browser cleanup in `try/finally`
- Bilingual code comments, docstrings, CLI messages

### Changed

- Build scripts in `scripts/`; `release/` as the sole exe output

---

## 1.0.0 — 2026-06-13

### Added

- Jupyter Notebook → text-based PDF with embedded images
- Truncate long stdout / text/plain / traceback
- Embed local Markdown images; auto-slice tall stitched images
- Windows onefile exe via PyInstaller
- CLI: `convert`, `install-browser`, globs, `-o`

---

# 更新日志

[English](#changelog) | 中文

## 1.3.0 — 2026-07-11

### 新增

- **安装日志压缩**：`%pip install` / `!pip install` / `conda|mamba|uv|apt install` 单元格的下载日志（常占多页）压缩为一行省略提示，仅保留 `Successfully installed …` 与 `ERROR:` 关键行
- **日志压缩**：合并单元格内相邻的 stream 输出块（logging 与 tqdm 交替写入会绕过逐块截断，实测 93 块 2796 行 → 43 行）；`\r` 进度条（tqdm/keras）只保留最终帧；连续 ≥8 行同模式日志（如 `Batch 3/500, Loss: 0.11`）折叠为首尾几行
- **头尾截断**：长输出、`text/plain` 与 traceback 截断时同时保留结尾——最终 loss、DataFrame 形状信息与错误消息不再被截掉

### 变更

- **图形界面**：完成通知改为窗口内显示（状态栏变绿/红并闪烁任务栏），不再弹出对话框；日志面板按窗口宽度自动换行；转换期间任何浏览器窗口都定位到屏幕外，不会再出现在界面上引起混淆

### 修复

- **双重截断**：截断预处理器此前执行两遍，导致截断提示中的总行数统计错误（如 5000 行显示为 43 行）

---

## 1.2.0 — 2026-07-04

### 新增

- **图形界面**：Tkinter GUI，支持批量多选 `.ipynb`、指定输出目录、进度与日志显示、取消转换；双击 exe 或运行 `nb2pdf` / `nb2pdf gui` 即可打开
- **应用图标**：exe 与窗口使用自定义 PDF 文档图标（`assets/nb2pdf.ico`，由 `icons.png` 生成）
- **中英双版本**：分别打包 `nb2pdf-zh.exe`（简体中文界面）与 `nb2pdf-en.exe`（English UI），两者均完整支持中文路径；源码运行可用 `NB2PDF_LANG=zh|en` 切换
- **作者信息**：界面右下角显示作者 `s0mu7l` 与 GitHub 链接
- **`-d/--output-dir`**：命令行批量转换统一输出目录
- 支持一次转换位于**不同目录**下的多个 notebook（GUI 与 CLI）

### 变更

- **打包**：由 PyInstaller 改为 **Nuitka** 单文件（`scripts/build_exe_nuitka.ps1`）；终端运行有输出，双击运行不闪黑框
- 运行时解压到英文缓存目录并跨运行复用，启动更快
- `runtime.py` 同时兼容 Nuitka 与 PyInstaller 冻结模式（通过 `JUPYTER_PATH` 定位打包的 nbconvert 模板）

---

## 1.1.2 — 2026-06-15

### 修复

- **解压后 `_internal` 过大（约 385 MB）**：恢复精简单文件打包，剔除 Playwright 浏览器包、JupyterLab 静态资源、Babel 语言包等冗余

### 变更

- 运行时解压到 `%LOCALAPPDATA%\nb2pdf\_pyi`（纯英文路径，修复中文路径下 DLL 加载错误）
- 发布物为单 exe + 说明文件（约 61 MB）

---

## 1.1.1 — 2026-06-13

### 修复

- 中文路径下 **`Failed to load Python DLL python312.dll`**：临时改为目录版打包（`nb2pdf.exe` + `_internal/`），禁用 UPX

### 变更

- 发布物由单文件改为文件夹

---

## 1.1.0 — 2026-06-13

### 修复

- **转换超时**：页面加载策略由 `networkidle` 改为 `load`（MathJax CDN 页面）
- **中文路径**：使用 `Path.as_uri()` 生成正确的 `file://` URL

### 优化

- 导航超时 **120 秒**（`PAGE_GOTO_TIMEOUT_MS`）
- 加载后渲染等待 **15 秒**（`page_render_timeout`）
- 浏览器关闭逻辑放入 `try/finally`
- 代码注释、文档字符串与 CLI 消息中英双语

### 变更

- 打包脚本迁入 `scripts/`；`release/` 作为唯一 exe 输出目录

---

## 1.0.0 — 2026-06-13

### 新增

- Jupyter Notebook → 文本型 PDF，内嵌图片
- 截断冗长的 stdout / text/plain / traceback
- 本地 Markdown 图片内嵌；超长拼接图自动切片
- PyInstaller 打包 Windows 单文件 exe
- 命令行：`convert`、`install-browser`、通配符、`-o`
