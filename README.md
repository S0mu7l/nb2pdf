# nb2pdf

![image](https://raw.githubusercontent.com/S0mu7l/nb2pdf/f198021a3885701a4a38aa7cb8c46686feebb5cb/nb2pdf-banner.webp)

English | [中文说明](#nb2pdf-中文说明)

Convert Jupyter Notebook (`.ipynb`) to **text-based PDF** with selectable text and embedded images — ideal for reading and printing course materials.

**Current version: 1.3.0**

## Two ways to use

| Mode       | For                   | Details                                                                 |
| ---------- | --------------------- | ----------------------------------------------------------------------- |
| **exe**    | Users without Python  | Download from [GitHub Releases](https://github.com/S0mu7l/nb2pdf/releases) |
| **Source** | Developers            | Clone this repo and install with Python — see below                     |

**exe download** (v1.3.0 on [GitHub Releases](https://github.com/S0mu7l/nb2pdf/releases)):

- Chinese UI: `nb2pdf-zh-windows-1.3.0.rar` → extract `nb2pdf-zh.exe`
- English UI: `nb2pdf-en-windows-1.3.0.rar` → extract `nb2pdf-en.exe`

Both editions support Chinese/CJK file paths — pick either one.

## Changelog

### 1.3.0

- **Log compression**: merge interleaved stream chunks (logging + tqdm used to dodge the per-output cap — a real course notebook went from 79 to 30 PDF pages); keep only the final frame of `\r` progress bars (tqdm/keras); collapse runs of ≥8 similar lines such as `Batch 3/500, Loss: 0.11`
- **Head + tail truncation**: long stdout, `text/plain` and tracebacks now keep the tail too — the final loss, the DataFrame shape footer and the actual error message survive truncation
- **Install-log suppression**: `%pip install` / `!pip install` / `conda|mamba|uv|apt install` cells collapse their download logs to a one-line note, keeping only `Successfully installed …` and `ERROR:` lines
- **Fixed**: the truncation preprocessor ran twice, corrupting the "N lines total" count in truncation notes

### 1.2.0

- **GUI**: Tkinter GUI — batch multi-select, output dir picker, progress & log, cancel; double-click the exe or run `nb2pdf gui`
- **Batch**: `-d/--output-dir` for CLI batch output; mix notebooks from different directories
- **Packaging**: PyInstaller → **Nuitka** onefile; console when run in terminal, silent on double-click
- **Two language builds**: `nb2pdf-zh.exe` + `nb2pdf-en.exe`, both support Chinese paths

Full history: [CHANGELOG.md](CHANGELOG.md).

## Source install

### Requirements

- Python 3.9+
- Windows 10/11 (64-bit, recommended; other platforms may work)
- [Google Chrome](https://www.google.com/chrome/) recommended (the app prefers system Chrome)

### Install

```bash
git clone https://github.com/S0mu7l/nb2pdf.git
cd nb2pdf
pip install -e .
python -m playwright install chromium
```

Skip `install chromium` if Chrome is already installed.

### Usage

```bash
# Open GUI (batch multi-select, output dir)
nb2pdf            # no args -> GUI
nb2pdf gui

# UI language (source mode; exe builds are pre-baked)
NB2PDF_LANG=en nb2pdf gui   # English UI
NB2PDF_LANG=zh nb2pdf gui   # Chinese UI (default)

# Show version
nb2pdf --version

# Convert (PDF next to notebook)
nb2pdf convert notebook.ipynb

# Custom output path
nb2pdf convert notebook.ipynb -o output.pdf

# Batch convert
nb2pdf convert "D:\notebooks\*.ipynb"

# Batch from different directories into one output dir
nb2pdf convert "D:\a\nb1.ipynb" "E:\b\nb2.ipynb" -d "D:\pdfs"
```

Or run as a module:

```bash
python -m nb2pdf convert examples/Seq2Seq教程.ipynb
```

### Dependencies

| Package                     | Purpose                             |
| --------------------------- | ----------------------------------- |
| `nbconvert[webpdf]>=7.16.0` | notebook → HTML → PDF               |
| `nbformat>=5.9.0`           | Read/write `.ipynb`                 |
| `playwright>=1.40.0`        | Drive Chromium                      |
| `Pillow>=10.0.0`            | Image handling & tall-image slicing |

```bash
pip install -r requirements.txt
```

## Features

| Feature                  | Description                                                                  |
| ------------------------ | ---------------------------------------------------------------------------- |
| GUI                      | Batch multi-select, output dir, progress/log, cancel                          |
| Any directory            | Run the exe anywhere; mix notebooks from different folders                    |
| Full input               | Export all Markdown & code cells                                              |
| Trimmed output           | Keep head + tail of long stdout — final loss/summary preserved                |
| Log compression          | Merge interleaved log chunks; collapse tqdm/keras progress bars & repeated `Batch/Loss` lines |
| Install-log suppression  | Collapse `%pip install` etc. logs to one line, keep `Successfully installed`/`ERROR:` |
| Embedded images          | matplotlib plots, local Markdown images (`./xxx.png`)                         |
| Tall-image slicing       | Auto-split images taller than 3000px to avoid PDF overlap                     |
| Text PDF                 | Vector text, selectable & copyable                                            |

## Configuration

Top of `nb2pdf/converter.py`:

| Constant                 | Default | Description                                        |
| ------------------------ | ------- | -------------------------------------------------- |
| `MAX_STREAM_LINES`       | 40      | Max stdout lines kept                              |
| `STREAM_TAIL_LINES`      | 12      | Of those, kept from the end                        |
| `MAX_TEXT_CHARS`         | 2500    | Max text/plain chars                               |
| `TEXT_TAIL_CHARS`        | 400     | Of those, kept from the end                        |
| `MAX_TRACEBACK_LINES`    | 20      | Max traceback lines                                |
| `TRACEBACK_TAIL_LINES`   | 12      | Of those, kept from the end (error message)        |
| `RUN_COLLAPSE_MIN`       | 8       | Collapse runs of ≥N similar lines                  |
| `INSTALL_LOG_KEEP_LINES` | 10      | Key lines kept from install logs                   |
| `PAGE_GOTO_TIMEOUT_MS`   | 120000  | Playwright navigation timeout (ms)                 |

## Project layout

```
nb2pdf/
├── README.md              # This guide
├── CHANGELOG.md           # Version history
├── LICENSE
├── pyproject.toml
├── requirements.txt       # Runtime deps
└── nb2pdf/                # Python package
    ├── cli.py
    ├── converter.py
    ├── gui.py             # Tkinter GUI
    ├── i18n.py            # UI language layer
    ├── images.py
    └── runtime.py
```

## FAQ

**Conversion timeout (`Page.goto: Timeout exceeded`)**
Fixed in 1.1.0+. Large notebooks may take 1–2 minutes on first run.

**Playwright / asyncio errors on Windows**
Use the `nb2pdf` CLI from this project, not raw `jupyter nbconvert`.

**PDF file locked**
Close the reader and retry; output falls back to `*_new.pdf`.

**Missing Markdown images**
Paths must be relative to the notebook directory and files must exist.

**Image overlaps following text**
Caused by very tall stitched images; auto-sliced in the latest version.

## License

MIT — see [LICENSE](LICENSE).

---

# nb2pdf 中文说明

[English](#nb2pdf) | 中文

将 Jupyter Notebook（`.ipynb`）转为**文本型 PDF**（文字可选中、图片内嵌），适合教程讲义阅读与打印。

**当前版本：1.3.0**

## 两种使用方式

| 方式       | 适合人群            | 说明                                                                     |
| ---------- | ------------------- | ------------------------------------------------------------------------ |
| **exe**    | 不想装 Python 的用户 | 从 [GitHub Releases](https://github.com/S0mu7l/nb2pdf/releases) 下载       |
| **源码**   | 开发者、需要自定义的用户 | 克隆本仓库，用 Python 安装运行（见下文）                                     |

**exe 下载**（v1.3.0，见 [GitHub Releases](https://github.com/S0mu7l/nb2pdf/releases)）：

- 中文界面：`nb2pdf-zh-windows-1.3.0.rar` → 解压得 `nb2pdf-zh.exe`
- English UI：`nb2pdf-en-windows-1.3.0.rar` → 解压得 `nb2pdf-en.exe`

两个版本均支持中文路径，按需下载其一即可。

## 更新日志

### 1.3.0

- **日志压缩**：合并单元格内交错的 stream 输出块（logging 与 tqdm 交替写入会绕过逐块截断，实测一份课件 PDF 从 79 页降到 30 页）；`\r` 进度条（tqdm/keras）只保留最终帧；连续 ≥8 行同模式日志（如 `Batch 3/500, Loss: 0.11`）折叠为首尾几行
- **头尾截断**：长输出、`text/plain` 与 traceback 截断时同时保留结尾——最终 loss、DataFrame 形状、错误消息不再被截掉
- **安装日志压缩**：`%pip install` / `!pip install` / `conda|mamba|uv|apt install` 单元格的下载日志压缩为一行省略提示，仅保留 `Successfully installed …` 与 `ERROR:` 关键行
- **修复**：截断预处理器此前执行两遍，导致截断提示中的总行数统计错误

### 1.2.0

- **图形界面**：Tkinter GUI，批量多选、选择输出目录、进度日志、可取消；双击 exe 或 `nb2pdf gui` 即可打开
- **批量**：新增 `-d/--output-dir` 统一输出目录；支持跨目录混合批量转换
- **打包**：由 PyInstaller 改为 **Nuitka** 单文件；终端有输出、双击无黑框
- **中英双版本**：`nb2pdf-zh.exe` + `nb2pdf-en.exe`，均支持中文路径

完整记录见 [CHANGELOG.md](CHANGELOG.md)。

## 源码安装

### 环境要求

- Python 3.9+
- Windows 10/11（64 位，推荐；其他平台可能可用）
- 推荐安装 [Google Chrome](https://www.google.com/chrome/)（优先使用系统 Chrome）

### 安装

```bash
git clone https://github.com/S0mu7l/nb2pdf.git
cd nb2pdf
pip install -e .
python -m playwright install chromium
```

若本机已安装 Chrome，可跳过 `install chromium`。

### 使用

```bash
# 打开图形界面（批量多选、输出目录）
nb2pdf            # 无参数即打开 GUI
nb2pdf gui

# 界面语言（源码模式；exe 已分别内置）
NB2PDF_LANG=en nb2pdf gui   # 英文界面
NB2PDF_LANG=zh nb2pdf gui   # 中文界面（默认）

# 查看版本
nb2pdf --version

# 转换 notebook（PDF 输出到同目录）
nb2pdf convert notebook.ipynb

# 指定输出路径
nb2pdf convert notebook.ipynb -o output.pdf

# 批量转换
nb2pdf convert "D:\notebooks\*.ipynb"

# 跨目录批量转换到统一输出目录
nb2pdf convert "D:\a\nb1.ipynb" "E:\b\nb2.ipynb" -d "D:\pdfs"
```

也可用模块方式：

```bash
python -m nb2pdf convert examples/Seq2Seq教程.ipynb
```

### 依赖

| 包                          | 用途                     |
| --------------------------- | ------------------------ |
| `nbconvert[webpdf]>=7.16.0` | notebook → HTML → PDF    |
| `nbformat>=5.9.0`           | 读写 `.ipynb`            |
| `playwright>=1.40.0`        | 驱动 Chromium            |
| `Pillow>=10.0.0`            | 图片处理与长图切片        |

```bash
pip install -r requirements.txt
```

## 功能说明

| 功能           | 说明                                                          |
| -------------- | ------------------------------------------------------------- |
| 图形界面       | 批量多选、输出目录、进度日志、可取消                             |
| 任意目录       | exe 任意位置运行，可混选不同目录文件                             |
| 完整 input     | Markdown 与代码单元格全部导出                                   |
| 精简 output    | 长输出保留头尾——结尾的最终结果不丢失                             |
| 日志压缩       | 合并交错日志块；折叠 tqdm/keras 进度条与重复训练日志行            |
| 安装日志压缩   | `%pip install` 等安装日志压缩为一行，保留关键行                  |
| 内嵌图片       | matplotlib 图表、本地 Markdown 图片（`./xxx.png`）              |
| 长图切片       | 高于 3000px 的图自动切片，避免 PDF 重叠                          |
| 文本型 PDF     | 矢量文字，可选中复制                                            |

## 配置项

位于 `nb2pdf/converter.py` 顶部：

| 常量                     | 默认值  | 说明                                   |
| ------------------------ | ------- | -------------------------------------- |
| `MAX_STREAM_LINES`       | 40      | stdout 保留行数                        |
| `STREAM_TAIL_LINES`      | 12      | 其中留给结尾的行数                      |
| `MAX_TEXT_CHARS`         | 2500    | text/plain 字符上限                    |
| `TEXT_TAIL_CHARS`        | 400     | 其中留给结尾的字符数                    |
| `MAX_TRACEBACK_LINES`    | 20      | traceback 行数上限                     |
| `TRACEBACK_TAIL_LINES`   | 12      | 其中留给结尾的行数（错误消息在结尾）      |
| `RUN_COLLAPSE_MIN`       | 8       | 连续 ≥N 行相似日志折叠                  |
| `INSTALL_LOG_KEEP_LINES` | 10      | 安装日志保留的关键行数上限               |
| `PAGE_GOTO_TIMEOUT_MS`   | 120000  | 页面导航超时（毫秒）                    |

## 项目结构

```
nb2pdf/
├── README.md              # 本说明
├── CHANGELOG.md           # 版本更新记录
├── LICENSE
├── pyproject.toml
├── requirements.txt       # 运行依赖
└── nb2pdf/                # 源码包
    ├── cli.py
    ├── converter.py
    ├── gui.py             # Tkinter 图形界面
    ├── i18n.py            # 界面语言层
    ├── images.py
    └── runtime.py
```

## 常见问题

**转换超时（`Page.goto: Timeout exceeded`）**
1.1.0 已修复；大 notebook 首次转换可能需要 1–2 分钟。

**Windows 上 Playwright / asyncio 报错**
请使用本项目的 `nb2pdf` 命令，不要直接用 `jupyter nbconvert`。

**PDF 被占用**
关闭阅读器后重试；输出会回退为 `*_new.pdf`。

**Markdown 图片缺失**
图片路径需相对 notebook 目录且文件存在。

**图片与文字重叠**
超长拼接图导致；最新版本会自动切片。

## 许可证

MIT — 见 [LICENSE](LICENSE)。
