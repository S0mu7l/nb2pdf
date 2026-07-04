# nb2pdf — Executable / 可执行文件版

Convert Jupyter Notebook (`.ipynb`) to PDF with selectable text and embedded images.

将 Jupyter Notebook（`.ipynb`）转为 PDF。文字可选中复制，图片自动内嵌。

**No Python required** — just run the exe after extracting the archive.

**无需安装 Python**，解压后运行 exe 即可。

**Current version / 当前版本：1.2.0**　|　Author / 作者：**s0mu7l**　|　[GitHub](https://github.com/S0mu7l/nb2pdf)

## Two language editions / 两个语言版本


| File / 文件         | UI language / 界面语言   | Chinese paths / 中文路径 |
| ----------------- | -------------------- | -------------------- |
| `nb2pdf-zh.exe`   | 简体中文                 | ✅ 支持                 |
| `nb2pdf-en.exe`   | English              | ✅ Supported          |

> Both editions are identical except for the interface language — **Chinese/CJK file paths work in both**. Pick whichever you prefer.
>
> 两个版本仅界面语言不同，**中文路径两个版本都完整支持**，按喜好选择即可。

## Download / 获取方式

1. Open the project **GitHub Releases** page / 打开 [GitHub Releases](https://github.com/S0mu7l/nb2pdf/releases) 页面
2. Download `nb2pdf-windows-v1.2.0.zip` (or latest) / 下载最新版压缩包
3. Extract to get `nb2pdf-zh.exe`, `nb2pdf-en.exe` and this README / 解压得到两个 exe 与本说明

Need source install or customization? See [README.md](../README.md) in the repo root.

需要源码安装或修改代码？请查看仓库根目录 [README.md](../README.md)。

## GUI / 图形界面（推荐）

**Double-click the exe** to open the GUI — no black console window.

**双击 exe** 即可打开图形界面，不会弹出黑色控制台窗口。

- **添加文件 / Add files**：multi-select `.ipynb` files, from **any folders**, added in batches / 可多选、可多次添加、可来自**不同目录**
- **输出目录 / Output dir**：leave empty to save each PDF next to its notebook / 留空则输出到各 notebook 同目录
- **开始转换 / Convert**：progress bar + per-file log; cancel anytime / 进度条与逐文件日志，可随时取消
- Bottom-right shows the author and a clickable GitHub link / 界面右下角为作者信息与 GitHub 链接

You may copy the exe to any folder — it works from any path. / exe 可放在任意目录运行。

## Command line / 命令行

The same exe also works in PowerShell / CMD (examples use `nb2pdf-zh.exe`; the `-en` edition behaves identically):

同一个 exe 也可在终端使用（示例用 `nb2pdf-zh.exe`，英文版用法完全相同）：

```powershell
# Version (expect nb2pdf 1.2.0) / 查看版本
.\nb2pdf-zh.exe --version

# Open GUI explicitly / 打开图形界面
.\nb2pdf-zh.exe gui

# Convert (Chinese paths supported) / 转换 notebook
.\nb2pdf-zh.exe convert "D:\课程\notebook.ipynb"

# Custom output / 指定输出路径
.\nb2pdf-zh.exe convert notebook.ipynb -o output.pdf

# Batch (glob) / 批量转换
.\nb2pdf-zh.exe convert "D:\notebooks\*.ipynb"

# Batch from different directories into one folder / 跨目录批量 + 统一输出目录
.\nb2pdf-zh.exe convert "D:\a\nb1.ipynb" "E:\b\nb2.ipynb" -d "D:\pdfs"
```

## First run / 首次使用

If **Google Chrome** is installed, convert directly — no extra setup.

若本机已安装 **Google Chrome**，可直接转换。

Otherwise install the browser engine first (also available as a button in the GUI):

若没有 Chrome，请先安装浏览器内核（图形界面中也有对应按钮）：

```powershell
.\nb2pdf-zh.exe install-browser
```

Chromium is stored in `%LOCALAPPDATA%\ms-playwright` (~150 MB, once). / 只需下载一次。

## System requirements / 系统要求

- Windows 10/11 (64-bit) / Windows 10/11（64 位）
- Google Chrome recommended / 推荐 Google Chrome

## What's new in 1.2.0 / 1.2.0 更新说明

- **GUI / 图形界面**：double-click to open; batch multi-select, output dir, progress & log, cancel / 双击即用；批量多选、输出目录、进度日志、可取消
- **Two editions / 双语言版本**：`nb2pdf-zh.exe` 中文界面、`nb2pdf-en.exe` English UI；both support Chinese paths / 均支持中文路径
- **Batch across folders / 跨目录批量**：mix notebooks from different directories; CLI adds `-d` output dir / 支持混选不同目录文件；命令行新增 `-d` 统一输出目录
- **App icon & author / 图标与作者**：custom PDF-document icon; author & GitHub link in the GUI / 自定义图标；界面显示作者与 GitHub 链接
- **Nuitka build / Nuitka 打包**：no console flash on double-click; runtime files cached in `%LOCALAPPDATA%\nb2pdf` (ASCII path, faster startup, Chinese paths OK) / 双击无黑框；运行时文件缓存于英文路径，启动更快，中文路径无忧

## FAQ / 常见问题

**Double-click shows nothing? / 双击没反应？**  
First launch extracts runtime files to `%LOCALAPPDATA%\nb2pdf` and may take a few seconds. / 首次启动需解压运行时文件，稍等几秒。

**Conversion slow / 转换耗时**  
Large notebooks may take 1–2 minutes. / 大 notebook 可能需要 1–2 分钟。

**PDF locked / PDF 被占用**  
Close the reader; output may save as `*_new.pdf`. / 关闭阅读器后重试。

**Missing Markdown images / Markdown 图片缺失**  
Image paths must be relative to the notebook folder and files must exist. / 路径需相对 notebook 目录且文件存在。

**Antivirus false positive / 杀毒软件误报**  
Possible for packed exes; add trust or use source install. / 可添加信任或改用源码方式。

---

Author / 作者：**s0mu7l** · GitHub: <https://github.com/S0mu7l/nb2pdf> · License: MIT
