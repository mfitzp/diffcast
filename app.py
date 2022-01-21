import difflib
import os
import sys
from turtle import clear

from PyQt6.Qsci import QsciLexerPython, QsciScintilla
from PyQt6.QtCore import QDir, QFileSystemWatcher, QSettings, QSize, Qt, QThreadPool, QTimer
from PyQt6.QtGui import QAction, QColor, QFileSystemModel, QFont, QFontMetrics, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from diffrunner import DiffRunner

differ = difflib.Differ()
settings = QSettings("Martin Fitzpatrick", "Playdiff")


class Editor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the default font
        font = QFont()
        font.setFamily('Consolas')
        font.setFixedPitch(True)
        font.setPointSize(18)

        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.horizontalAdvance("00000") + 8)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#181818"))
        self.setMarginsForegroundColor(QColor('#888888'))

        # Highlight current line.
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#181818"))
        self.setCaretForegroundColor(QColor("#ffffff"))

        # Use Python lexer.
        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        lexer.setDefaultPaper(QColor('#1e1e1e'))
        lexer.setDefaultColor(QColor('#d4d4d4'))
        lexer.setHighlightSubidentifiers(False)

        """
        0 Default
        1 Comment
        2 Number
        3 Double-quoted string
        4 Single-quoted string
        5 Keyword
        6 Triple single-quoted string
        7 Triple double-quoted string
        8 Class name
        9 Function or method name
        10 Operator
        11 Identifier
        12 Comment block
        13 Unclosed string
        14 Highlighted identifier
        15 Decorator
        16 Double-quoted f-string
        17 Single-quoted f-string
        18 Triple single-quoted f-string
        19 Triple double-quoted f-string
        """

        # light blue c586c0
        # purple c586c0
        # custom dark blue #3D83BD

        lexer.setColor(QColor('#d4d4d4'), 0)  # 0 Default
        lexer.setColor(QColor('#608b4e'), 1)  # 1 Comment
        lexer.setColor(QColor('#b5cea8'), 2)  # 2 Number
        lexer.setColor(QColor('#ce9178'), 3)  # 3 Double-quoted string
        lexer.setColor(QColor('#ce9178'), 4)  # 4 Single-quoted string
        lexer.setColor(QColor('#c586c0'), 5)  # 5 Keyword
        lexer.setColor(QColor('#ce9178'), 6)  # 6 Triple single-quoted string
        lexer.setColor(QColor('#ce9178'), 7)  # 7 Triple double-quoted string
        lexer.setColor(QColor('#4ec9b0'), 8)  # 8 Class name
        lexer.setColor(QColor('#dcdcaa'), 9)  # 9 Function or method name
        lexer.setColor(QColor('#d4d4d4'), 10)  # 10 Operator
        lexer.setColor(QColor('#9cdcfe'), 11)  # 11 Identifier
        lexer.setColor(QColor('#608b4e'), 12)  # 12 Comment block
        lexer.setColor(QColor('#ce9178'), 13)  # 13 Unclosed string
        lexer.setColor(QColor('#3D83BD'), 14)  # 1 Highlighted identifier
        lexer.setColor(QColor('#dcdcaa'), 15)  # 15 Decorator
        lexer.setColor(QColor('#ce9178'), 16)  # 16 Double-quoted f-string
        lexer.setColor(QColor('#ce9178'), 17)  # 17 Single-quoted f-string
        lexer.setColor(QColor('#ce9178'), 18)  # 18 Triple single-quoted f-string
        lexer.setColor(QColor('#ce9178'), 19)  # 19 Triple double-quoted f-string

        lexer.setFont(font)

        self.setLexer(lexer)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, b'Courier')

        # Hide horizontal scrollbar.
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        # Override lexer keywords.
        self.SendScintilla(
            QsciScintilla.SCI_SETKEYWORDS,
            0,
            b"False None True and as assert break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield",
        )
        self.SendScintilla(QsciScintilla.SCI_SETKEYWORDS, 1, b"self")


class NoMouseListView(QListView):
    def mousePressEvent(self, e):
        e.accept()

    def mouseMoveEvent(self, e):
        e.accept()

    def mouseDoubleClickEvent(self, e):
        e.accept()


class CodeViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )

        self.fs = QFileSystemModel()
        self.files = NoMouseListView()
        font = self.files.font()
        font.setPointSize(14)
        self.files.setFont(font)
        self.files.setMaximumWidth(250)
        self.files.setModel(self.fs)
        self.fs.setRootPath(QDir.currentPath())
        self.files.setRootIndex(self.fs.index(QDir.currentPath()))

        # Hide file browser by default.
        self.files.setVisible(False)

        self.editor = Editor()

        hl = QHBoxLayout()
        # hl.setContentsMargins(25, 25, 25, 25)
        hl.addWidget(self.files)
        hl.addWidget(self.editor)

        self.setLayout(hl)

        self.active_file = None

        geometry = settings.value("Geometry/CodeViewer")
        if geometry:
            self.restoreGeometry(geometry)

    def resizeEvent(self, e):
        self.update_lines_on_screen()
        super().resizeEvent(e)

    def set_active_file(self, fn):
        """ Active file will be overwritten by differ at end of each file complete. """
        filename = os.path.basename(fn)
        folder = os.path.dirname(fn)

        # Enter folder.
        idx = self.fs.index(folder)
        self.files.setRootIndex(idx)

        idx = self.fs.index(fn)
        self.files.setCurrentIndex(idx)

        self.setWindowTitle(filename)

    def update_lines_on_screen(self):
        self.lines_on_screen = self.editor.SendScintilla(QsciScintilla.SCI_LINESONSCREEN)

    def update_editor_caret(self, line, col):
        self.activateWindow()
        self.editor.setCursorPosition(line, col)

        first_visible_line = line - (self.lines_on_screen // 2)
        if first_visible_line < 0:
            first_visible_line = 0
        self.editor.setFirstVisibleLine(first_visible_line)
        # self.editor.SendScintilla(QsciScintilla.SCI_GOTOLINE, line)

    def differ_edit(self, line, col, source):
        self.editor.setText(''.join(source))
        self.update_editor_caret(line, col)

    def closeEvent(self, e):
        settings.setValue("Geometry/CodeViewer", self.saveGeometry())
        super().closeEvent(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.viewer = CodeViewer()
        self.viewer.show()

        vl = QVBoxLayout()

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
        filename, _ = QFileDialog.getOpenFileName()

        if filename:
            result = QMessageBox.warning(
                self, f"File will be overwritten!", f"Differ will overwrite '{filename}'"
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

