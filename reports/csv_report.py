import csv

from core.constants import (
    IEC_FREQUENCIES,
    TEST_LEVELS_DB,
    REFERENCE_FREQUENCY,
    FREQUENCY_TOLERANCE_PCT,
    LEVEL_RESOLUTION_DB,
    THD_MAX_PCT
)
from reports.report_data import report_warnings, level_tolerance_text

DEVICE_LABELS = [
    ("brand", "Brand"),
    ("model", "Model / Type"),
    ("serial_number", "Serial number"),
    ("calibration_date", "Calibration date"),
    ("technician", "Technician"),
    ("notes", "Notes"),
    ("report_date", "Report date")
]

CALIBRATION_HEADER = [
    "Frequency (Hz)",
    "Measured (dB)",
    "Calibrator level (dB)",
    "Gain Correction (dB) = Calibrator - Measured",
    "Corrected (dB) = Measured + Gain Correction",
    "Status",
    "Calibrated at"
]

RESPONSE_HEADER = [
    "Frequency (Hz)",
    "Response correction (dB re 1 kHz)",
    "Total correction (dB) = Gain + Response"
]

RESULT_HEADER = [
    "Frequency (Hz)",
    "Measured Frequency (Hz)",
    "Frequency Status",
    "Level (dB)",
    "Raw Level (dB)",
    "Total Correction (dB)",
    "Calibrated Level (dB)",
    "Level Status",
    "THD (%)",
    "THD Status",
    "Overall",
    "Saved at"
]


def report_rows(data):
    """All report sections as rows; shared by the CSV and Excel exports."""
    rows = [["Audiometer Calibration Report"], ["Generated", data["generated"]], []]

    rows.append(["DEVICE INFORMATION"])
    for key, label in DEVICE_LABELS:
        rows.append([label, data["device_info"].get(key, "")])
    rows.append([])

    rows.append(["CRITERIA"])
    rows.append(["Frequency", f"within +/- {FREQUENCY_TOLERANCE_PCT:g} % of nominal"])
    rows.append(["Calibration", f"corrected level equals calibrator level ({LEVEL_RESOLUTION_DB:g} dB resolution)"])
    rows.append(["Level", level_tolerance_text()])
    rows.append(["THD", f"<= {THD_MAX_PCT:g} %"])
    rows.append([])

    rows.append([f"REFERENCE CALIBRATION ({REFERENCE_FREQUENCY} Hz, ACOUSTIC CALIBRATOR)"])
    rows.append(CALIBRATION_HEADER)
    p = data["reference_point"]
    if p is None:
        rows.append([REFERENCE_FREQUENCY, "", "", "", "", "NOT CALIBRATED", ""])
    else:
        rows.append([
            REFERENCE_FREQUENCY,
            f"{p['measured_db']:.2f}",
            f"{p['reference_db']:.2f}",
            f"{p['gain_correction_db']:+.2f}",
            f"{p['corrected_db']:.2f}",
            p["status"],
            p["timestamp"]
        ])
    rows.append([])

    rows.append(["CALIBRATION POINTS (MICROPHONE RESPONSE CORRECTION RELATIVE TO 1 kHz)"])
    rows.append(RESPONSE_HEADER)
    for r in data["response"]:
        rows.append([
            r["frequency"],
            f"{r['response_db']:+.2f}",
            "" if r["total_db"] is None else f"{r['total_db']:+.2f}"
        ])
    rows.append([])

    # Every planned point is listed; missing ones are left blank so gaps are visible.
    rows.append(["MEASUREMENT RESULTS"])
    rows.append(RESULT_HEADER)
    for f in IEC_FREQUENCIES:
        for level in TEST_LEVELS_DB:
            r = data["coverage"][(f, float(level))]
            if r is None:
                rows.append([f, "", "", level] + [""] * 6 + ["MISSING", ""])
                continue
            rows.append([
                r["frequency"],
                f"{r['measured_frequency']:.1f}",
                r["frequency_status"],
                f"{r['level_db']:.0f}",
                f"{r['measured_db']:.2f}",
                f"{r['gain_correction_db']:+.2f}",
                f"{r['calibrated_db']:.2f}",
                r["level_status"],
                f"{r['thd']:.2f}",
                r["thd_status"],
                r["overall_status"],
                r["timestamp"]
            ])
    rows.append([])

    summary = data["summary"]
    rows.append(["SUMMARY"])
    rows.append(["Planned points", summary["planned"]])
    rows.append(["Measured", summary["measured"]])
    rows.append(["PASS", summary["passed"]])
    rows.append(["FAIL", summary["failed"]])
    rows.append(["Missing", summary["missing"]])
    rows.append(["Overall", summary["overall"]])

    warnings = report_warnings(data)
    if warnings:
        rows.append([])
        rows.append(["WARNINGS"])
        rows.extend([w] for w in warnings)

    return rows


def export_csv(path, data):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(report_rows(data))


def export_xlsx(path, data):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Calibration Report"
    for row in report_rows(data):
        ws.append(row)
    wb.save(path)
