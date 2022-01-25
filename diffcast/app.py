import difflib
import os
import sys

from PyQt6.QtCore import QSettings, QSize, Qt, QThreadPool
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from diffrunner import DiffRunner
from viewer import DISPLAY_MODES, CodeViewer

try:
    # Include in try/except block if you're also targeting Mac/Linux
    from PyQt5.QtWinExtras import QtWin

    myappid = 'mfitzp.diffcast'
    QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


differ = difflib.Differ()
settings = QSettings("Martin Fitzpatrick", "DiffCast")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DiffCast")

        self.viewer = CodeViewer()
        self.viewer.show()

        vl = QVBoxLayout()

        display = QComboBox()
        for mode, label in DISPLAY_MODES.items():
            display.addItem(label, mode)
        display.currentIndexChanged.connect(
            lambda: self.viewer.set_display_mode(display.currentData())
        )
        vl.addWidget(display)

        controls = QHBoxLayout()

        add_btn = QPushButton("Add")
        add_btn.pressed.connect(self.open_file_dialog)
        controls.addWidget(add_btn)

        del_btn = QPushButton("Remove")
        del_btn.pressed.connect(self.delete_selected_diffs)
        controls.addWidget(del_btn)

        vl.addLayout(controls)

        self.difflist = QListWidget()
        self.difflist.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.difflist.currentRowChanged.connect(self.update_button_state)

        vl.addWidget(self.difflist)

        controls = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.pressed.connect(self.start)
        controls.addWidget(self.start_btn)

        self.prev_btn = QPushButton("Prev")
        self.prev_btn.pressed.connect(self.prev)
        controls.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next")
        self.next_btn.pressed.connect(self.next)
        controls.addWidget(self.next_btn)

        self.stop_btn = QPushButton("Stop")
        controls.addWidget(self.stop_btn)
        vl.addLayout(controls)

        self.update_button_state()

        self.target_file = None
        target_file = QPushButton("Select output file...")
        target_file.pressed.connect(self.select_target_file)
        clear_target_file = QPushButton("Clear")
        clear_target_file.pressed.connect(self.clear_target_file)

        controls = QHBoxLayout()
        controls.addWidget(target_file)
        controls.addWidget(clear_target_file)
        vl.addLayout(controls)

        self.target_file_label = QLineEdit()
        self.target_file_label.setDisabled(True)
        vl.addWidget(self.target_file_label)

        show_hide_filelist = QCheckBox("Show file list")
        show_hide_filelist.setCheckable(True)
        show_hide_filelist.setChecked(False)
        show_hide_filelist.toggled.connect(self.viewer.files.setVisible)
        vl.addWidget(show_hide_filelist)

        container = QWidget()
        container.setLayout(vl)
        self.setCentralWidget(container)

        self.threadpool = QThreadPool()
        self.runner = None

        self.setFixedSize(QSize(300, 400))

    def update_button_state(self, row=None):
        if row is None:
            row = self.difflist.currentRow()

        disable_prev = row == -1 or row == 0
        disable_next = row == -1 or row == self.difflist.count()
        self.prev_btn.setDisabled(disable_prev)
        self.next_btn.setDisabled(disable_next)

    def select_target_file(self):
        filename, _ = QFileDialog.getSaveFileName()

        if filename:
            result = True
            if os.path.exists(filename):
                result = QMessageBox.warning(
                    self, f"File will be overwritten!", f"DiffCast will overwrite '{filename}'"
                )
            if result:

                self.target_file = filename
                self.target_file_label.setText(filename)
                self.viewer.set_active_file(filename)

    def clear_target_file(self):
        self.target_file = None
        self.target_file_label.setText("")

    def diff_file_changed(self, path):
        for idx in range(self.difflist.count()):
            lwi = self.difflist.item(idx)
            if lwi.data(Qt.ItemDataRole.UserRole) == path:
                self.difflist.setCurrentItem(lwi)

    def differ_file_complete(self, filename, source):
        if self.target_file:
            # If file is unset, this will be skipped.
            with open(self.target_file, 'w') as f:
                f.write(''.join(source))

    def delete_selected_diffs(self):
        for lwi in self.difflist.selectedItems():
            self.difflist.takeItem(self.difflist.row(lwi))

    def start(self):
        row = self.difflist.currentRow()
        if row == -1:
            return

        files = []
        for n in range(row, self.difflist.count()):
            lwi = self.difflist.item(n)
            path = lwi.data(Qt.ItemDataRole.UserRole)
            files.append(path)

        self.diff(files)

    def prev(self):
        row = self.difflist.currentRow()
        if row == -1 or row == 0:
            return

        files = []
        for n in range(row, row - 2, -1):
            lwi = self.difflist.item(n)
            path = lwi.data(Qt.ItemDataRole.UserRole)
            files.append(path)

        self.diff(files)

    def next(self):
        row = self.difflist.currentRow()
        if row == -1 or row == self.difflist.count() - 1:
            return

        files = []
        for n in range(row, row + 2):
            lwi = self.difflist.item(n)
            path = lwi.data(Qt.ItemDataRole.UserRole)
            files.append(path)

        self.diff(files)

    def diff(self, files):
        if len(files) > 1:
            self.start_btn.setDisabled(True)
            self.prev_btn.setDisabled(True)
            self.next_btn.setDisabled(True)
            self.runner = DiffRunner(files)
            self.runner.signals.updated.connect(self.viewer.differ_edit)
            self.runner.signals.file_changed.connect(self.diff_file_changed)
            self.runner.signals.file_complete.connect(self.differ_file_complete)
            self.runner.signals.completed.connect(self.differ_complete)

            self.stop_btn.pressed.connect(self.runner.quit)

            self.threadpool.start(self.runner)

    def differ_complete(self):
        self.start_btn.setDisabled(False)

    def open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames()
        if not paths:
            return

        # Sort alphanumerically before adding.
        # FIXME: Split numeric suffix, something smarter?
        paths.sort()

        for path in paths:
            filename = os.path.basename(path)
            lwi = QListWidgetItem(filename)
            lwi.setData(Qt.ItemDataRole.UserRole, path)
            self.difflist.addItem(lwi)

        self.update_button_state()

    def closeEvent(self, e):
        self.viewer.close()
        if self.runner:
            self.runner.quit()
        super().closeEvent(e)


app = QApplication(sys.argv)
app.setWindowIcon(QIcon('images\icon.ico'))
app.setApplicationName("DiffCast")

app.setStyle("Fusion")

darkPalette = app.palette()
darkPalette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
darkPalette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
darkPalette.setColor(
    QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127)
)
darkPalette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
darkPalette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
darkPalette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
darkPalette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
darkPalette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
darkPalette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
darkPalette.setColor(QPalette.ColorRole.Dark, QColor(35, 35, 35))
darkPalette.setColor(QPalette.ColorRole.Shadow, QColor(20, 20, 20))
darkPalette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
darkPalette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
darkPalette.setColor(
    QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127)
)
darkPalette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
darkPalette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
darkPalette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
darkPalette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
darkPalette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
darkPalette.setColor(
    QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(127, 127, 127)
)
app.setPalette(darkPalette)

w = MainWindow()
w.show()

app.exec()

