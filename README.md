# nb2pdf

Convert Jupyter Notebook (`.ipynb`) to **text-based PDF** with selectable text and embedded images — ideal for reading and printing course materials.

将 Jupyter Notebook（`.ipynb`）转为**文本型 PDF**（文字可选中、图片内嵌），适合教程讲义阅读与打印。

**Current version / 当前版本：1.1.2**

## Two ways to use / 两种使用方式


| Mode / 方式  | For / 适合人群                            | Details / 说明                                                                   |
| ---------- | ------------------------------------- | ------------------------------------------------------------------------------ |
| **exe**    | Users without Python / 不想装 Python 的用户 | Download from **GitHub Releases** — see [release](https://github.com/S0mu7l/nb2pdf/releases)|
| **Source** | Developers / 开发者、需要自定义的用户             | Clone repo and install with Python — see below / 克隆本仓库，用 Python 安装运行（见下文）      |


---

## Changelog / 更新日志

### 1.1.2

- **Size / 体积**：Lean **onefile** exe (~61 MB); no 300MB+ `_internal` folder after unzip / 恢复单文件 exe，精简打包，解压后不再生成 `_internal` 目录
- **Chinese paths / 中文路径**：Runtime extracts to `%LOCALAPPDATA%\nb2pdf\_pyi`; fixes `Failed to load Python DLL` / 运行时解压到纯英文路径，修复 DLL 加载错误

### 1.1.1

- **Fixed / 修复**：`Failed to load Python DLL` on Chinese cwd — temporary **onedir** layout (`nb2pdf.exe` + `_internal/`) / exe 在中文路径下报错，改为目录版打包

### 1.1.0

- **Fixed / 修复**：`Page.goto: Timeout exceeded` — use `load` instead of `networkidle`, 120s nav timeout, correct `file://` encoding for Chinese paths / 转换超时修复
- **Improved / 优化**：15s render wait, browser cleanup, bilingual code comments / 渲染等待与浏览器关闭逻辑优化
- **Changed / 整理**：`scripts/` for build, `release/` for exe output / 项目目录整理

### 1.0.0

- Initial release: text PDF, output truncation, image embed, tall-image slicing, Windows exe / 首个发布版本

Full history / 完整记录见 [CHANGELOG.md](CHANGELOG.md).

---

## Source install / 源码安装

### Requirements / 环境要求

- Python 3.9+
- Windows 10/11 (64-bit, recommended; other platforms may work) / Windows 10/11（64 位，推荐）
- [Google Chrome](https://www.google.com/chrome/) recommended (app prefers system Chrome) / 推荐安装 Google Chrome

### Install / 安装

```bash
git clone <https://github.com/S0mu7l/nb2pdf>
cd nb2pdf
pip install -e .
python -m playwright install chromium
```

Skip `install chromium` if Chrome is already installed. / 若本机已安装 Chrome，可跳过。

### Usage / 使用

```bash
# Show version / 查看版本
nb2pdf --version

# Convert (PDF next to notebook) / 转换 notebook
nb2pdf convert notebook.ipynb

# Custom output path / 指定输出路径
nb2pdf convert notebook.ipynb -o output.pdf

# Batch convert / 批量转换
nb2pdf convert "D:\notebooks\*.ipynb"
```

Or run as a module / 也可用模块方式：

```bash
python -m nb2pdf convert examples/Seq2Seq.ipynb
```

### Dependencies / 依赖


| Package                     | Purpose / 用途                                    |
| --------------------------- | ----------------------------------------------- |
| `nbconvert[webpdf]>=7.16.0` | notebook → HTML → PDF                           |
| `nbformat>=5.9.0`           | Read/write `.ipynb` / 读写 `.ipynb`               |
| `playwright>=1.40.0`        | Drive Chromium / 驱动 Chromium                    |
| `Pillow>=10.0.0`            | Image handling & tall-image slicing / 图片处理与长图切片 |


```bash
pip install -r requirements.txt
```

---

## Features / 功能说明


| Feature / 功能               | Description / 说明                                          |
| -------------------------- | --------------------------------------------------------- |
| Full input / 完整 input      | Export all Markdown & code cells / Markdown 与代码单元格全部导出    |
| Trimmed output / 精简 output | Truncate stdout beyond 40 lines / stdout 超过 40 行自动截断      |
| Embedded images / 内嵌图片     | matplotlib plots, local Markdown images (`./xxx.png`)     |
| Tall-image slicing / 长图切片  | Auto-split images taller than 3000px to avoid PDF overlap |
| Text PDF / 文本型 PDF         | Vector text, selectable & copyable / 矢量文字，可选中复制           |


## Configuration / 配置项

Top of `nb2pdf/converter.py`:


| Constant               | Default | Description / 说明                                |
| ---------------------- | ------- | ----------------------------------------------- |
| `MAX_STREAM_LINES`     | 40      | Max stdout lines kept / stdout 保留行数             |
| `MAX_TEXT_CHARS`       | 2500    | Max text/plain chars / text/plain 字符上限          |
| `MAX_TRACEBACK_LINES`  | 20      | Max traceback lines / traceback 行数上限            |
| `PAGE_GOTO_TIMEOUT_MS` | 120000  | Playwright navigation timeout (ms) / 页面导航超时（毫秒） |


## Project layout / 项目结构

```
nb2pdf/
├── README.md              # Source-mode guide / 源码模式说明
├── CHANGELOG.md           # Version history / 版本更新记录
├── LICENSE
├── pyproject.toml
├── requirements.txt       # Runtime deps / 运行依赖
├── requirements-build.txt # Build deps / 打包依赖
├── nb2pdf/                # Python package / 源码包
│   ├── cli.py
│   ├── converter.py
│   ├── images.py
│   └── runtime.py
```

## FAQ / 常见问题

**Conversion timeout (`Page.goto: Timeout exceeded`) / 转换超时**  
Fixed in 1.1.0+. Large notebooks may take 1–2 minutes on first run. / 1.1.0 已修复；大 notebook 首次转换可能需要 1–2 分钟。

**Playwright / asyncio errors on Windows / Playwright 报错**  
Use the `nb2pdf` CLI from this project, not raw `jupyter nbconvert`. / 请使用本项目的 `nb2pdf` 命令。

**PDF file locked / PDF 被占用**  
Close the reader and retry; output falls back to `*_new.pdf`. / 关闭阅读器后重试。

**Missing Markdown images / Markdown 图片缺失**  
Paths must be relative to the notebook directory and files must exist. / 图片路径需相对 notebook 目录且文件存在。

**Image overlaps following text / 图片与文字重叠**  
Caused by very tall stitched images; auto-sliced in latest version. / 超长拼接图会自动切片。

## License

MIT — see [LICENSE](LICENSE).# nb2pdf
