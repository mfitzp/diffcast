import argparse
import difflib
import sys
import time

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

INITIAL_SPEED = 3
TYPING_SPEED = 0.05
INSERT_SPEED = 1.0
DELETE_SPEED = 0.5

DIFF_NO_CHANGE = ' '
DIFF_INSERTION = '+'
DIFF_DELETION = '-'
DIFF_COMMENT = '?'


def first_whitespace(s):
    return len(s) - len(s.lstrip())


def chunkify(lst, n):
    lst = list(lst)
    return [lst[i : i + n] for i in range(0, len(lst), n)]


class Signals(QObject):
    # emit the row, col and entire text
    updated = pyqtSignal(int, int, list)
    file_changed = pyqtSignal(str)
    file_complete = pyqtSignal(str, list)
    completed = pyqtSignal()


class DiffRunner(QRunnable):

    signals = Signals()

    def __init__(self, files):
        super().__init__()

        # Store the current active text.
        self.current = []
        self.files = files
        self._quit_requested = False
        self._step_over_files = False

    def insert_line(self, line, diffline):
        self.current.insert(line, '\n')
        for n in range(len(diffline)):
            self.current[line] = diffline[:n] + '\n'
            time.sleep(TYPING_SPEED)

            self.signals.updated.emit(line, n, self.current)

    def _indent_line(self, line, nindents):
        chunks = chunkify(range(0, nindents), 4)
        for chunk in chunks:
            n = len(chunk)
            self.current[line] = (' ' * n) + self.current[line]
            time.sleep(TYPING_SPEED)

            self.signals.updated.emit(line, n, self.current)

    def _dedent_line(self, line, ndedents):
        chunks = chunkify(range(0, ndedents), 4)
        for chunk in chunks:
            n = len(chunk)
            self.current[line] = self.current[line][n:]
            time.sleep(TYPING_SPEED)

            self.signals.updated.emit(line, 0, self.current)

    def indent_line(self, line, diffline):
        # diffline has our goal
        current_line = self.current[line]

        #  check for indent difference, bring indent up to level first.
        cstart = first_whitespace(current_line)
        dstart = first_whitespace(diffline)

        # Fix indent differences if there are any.
        # FIXME: Should do in x4 if possible.
        self._indent_line(line, dstart - cstart)
        self._dedent_line(line, cstart - dstart)

    def edit_line(self, line, diffline):

        # diffline has our goal
        current_line = self.current[line]

        # find common start, common end, rewrite the middle.
        for n, (a, b) in enumerate(zip(current_line, diffline)):
            starti = n
            if a != b:
                break

        for n, (a, b) in enumerate(zip(current_line[::-1], diffline[::-1])):
            endi = n
            if a != b:
                break

        to_type_len = len(diffline) - (starti + endi)

        for n in range(to_type_len + 1):
            self.current[line] = (
                current_line[:starti] + diffline[starti : starti + n] + current_line[-endi:]
            )
            time.sleep(TYPING_SPEED)
            self.signals.updated.emit(line, starti + n, self.current)

    def quit(self):
        self._quit_requested = True

    @pyqtSlot()
    def run(self):
        print(self.files)

        initial_file, files = self.files[0], self.files[1:]

        with open(initial_file, 'r') as f1:
            self.current = f1.readlines()

        self.signals.file_changed.emit(initial_file)
        self.signals.file_complete.emit(initial_file, self.current)

        # Update initial state.
        last_line = len(self.current) - 1
        last_char = len(self.current[last_line]) - 1

        self.signals.updated.emit(last_line, last_char, self.current)
        time.sleep(INITIAL_SPEED)

        for file in files:

            if self._quit_requested:
                break

            self.signals.file_changed.emit(file)

            with open(file, 'r') as f2:
                target = f2.readlines()

            diff = difflib.Differ()
            delta = list(diff.compare(self.current, target))

            # Strip comments.
            delta = [d for d in delta if d[0] != DIFF_COMMENT]

            cl, dl = 0, 0  # current line, diff line
            while cl < len(self.current) - 1:

                if self._quit_requested:
                    break

                dc = delta[dl]

                first_char, diffline = dc[0], dc[2:]

                if first_char == DIFF_NO_CHANGE:
                    # continue
                    cl += 1
                    dl += 1
                    continue

                # Temporary look-ahead for whitespace after series of inserts.
                # add the edit early, then convert that edit in the delta list to a comment.
                if first_char == DIFF_INSERTION and diffline.strip():
                    tdl = dl
                    while True:
                        tdl += 1
                        tdc = delta[tdl]
                        tfc, tdiffline = tdc[0], tdc[2:]
                        if tfc != DIFF_INSERTION:
                            break
                        if not tdiffline.strip():  # Empty line.
                            self.insert_line(cl, tdiffline)
                            delta[tdl] = (DIFF_NO_CHANGE, None, '')
                            break

                # End temporary lookahead.

                if dl < len(delta) - 1:
                    # Handle subsequent edit lines, delete>insert = modify
                    dn = delta[dl + 1]
                    next_char, nextdiffline = dn[0], dn[2:]
                else:
                    next_char = None

                if (first_char, next_char) == (DIFF_DELETION, DIFF_INSERTION):
                    # Correct the indentation of the line.
                    self.indent_line(cl, nextdiffline)
                    # Modify diffline to nextdiffline.
                    self.edit_line(cl, nextdiffline)
                    dl += 2  # Advance diff 2, deletion & insertion.
                    cl += 1
                    time.sleep(INSERT_SPEED)
                    continue

                if first_char == DIFF_DELETION:
                    del self.current[cl]  # don't increment cl.
                    self.signals.updated.emit(cl, 0, self.current)
                    dl += 1
                    time.sleep(DELETE_SPEED)
                    continue

                if first_char == DIFF_INSERTION:
                    # add a line at cl in current
                    self.insert_line(cl, diffline)
                    cl += 1
                    dl += 1
                    time.sleep(INSERT_SPEED)
                    continue

            # Emit the completed file edit.
            self.signals.file_complete.emit(file, self.current)

        # We're finished.
        self.signals.completed.emit()
