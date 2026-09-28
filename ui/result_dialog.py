from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt

from core.constants import FREQUENCY_TOLERANCE_PCT, THD_MAX_PCT, LEVEL_TOLERANCE_DB
from ui.i18n import tr
from ui.style import status_item, style_status_label, setup_table, s


def parameter_names():
    return [tr("Frequency"), tr("Level"), "THD"]


def parameter_rows(result):
    """Per-parameter breakdown: Frequency, Level, THD (same order everywhere)."""
    names = parameter_names()
    return [
        (
            names[0],
            f"{result['frequency']} Hz",
            f"{result['measured_frequency']:.1f} Hz",
            f"± {FREQUENCY_TOLERANCE_PCT:g} %",
            result["frequency_status"]
        ),
        (
            names[1],
            f"{result['level_db']:.1f} dB",
            f"{result['calibrated_db']:.1f} dB",
            f"± {LEVEL_TOLERANCE_DB[result['frequency']]:g} dB",
            result["level_status"]
        ),
        (
            names[2],
            "—",
            f"{result['thd']:.2f} %",
            f"≤ {THD_MAX_PCT:g} %",
            result["thd_status"]
        )
    ]


def make_parameter_table():
    columns = [tr("Parameter"), tr("Target"), tr("Result"), tr("Criterion"), tr("Status")]
    table = QTableWidget(3, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    row_height = s(36)
    table.horizontalHeader().setFixedHeight(row_height)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    setup_table(table)
    for r in range(3):
        table.setRowHeight(r, row_height)
    table.setFixedHeight(row_height * 4 + 4)
    return table


def fill_parameter_table(table, result):
    if result is None:
        for r, name in enumerate(parameter_names()):
            table.setItem(r, 0, QTableWidgetItem(name))
            for c in range(1, 5):
                table.setItem(r, c, status_item(None, "—"))
        return

    for r, (name, target, value, criterion, status) in enumerate(parameter_rows(result)):
        table.setItem(r, 0, QTableWidgetItem(name))
        for c, text in enumerate([target, value, criterion], start=1):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(r, c, item)
        table.setItem(r, 4, status_item(status))


class ResultDetailDialog(QDialog):
    """Small pop-up with the full breakdown of one saved test point."""

    RETAKE = 2
    DELETE = 3

    def __init__(self, result, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"{result['frequency']} Hz · {result['level_db']:.0f} dB")
        self.setMinimumWidth(s(640))

        root = QVBoxLayout(self)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(f"{result['frequency']} Hz · {result['level_db']:.0f} dB")
        title.setObjectName("pageTitle")
        overall = QLabel()
        style_status_label(overall, result["overall_status"])
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(overall)
        root.addLayout(header)

        table = make_parameter_table()
        fill_parameter_table(table, result)
        root.addWidget(table)

        info = QLabel(tr("{raw:.2f} dB (raw) {corr:+.2f} dB (gain correction) = {cal:.2f} dB  ·  saved {time}").format(
            raw=result["measured_db"],
            corr=result["gain_correction_db"],
            cal=result["calibrated_db"],
            time=result["timestamp"]
        ))
        info.setObjectName("caption")
        root.addWidget(info)

        buttons = QHBoxLayout()
        retake = QPushButton(tr("Retake"))
        retake.setObjectName("primary")
        retake.clicked.connect(lambda: self.done(self.RETAKE))
        delete = QPushButton(tr("Delete"))
        delete.setObjectName("danger")
        delete.clicked.connect(lambda: self.done(self.DELETE))
        close = QPushButton(tr("Close"))
        close.clicked.connect(self.reject)
        buttons.addWidget(retake)
        buttons.addWidget(delete)
        buttons.addStretch(1)
        buttons.addWidget(close)
        root.addLayout(buttons)
