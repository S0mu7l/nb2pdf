# Changelog / 更新日志

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
