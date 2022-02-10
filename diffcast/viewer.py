import os

from PyQt6.Qsci import QsciLexerPython, QsciScintilla
from PyQt6.QtCore import QDir, QPoint, QSettings, QSize, Qt
from PyQt6.QtGui import QColor, QFileSystemModel, QFont, QFontMetrics
from PyQt6.QtWidgets import QHBoxLayout, QListView, QWidget

DISPLAY_MODES = {
    'custom': 'Custom Display',
    'fhd': 'Full HD (1920 x 1080)',
    'hd': 'HD (1280x720)',
    'sd': 'SD (720x576)',
    'frameless': 'Frameless',
}

settings = QSettings("Martin Fitzpatrick", "DiffCast")


class Editor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Don't take focus.
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

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

        # Background colors.
        lexer.setPaper(QColor('#1e1e1e'), 13)  # 13 Unclosed string

        lexer.setFont(font)

        self.setLexer(lexer)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, b'Courier')

        # Hide horizontal scrollbar.
        self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)

        # Tweak lexer.
        self.SendScintilla(
            QsciScintilla.SCI_SETKEYWORDS,
            0,
            b"False None True and as assert break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield",
        )
        self.SendScintilla(QsciScintilla.SCI_SETKEYWORDS, 1, b"self")

    def keyPressEvent(self, e):
        e.accept()

    def keyReleaseEvent(self, e):
        e.accept()


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

        self.set_active_file('~')
        self.set_display_mode('custom')

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

    def set_display_mode(self, display):
        handler = {
            'custom': self._display_custom,
            'fhd': self._display_fhd,
            'hd': self._display_hd,
            'sd': self._display_sd,
            'frameless': self._display_frameless,
        }.get(display)

        if handler:
            handler()
            self.show()

    def _display_custom(self):
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setMinimumSize(QSize(0, 0))
        self.setMaximumSize(QSize(16777215, 16777215))
        geometry = settings.value("Geometry/CodeViewer")
        if geometry:
            self.restoreGeometry(geometry)

    def _display_fhd(self):
        self.setFixedSize(1920, 1080)
        self._display_frameless()

    def _display_hd(self):
        self.setFixedSize(1280, 720)
        self._display_frameless()

    def _display_sd(self):
        self.setFixedSize(720, 576)
        self._display_frameless()

    def _display_frameless(self):
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.move(QPoint(0, 0))
