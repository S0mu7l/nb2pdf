"""nb2pdf - Jupyter Notebook to PDF converter. Jupyter Notebook 转 PDF 工具。"""

from nb2pdf._version import __version__

__all__ = ["__version__", "convert", "install_browser"]


def convert(*args, **kwargs):
    from nb2pdf.converter import convert as _convert

    return _convert(*args, **kwargs)


def install_browser():
    from nb2pdf.converter import install_browser as _install

    return _install()
