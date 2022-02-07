#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import collections
import curses
import curses.ascii
import curses.panel
import sys
import select
import threading
from typing import Tuple

#gui = None


class LockedCurses(threading.Thread):
    """
    This class essentially wraps curses operations so that they
    can be used with threading.  Noecho and cbreak are always in
    force.

    Usage: call start() to start the thing running.  Then call
    newwin, new_panel, mvaddstr, and other standard curses functions
    as usual.

    Call teardown() to end.

    Note: it's very important that the user catch things like
    keyboard interrupts and redirect them to make us shut down
    cleanly.  (This could be improved...)
    """

    def __init__(self):
        super(LockedCurses, self).__init__()
        self._lock = threading.Lock()

        # generic cond var
        self._cv = threading.Condition(self._lock)
        # results-updated cond var
        self._resultcv = threading.Condition(self._lock)

        self._workqueue = collections.deque()
        self._starting = False
        self._running = False
        self._do_quit = False
        self._screen = None
        self._ticket = 0
        self._served = -1
        self._result = {}

    def start(self):
        assert(not self._running)
        assert(self._screen is None)
        self._screen = curses.initscr()
        with self._lock:
            self._starting = True
            super(LockedCurses, self).start()
            while self._starting:
                self._cv.wait()

    def _waitch(self):
        """
        Wait for a character to be readable from sys.stdin.
        Return True on success.

        Unix-specific (ugh)
        """
        while True:
            with self._lock:
                if not self._running:
                    return False
            # Wait about 0.1 second for a result.  Really, should spin
            # off a thread to do this instead.
            l = select.select([sys.stdin], [], [], 0.1)[0]
            if len(l) > 0:
                return True
            # No result: go around again to recheck self._running.

    def run(self):
        # This happens automatically inside the new thread; do not
        # call it yourself!
        assert(not self._running)
        assert(self._screen is not None)
        curses.savetty()
        curses.noecho()
        # curses.cbreak()
        self._running = True
        self._starting = False
        with self._lock:
            self._cv.notifyAll()
            while not self._do_quit:
                while len(self._workqueue) == 0 and not self._do_quit:
                    self._cv.wait()
                # we have work to do, or were asked to quit
                while len(self._workqueue):
                    ticket, func, args, kwargs = self._workqueue.popleft()
                    self._result[ticket] = func(*args, **kwargs)
                    self._served = ticket
                    self._resultcv.notifyAll()

            # Quitting!  NB: resettty should do all of this for us
            # curses.nocbreak()
            # curses.echo()
            curses.resetty()
            curses.endwin()
            self._running = False
            self._cv.notifyAll()

    def teardown(self):
        with self._lock:
            if not self._running:
                return
            self._do_quit = True
            while self._running:
                self._cv.notifyAll()
                self._cv.wait()

    def refresh(self):
        s = self._screen
        if s is not None:
            self._passthrough('refresh', s.refresh)

    def _passthrough(self, fname, func, *args, **kwargs):
        with self._lock:
            if not self._running:
                raise ValueError('called {}() while not running'.format(fname))
            # Should we check for self._do_quit here?  If so,
            # what should we return?
            ticket = self._ticket
            self._ticket += 1
            self._workqueue.append((ticket, func, args, kwargs))
            while self._served < ticket:
                self._cv.notifyAll()
                self._resultcv.wait()
            return self._result.pop(ticket)

    def newwin(self, *args, **kwargs):
        w = self._passthrough('newwin', curses.newwin, *args, **kwargs)
        return WinWrapper(self, w)

    def new_panel(self, win, *args, **kwargs):
        w = win._interior
        p = self._passthrough('new_panel', curses.panel.new_panel, w,
                              *args, **kwargs)
        return LockedWrapper(self, p)

    def getmaxyx(self) -> Tuple[int, int]:
        return self._screen.getmaxyx()


class LockedWrapper(object):
    """
    Wraps windows and panels and such.  locker is the LockedCurses
    that we need to use to pass calls through.
    """

    def __init__(self, locker, interior_object):
        self._locker = locker
        self._interior = interior_object

    def __getattr__(self, name):
        i = self._interior
        l = self._locker
        a = getattr(i, name)
        if callable(a):
            # return a function that uses passthrough
            return lambda *args, **kwargs: l._passthrough(name, a,
                                                          *args, **kwargs)
        # not callable, just return the attribute directly
        return a


class WinWrapper(LockedWrapper):
    def getch(self):
        """
        Overrides basic getch() call so that it's specifically *not*
        locked.  This is a bit tricky.
        """
        # (This should really test for nodelay mode too though.)
        l = self._locker
        ok = l._waitch()
        if ok:
            return l._passthrough('getch', self._interior.getch)
        return curses.ERR

    def getstr(self, y, x, maxlen):
        self.move(y, x)
        s = ""
        while True:
            self.refresh()
            c = self.getch()
            if c in (curses.ERR, ord('\r'), ord('\n')):
                break
            if c in (ord('\b'), ord('\x7f')):
                if len(s) > 0:
                    s = s[:-1]
                    x -= 1
                    self.addch(y, x, ' ')
                    self.move(y, x)
            else:
                if curses.ascii.isprint(c) and len(s) < maxlen:
                    c = chr(c)
                    s += c
                    self.addch(c)
                    x += 1
        return s
