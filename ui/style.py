from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QColor, QDoubleValidator
from PyQt6.QtWidgets import QTableWidgetItem, QLabel, QStyledItemDelegate

from core.constants import PASS, FAIL
from ui.i18n import tr

TEXT = "#f2f6fa"
TEXT_MUTED = "#c3ccd6"

PASS_BG = "#1f7a3d"
PASS_FG = "#ffffff"
FAIL_BG = "#a32b2b"
FAIL_FG = "#ffffff"
MISSING_BG = "#2b323b"
MISSING_FG = "#b4bec9"
WARN_BG = "#5a4412"
WARN_FG = "#ffe4a3"

# Inputs (things the user types/chooses) vs readings (values from the device).
INPUT_BORDER = "#4c9aff"
READING_BG = "#0f3036"
READING_FG = "#8ff5ea"

# UI scale: 1.0 is sized for ~900 px of usable screen height. main.py raises it on
# larger screens (e.g. 1.2 on a 1080p laptop) so text is not tiny when full screen.
SCALE = 1.0
# Narrow screens (e.g. 14" laptops at 125-150 % Windows scaling) get a slimmer live panel.
COMPACT = False


def set_scale(scale):
    global SCALE
    SCALE = scale


def configure_for_screen(width, height):
    """Pick scale and compact mode from the usable screen size (logical pixels)."""
    global COMPACT
    set_scale(max(1.0, min(1.4, height / 860)))
    COMPACT = width < 1500


def two_line_header(label):
    """'Corrected level (dB)' -> 'Corrected level\\n(dB)' so narrow columns do not clip."""
    return label.replace(" (", "\n(", 1)


def s(value):
    """Scale a pixel size."""
    return round(value * SCALE)


def px(value):
    return f"{s(value)}px"


def app_stylesheet():
    return f"""
QWidget {{ font-size: {px(15)}; color: {TEXT}; }}
QLabel#pageTitle {{ font-size: {px(22)}; font-weight: 700; }}
QLabel#sectionTitle {{ font-size: {px(16)}; font-weight: 600; }}
QLabel#caption {{ font-size: {px(13)}; color: {TEXT_MUTED}; }}
QLabel#info {{ color: {INPUT_BORDER}; font-size: {px(16)}; font-weight: 700; }}
QTabBar::tab {{ font-size: {px(15)}; padding: {px(8)} {px(16)}; }}
QTabBar::tab:selected {{ font-weight: 700; }}
QGroupBox {{ font-size: {px(16)}; font-weight: 600; border: 1px solid rgba(255,255,255,0.14);
            border-radius: 8px; margin-top: {px(12)}; padding: {px(12)} {px(10)} {px(10)} {px(10)}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QPushButton {{ background: #243746; color: {TEXT}; padding: {px(8)} {px(16)}; border-radius: 6px; }}
QPushButton:hover {{ background: #2e4658; }}
QPushButton#primary {{ background: #1f6feb; color: white; font-weight: 700; }}
QPushButton#primary:hover {{ background: #3b82f6; }}
QPushButton#danger {{ background: #8f2626; color: white; }}
QComboBox, QLineEdit, QDateEdit, QPlainTextEdit {{
    background: #0d1620; color: {TEXT}; padding: {px(6)} {px(8)}; min-height: {px(22)};
    border: 1px solid {INPUT_BORDER}; border-radius: 5px; }}
QLineEdit:read-only {{ background: {READING_BG}; color: {READING_FG};
                      border: 1px dashed #3a8a83; }}
QLabel#reading {{ background: {READING_BG}; color: {READING_FG};
                 border: 1px dashed #3a8a83; border-radius: 5px; padding: {px(6)} {px(8)};
                 font-family: Consolas, monospace; font-size: {px(17)}; font-weight: 600; }}
QTableWidget {{ background: #0b1220; color: {TEXT}; gridline-color: #253241; font-size: {px(15)}; }}
QHeaderView::section {{ background: #172231; color: {TEXT}; padding: {px(7)};
                       font-weight: 700; font-size: {px(14)}; border: none; }}
QToolTip {{ font-size: {px(14)}; color: #0b1220; background: #f2f6fa; padding: 6px; }}
"""


def status_colors(status):
    if status == PASS:
        return PASS_BG, PASS_FG
    if status == FAIL:
        return FAIL_BG, FAIL_FG
    return MISSING_BG, MISSING_FG


def status_item(status, text=None):
    item = QTableWidgetItem(text if text is not None else (status or "—"))
    bg, fg = status_colors(status)
    item.setBackground(QColor(bg))
    item.setForeground(QColor(fg))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    if status in (PASS, FAIL):
        font = item.font()
        font.setBold(True)
        item.setFont(font)
    return item


def style_status_label(label: QLabel, status, text=None):
    bg, fg = status_colors(status)
    label.setText(text if text is not None else (status or "—"))
    label.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:5px; padding:{px(4)} {px(12)}; font-weight:700;"
    )
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)


class CellBackgroundDelegate(QStyledItemDelegate):
    """Paints item backgrounds that the app stylesheet would otherwise hide."""

    def paint(self, painter, option, index):
        background = index.data(Qt.ItemDataRole.BackgroundRole)
        if background is not None:
            painter.fillRect(option.rect.adjusted(1, 1, -1, -1), background)
        super().paint(painter, option, index)


def setup_table(table):
    table.setItemDelegate(CellBackgroundDelegate(table))
    table.setWordWrap(False)
    table.verticalHeader().setDefaultSectionSize(s(36))


class NumericItem(QTableWidgetItem):
    """Table item that sorts by a numeric key instead of its text."""

    def __init__(self, value, text):
        super().__init__(text)
        self.sort_value = value
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        if isinstance(other, NumericItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


def db_validator():
    """Accepts plain decimal numbers with '.' regardless of the OS locale."""
    validator = QDoubleValidator(-200.0, 200.0, 2)
    validator.setNotation(QDoubleValidator.Notation.StandardNotation)
    validator.setLocale(QLocale.c())
    return validator


def banner(label: QLabel, kind, text):
    """Show a colored warning/info banner, or hide it when text is empty."""
    colors = {
        "warn": (WARN_BG, WARN_FG),
        "error": (FAIL_BG, FAIL_FG),
        "ok": (PASS_BG, PASS_FG),
    }
    bg, fg = colors[kind]
    label.setVisible(bool(text))
    label.setText(text)
    label.setWordWrap(True)
    label.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:5px; padding:{px(8)} {px(10)}; font-size:{px(14)};"
    )


def info_icon(tooltip):
    """Small ⓘ that keeps long explanations out of the layout until hovered."""
    label = QLabel("ⓘ")
    label.setObjectName("info")
    label.setToolTip(tooltip)
    label.setCursor(Qt.CursorShape.WhatsThisCursor)
    return label


def fit_table_height(table):
    """Size a table to exactly its rows, so short tables leave no empty body."""
    height = table.horizontalHeader().sizeHint().height() + 2 * table.frameWidth()
    height += sum(table.rowHeight(r) for r in range(table.rowCount()))
    table.setFixedHeight(height)


def section_title(text):
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def legend_label():
    label = QLabel(
        f"<span style='color:{INPUT_BORDER}'>■</span> {tr('Input')} &nbsp;&nbsp; "
        f"<span style='color:{READING_FG}'>■</span> {tr('Reading from device')}"
    )
    label.setObjectName("caption")
    return label
