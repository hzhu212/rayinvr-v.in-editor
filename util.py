import json
import logging
import numpy as np
import os
import re
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
    def __init__(self, delegate=None, allowed_attrs=None):
        self.delegate = delegate
        self.allowed_attrs = allowed_attrs
        # Cache is used to only remove added attributes when changing the delegate.
        self._cache = set()

    def __getattr__(self, name):
        if (self.allowed_attrs is not None) and (name not in self.allowed_attrs):
            raise AttributeError(
                'Attribute "%s" is not allowed by %s' %(name, type(self).__name__))
        attr = getattr(self.delegate, name)
        setattr(self, name, attr)
        self._cache.add(name)
        return attr

    def resetcache(self):
        """Removes added attributes while leaving original attributes."""
        for key in self._cache:
            try:
                delattr(self, key)
            except AttributeError:
                pass
        self._cache.clear()

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

    def clear(self):
        self.data = {
            'file': '',
            'pois': '',
        }

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

    def get_session_data(self, sid):
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


def parse_pois_str(pois_str):
    """Parse poission string copied from r.in.
    A poission string consists of 4 parts:
    1. pois - an array containing the value of Poisson's ratio for each model layer.
    2. poisl, 3. poisb - arrays specifying the layers and block numbers, respectively,
        of model trapezoids within which Poisson's ratio is modified over that given
        by pois using the array poisbl; for poisb, the trapezoids with a layer are
        numbered from left to right.
    4. poisbl - an array containing the value of Poisson's ratio for the model trapezoids
        specified in the arrays poisl and poisb overriding the values assigned using
        the array pois.
    The last 3 parts are optional.
    Here is an example of `pois_str`:
        pois_str = '''pois=0.4999,0.4852,0.4770,0.4620,0.4700,
        poisl=2,2,2,2,3,3,
        poisb=2,3,5,6,2,4,
        poisbl=0.485,0.487,0.476,0.458,0.462,0.489,'''
    """
    res = {}
    names = ['pois', 'poisl', 'poisb', 'poisbl']
    parts = re.split('\s*\n\s*', pois_str.strip())
    if len(parts) not in (1, 4):
        raise ValueError('Invalid poission string: %r ...' %(pois_str[:50]))
    for part in parts:
        name, value = part.split('=')
        res[name] = eval('[' + value + ']')
    if len(parts) == 4:
        if set(res.keys()) != set(names):
            raise ValueError('Invalid poission string: should contain and only contain %r' %','.join(names))
        if not (len(res['poisl']) == len(res['poisb']) and len(res['poisl']) == len(res['poisbl'])):
            raise ValueError('Invalid poission string: poisl, poisb and poisbl should be in the same length')
    elif len(parts) == 1:
        if list(res.keys()) != ['pois']:
            raise ValueError('Invalid poission string: should contain a filed %r' %('pois'))
    return res
