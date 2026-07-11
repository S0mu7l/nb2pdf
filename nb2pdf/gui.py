"""Tkinter GUI: batch-select notebooks and convert to PDF.
图形界面：批量选择 notebook 并转换为 PDF。"""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from nb2pdf._version import __version__
from nb2pdf.i18n import AUTHOR, GITHUB_URL, tr

_PAD = 8


class App:
    """Main window. 主窗口。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.files: list[str] = []
        self.worker: threading.Thread | None = None
        self.cancel_flag = threading.Event()
        self.msg_queue: queue.Queue[tuple] = queue.Queue()

        root.title(tr("window_title", version=__version__))
        root.geometry("780x600")
        root.minsize(640, 500)

        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")

        self._set_window_icon()
        self._build_widgets()
        self.root.after(100, self._poll_queue)

    def _set_window_icon(self) -> None:
        """Best-effort window icon; bundled at <root>/assets/nb2pdf.png.
        尽力设置窗口图标；图标随包放在 assets/nb2pdf.png。"""
        icon = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "nb2pdf.png",
        )
        try:
            if os.path.isfile(icon):
                # keep a reference so Tk does not garbage-collect the image
                # 保留引用，防止图片对象被回收导致图标失效
                self._icon_image = tk.PhotoImage(file=icon)
                self.root.iconphoto(True, self._icon_image)
        except Exception:
            pass

    # ------------------------------------------------------------------ UI

    def _build_widgets(self) -> None:
        top = ttk.Frame(self.root, padding=_PAD)
        top.pack(fill="x")

        ttk.Button(top, text=tr("add_files"), command=self.add_files).pack(side="left")
        ttk.Button(top, text=tr("remove_selected"), command=self.remove_selected).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(top, text=tr("clear"), command=self.clear_files).pack(
            side="left", padx=(6, 0)
        )
        self.count_label = ttk.Label(top, text=tr("file_count", n=0))
        self.count_label.pack(side="right")

        list_frame = ttk.Frame(self.root, padding=(_PAD, 0, _PAD, 0))
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode="extended", activestyle="dotbox")
        ysb = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        xsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.listbox.xview)
        self.listbox.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.listbox.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        out_frame = ttk.Frame(self.root, padding=_PAD)
        out_frame.pack(fill="x")
        ttk.Label(out_frame, text=tr("output_dir")).pack(side="left")
        self.outdir_var = tk.StringVar()
        ttk.Entry(out_frame, textvariable=self.outdir_var).pack(
            side="left", fill="x", expand=True, padx=6
        )
        ttk.Button(out_frame, text=tr("browse"), command=self.pick_outdir).pack(side="left")
        ttk.Label(
            self.root,
            text=tr("output_hint"),
            foreground="#666",
            padding=(_PAD, 0, _PAD, 0),
        ).pack(fill="x")

        act = ttk.Frame(self.root, padding=_PAD)
        act.pack(fill="x")
        self.convert_btn = ttk.Button(act, text=tr("convert"), command=self.start_convert)
        self.convert_btn.pack(side="left")
        self.cancel_btn = ttk.Button(
            act, text=tr("cancel"), command=self.cancel_convert, state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=(6, 0))
        self.install_btn = ttk.Button(
            act, text=tr("install_browser"), command=self.install_browser
        )
        self.install_btn.pack(side="right")

        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill="x", padx=_PAD)

        self.status_var = tk.StringVar(value=tr("ready"))
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, padding=(_PAD, 4))
        self.status_label.pack(fill="x")

        log_frame = ttk.Frame(self.root, padding=(_PAD, 0, _PAD, 0))
        log_frame.pack(fill="both", expand=True)
        # wrap="word": long paths/messages wrap to the window width instead
        # of running off-screen / 长路径与消息按窗口宽度自动换行，不再横向溢出
        self.log_text = tk.Text(log_frame, height=8, state="disabled", wrap="word")
        log_ysb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_ysb.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_ysb.grid(row=0, column=1, sticky="ns")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        # Footer: author + GitHub link, bottom-right / 底部右侧：作者与 GitHub 链接
        footer = ttk.Frame(self.root, padding=(_PAD, 2, _PAD, 4))
        footer.pack(fill="x", side="bottom")
        link = tk.Label(
            footer,
            text="GitHub: S0mu7l/nb2pdf",
            foreground="#0969da",
            cursor="hand2",
        )
        link.pack(side="right")
        link.bind("<Button-1>", lambda _e: webbrowser.open(GITHUB_URL))
        link.bind("<Enter>", lambda _e: link.config(font=(None, 9, "underline")))
        link.bind("<Leave>", lambda _e: link.config(font=(None, 9, "normal")))
        link.config(font=(None, 9, "normal"))
        author = ttk.Label(footer, text=f"{tr('author')}: {AUTHOR}   ")
        author.pack(side="right")

    # -------------------------------------------------------------- actions

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title=tr("select_files_title"),
            filetypes=[("Jupyter Notebook", "*.ipynb"), ("All files", "*.*")],
        )
        added = 0
        for p in paths:
            p = os.path.abspath(p)
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", p)
                added += 1
        if added:
            self._update_count()

    def remove_selected(self) -> None:
        for idx in reversed(self.listbox.curselection()):
            self.listbox.delete(idx)
            del self.files[idx]
        self._update_count()

    def clear_files(self) -> None:
        self.listbox.delete(0, "end")
        self.files.clear()
        self._update_count()

    def pick_outdir(self) -> None:
        path = filedialog.askdirectory(title=tr("select_outdir_title"))
        if path:
            self.outdir_var.set(os.path.abspath(path))

    def _update_count(self) -> None:
        self.count_label.config(text=tr("file_count", n=len(self.files)))

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.convert_btn.config(state=state)
        self.install_btn.config(state=state)
        self.cancel_btn.config(state="normal" if running else "disabled")
        if running:
            self.status_label.config(foreground="")

    def _notify_done(self, text: str, failed: bool) -> None:
        """Completion notice inside the window — no popup dialog.
        完成通知显示在窗口内，不再弹出对话框。"""
        self.status_var.set(text)
        self.log(text)
        self.status_label.config(foreground="#b91c1c" if failed else "#15803d")
        # Flash the taskbar button so completion is still noticed when the
        # window is in the background / 任务栏闪烁提示，窗口在后台时也能察觉完成
        if sys.platform == "win32":
            try:
                import ctypes

                class _FLASHWINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_uint),
                        ("hwnd", ctypes.c_void_p),
                        ("dwFlags", ctypes.c_uint),
                        ("uCount", ctypes.c_uint),
                        ("dwTimeout", ctypes.c_uint),
                    ]

                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                # FLASHW_ALL | FLASHW_TIMERNOFG: flash until window is focused
                info = _FLASHWINFO(ctypes.sizeof(_FLASHWINFO), hwnd, 0x3 | 0xC, 0, 0)
                ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))
            except Exception:
                pass

    def log(self, text: str) -> None:
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # -------------------------------------------------------------- convert

    def start_convert(self) -> None:
        if not self.files:
            messagebox.showwarning("nb2pdf", tr("need_files"))
            return

        outdir = self.outdir_var.get().strip()
        if outdir:
            try:
                os.makedirs(outdir, exist_ok=True)
            except OSError as exc:
                messagebox.showerror("nb2pdf", tr("outdir_error", err=exc))
                return

        self.cancel_flag.clear()
        self._set_running(True)
        self.progress.config(maximum=len(self.files), value=0)
        files = list(self.files)
        self.worker = threading.Thread(
            target=self._convert_worker, args=(files, outdir), daemon=True
        )
        self.worker.start()

    def cancel_convert(self) -> None:
        self.cancel_flag.set()
        self.msg_queue.put(("status", tr("cancelling")))

    def _convert_worker(self, files: list[str], outdir: str) -> None:
        from nb2pdf.converter import convert

        ok = fail = 0
        total = len(files)
        for i, nb_path in enumerate(files, 1):
            if self.cancel_flag.is_set():
                self.msg_queue.put(("log", tr("cancelled_skip", n=total - i + 1)))
                break
            name = os.path.basename(nb_path)
            self.msg_queue.put(("status", tr("converting", i=i, total=total, name=name)))
            try:
                output = None
                if outdir:
                    stem = os.path.splitext(os.path.basename(nb_path))[0]
                    output = os.path.join(outdir, stem + ".pdf")
                out = convert(nb_path, output)
                ok += 1
                self.msg_queue.put(("log", f"OK    {nb_path} -> {out}"))
            except Exception as exc:
                fail += 1
                self.msg_queue.put(("log", f"FAIL  {nb_path}: {exc}"))
            self.msg_queue.put(("progress", i))
        self.msg_queue.put(("done", ok, fail))

    # ------------------------------------------------------ install browser

    def install_browser(self) -> None:
        if not messagebox.askyesno("nb2pdf", tr("install_confirm")):
            return
        self._set_running(True)
        self.cancel_btn.config(state="disabled")
        self.status_var.set(tr("installing"))
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self) -> None:
        from nb2pdf.converter import install_browser

        try:
            code = install_browser()
            failed = code != 0
            msg = tr("install_ok") if code == 0 else tr("install_fail_code", code=code)
        except Exception as exc:
            failed = True
            msg = tr("install_fail", err=exc)
        self.msg_queue.put(("install_done", msg, failed))

    # ----------------------------------------------------------- msg pump

    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                kind = msg[0]
                if kind == "log":
                    self.log(msg[1])
                elif kind == "status":
                    self.status_var.set(msg[1])
                elif kind == "progress":
                    self.progress.config(value=msg[1])
                elif kind == "done":
                    ok, fail = msg[1], msg[2]
                    self._set_running(False)
                    self._notify_done(tr("done_summary", ok=ok, fail=fail), failed=bool(fail))
                elif kind == "install_done":
                    self._set_running(False)
                    self._notify_done(msg[1], failed=msg[2])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)


def run_gui(initial_files: list[str] | None = None) -> int:
    """Launch the GUI. 启动图形界面。"""
    root = tk.Tk()
    app = App(root)
    for p in initial_files or []:
        p = os.path.abspath(p)
        if p not in app.files:
            app.files.append(p)
            app.listbox.insert("end", p)
    app._update_count()
    root.mainloop()
    return 0
