"""PyInstaller frozen-runtime configuration. PyInstaller 打包运行时环境配置。"""
import os
import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def setup_frozen() -> None:
    """Initialize paths and env vars when bundled as exe. 打包为 exe 后初始化路径与环境变量。"""
    if not is_frozen():
        return

    bundle = getattr(sys, "_MEIPASS", "")
    if bundle and bundle not in sys.path:
        sys.path.insert(0, bundle)

    # Playwright browsers live in user dir, not inside exe
    # Playwright 浏览器安装在用户目录，不打包进 exe
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(local, "ms-playwright"))
