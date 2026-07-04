"""Frozen-runtime configuration (Nuitka / PyInstaller).
打包运行时环境配置（支持 Nuitka 与 PyInstaller）。"""
import os
import sys


def is_frozen() -> bool:
    """True when running as a bundled exe. 是否运行在打包后的 exe 中。"""
    if getattr(sys, "frozen", False):
        return True
    # Nuitka marks the compiled main module with __compiled__
    # Nuitka 会在编译后的主模块上设置 __compiled__ 标记
    main_mod = sys.modules.get("__main__")
    return main_mod is not None and hasattr(main_mod, "__compiled__")


def _bundle_root() -> str:
    """Directory containing bundled data files. 打包数据文件所在根目录。"""
    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        return meipass
    # Nuitka standalone/onefile: package files sit next to the dist root,
    # i.e. <root>/nb2pdf/runtime.py -> <root>
    # Nuitka 模式：包文件位于解压目录下，取本文件上两级目录
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_frozen() -> None:
    """Initialize paths and env vars when bundled as exe. 打包为 exe 后初始化路径与环境变量。"""
    if not is_frozen():
        return

    # GUI-mode exe may have no console: guard against None stdout/stderr
    # 无控制台窗口时 stdout/stderr 可能为 None，替换为空设备避免 print 报错
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    root = _bundle_root()
    if root and root not in sys.path:
        sys.path.insert(0, root)

    # nbconvert templates are bundled under <root>/share/jupyter
    # nbconvert 模板打包在 <root>/share/jupyter 下，通过 JUPYTER_PATH 指定
    jupyter_share = os.path.join(root, "share", "jupyter")
    if os.path.isdir(jupyter_share):
        existing = os.environ.get("JUPYTER_PATH", "")
        os.environ["JUPYTER_PATH"] = (
            jupyter_share + os.pathsep + existing if existing else jupyter_share
        )

    # Playwright browsers live in user dir, not inside exe
    # Playwright 浏览器安装在用户目录，不打包进 exe
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(local, "ms-playwright"))
