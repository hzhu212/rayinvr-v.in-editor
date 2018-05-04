import json
import logging
import numpy as np
import os
from scipy.interpolate import griddata
import tkinter as tk

from definitions import ROOT_DIR


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


class Delegator(object):
    """Delegator Base Class"""
    def __init__(self, delegate=None):
        self.delegate = delegate
        # Cache is used to only remove added attributes when changing the delegate.
        self.__cache = set()

    def __getattr__(self, name):
        attr = getattr(self.delegate, name)
        setattr(self, name, attr)
        self.__cache.add(name)
        return attr

    def resetcache(self):
        """Removes added attributes while leaving original attributes."""
        for key in self.__cache:
            try:
                delattr(self, key)
            except AttributeError:
                pass
        self.__cache.clear()

    def setdelegate(self, delegate):
        """Reset attributes and change delegate."""
        self.resetcache()
        self.delegate = delegate


class BaseConfigManager(object):
    """Base class for managing json config"""
    def __init__(self):
        self.autosave = None
        self.store = None
        self.data = None

    def load(self):
        with open(self.store, 'r', encoding='utf8') as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError:
                return None

    def save(self):
        with open(self.store, 'w', encoding='utf8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def __str__(self):
        return self.data.__str__()

    def __getitem__(self, *args, **kw):
        return self.data.__getitem__(*args, **kw)

    def __setitem__(self, *args, **kw):
        self.data.__setitem__(*args, **kw)
        if self.autosave:
            self.save()

    def __getattr__(self, attr):
        print('%s getattr: %s' %(type(self).__name__, attr))
        return getattr(self.data, attr)

    def update(self, *args, **kw):
        self.data.update(*args, **kw)
        if self.autosave:
            self.save()

    def get(self, key):
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value
        if self.autosave:
            self.save()


class SessionManager(BaseConfigManager):
    """Manage application session"""
    def __init__(self, autosave=False):
        self.autosave = autosave
        self.store = os.path.join(ROOT_DIR, 'config', 'session')
        self.data = {
            'file': '',
            'pois': '',
        }
        if self.autosave:
            self.save


class HistoryManager(BaseConfigManager):
    """Manage application history"""
    def __init__(self, autosave=False):
        self.autosave = autosave
        self.store = os.path.join(ROOT_DIR, 'config', 'history')
        self.data = {
            'recent_opens': [],
            'sessions': [],
        }
        if os.path.isfile(self.store):
            temp = self.load()
            if temp: self.data = temp
        else:
            self.save()

    def merge_session(self, sess):
        """Merge the most recent session to history"""
        sess_data = sess.data.copy()
        file = sess_data['file']
        if file in self.data['recent_opens']:
            idx = self.data['recent_opens'].index(file)
            self.data['recent_opens'].pop(idx)
            self.data['recent_opens'].insert(0, file)
            self.data['sessions'].pop(idx)
            self.data['sessions'].insert(0, sess_data)
        else:
            self.data['recent_opens'].insert(0, file)
            self.data['sessions'].insert(0, sess_data)

        if self.autosave:
            self.save()

    def get_session(self, sid):
        """Get history session by sid. `sid` is a integer(the index of recently opened files)
        or a recently opened file name"""
        if isinstance(sid, int):
            if sid >= len(self.data['sessions']):
                return None
            return self.data['sessions'][sid]

        if sid not in self.data['recent_opens']:
            return None
        idx = self.data['recent_opens'].index(sid)
        return self.data['sessions'][idx]

    def truncate(self, keep=10):
        """Clear old history but keeping the newest `keep` history"""
        self.data['recent_opens'] = self.data['recent_opens'][:keep]
        self.data['sessions'] = self.data['sessions'][:keep]
        if self.autosave:
            self.save()

    def clear(self):
        self.data = {
            'recent_opens': [],
            'sessions': [],
        }
        if self.autosave:
            self.save()
