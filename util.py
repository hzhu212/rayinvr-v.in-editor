import logging
import tkinter as tk


LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


def get_file_logger(name, file, level=logging.INFO):
    if isinstance(level, str) :
        level = LOG_LEVELS.get(level.lower(), logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    file_handler = logging.FileHandler(file, encoding='utf8')
    # file_handler.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


class ScrollText(tk.Frame):
    """Custom tkinter widget: ScrollText"""
    def __init__(self, master, **kw):
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.text = tk.Text(self, **kw)
        self.text.grid(row=0, column=0, sticky='nswe')
        y_scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        y_scroll.grid(row=0, column=1, sticky='ns')
        self.text.config(yscrollcommand=y_scroll.set)

    def get(self):
        return self.text.get('1.0', tk.END)

    def set(self, string):
        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, string)
        self.text.config(state=tk.DISABLED)
