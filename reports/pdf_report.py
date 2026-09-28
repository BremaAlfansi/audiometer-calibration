from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)

from core.constants import (
    APP_NAME,
    ORG_NAME,
    IEC_FREQUENCIES,
    TEST_LEVELS_DB,
    FREQUENCY_TOLERANCE_PCT,
    LEVEL_RESOLUTION_DB,
    THD_MAX_PCT,
    PASS,
    FAIL
)
from reports.report_data import report_warnings, level_tolerance_text

PASS_BG = colors.HexColor("#d4f4dd")
PASS_FG = colors.HexColor("#1b5e20")
FAIL_BG = colors.HexColor("#fbd5d5")
FAIL_FG = colors.HexColor("#8b1a1a")
MISSING_BG = colors.HexColor("#eeeeee")
MISSING_FG = colors.HexColor("#777777")
HEADER_BG = colors.HexColor("#1f3a5f")


def status_style(col, row, status):
    if status == PASS:
        bg, fg = PASS_BG, PASS_FG
    elif status == FAIL:
        bg, fg = FAIL_BG, FAIL_FG
    else:
        bg, fg = MISSING_BG, MISSING_FG
    return [
        ("BACKGROUND", (col, row), (col, row), bg),
        ("TEXTCOLOR", (col, row), (col, row), fg),
        ("FONTNAME", (col, row), (col, row), "Helvetica-Bold"),
    ]


def base_table_style():
    return [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa5b1")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]


class PDFReport:
    @staticmethod
    def export_calibration_report(file_path, data):
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title="Audiometer Calibration Report"
        )
        styles = getSampleStyleSheet()
        small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, leading=10)
        h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=4)

        info = data["device_info"]
        summary = data["summary"]
        elements = []

        elements.append(Paragraph("Audiometer Calibration Report", styles["Title"]))
        elements.append(Paragraph(
            f"{escape(APP_NAME)} · {escape(ORG_NAME)} · Generated {data['generated']}", small
        ))
        elements.append(Spacer(1, 8))

        # Device information
        elements.append(Paragraph("Device Information", h2))
        device_rows = [
            ["Brand", info["brand"] or "—", "Calibration date", info["calibration_date"] or "—"],
            ["Model / Type", info["model"] or "—", "Technician", info["technician"] or "—"],
            ["Serial number", info["serial_number"] or "—", "", ""],
        ]
        device_table = Table(device_rows, colWidths=[30 * mm, 60 * mm, 32 * mm, 58 * mm])
        device_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#444444")),
            ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#444444")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(device_table)
        if info["notes"]:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(
                "<b>Notes:</b> " + escape(info["notes"]).replace("\n", "<br/>"), small
            ))

        # Result summary
        elements.append(Paragraph("Summary", h2))
        summary_rows = [
            ["Planned", "Measured", "PASS", "FAIL", "Missing", "Overall"],
            [summary["planned"], summary["measured"], summary["passed"],
             summary["failed"], summary["missing"], summary["overall"]]
        ]
        summary_table = Table(summary_rows, colWidths=[30 * mm] * 6)
        summary_style = base_table_style() + status_style(5, 1, summary["overall"])
        summary_table.setStyle(TableStyle(summary_style))
        elements.append(summary_table)

        warnings = report_warnings(data)
        if warnings:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(
                "<b>Attention:</b><br/>" + "<br/>".join("• " + escape(w) for w in warnings),
                ParagraphStyle("warn", parent=small, textColor=colors.HexColor("#8a5a00"),
                               backColor=colors.HexColor("#fff4d6"), borderPadding=4)
            ))

        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"<b>Criteria:</b> Calibration: corrected level equals reference ({LEVEL_RESOLUTION_DB:g} dB resolution). "
            f"Measurement: frequency within ±{FREQUENCY_TOLERANCE_PCT:g} % of nominal; "
            f"level {level_tolerance_text()}; "
            f"THD &lt;= {THD_MAX_PCT:g} %.", small
        ))

        # Calibration points
        cal_block = [Paragraph("Calibration: Gain Correction per Frequency", h2)]
        cal_rows = [["Frequency (Hz)", "Measured (dB)", "Reference (dB)",
                     "Gain Correction (dB)", "Corrected (dB)", "Status"]]
        cal_style = base_table_style()
        points = {p["frequency"]: p for p in data["calibration_points"]}
        for i, f in enumerate(IEC_FREQUENCIES, start=1):
            p = points.get(f)
            if p is None:
                cal_rows.append([f, "—", "—", "—", "—", "NOT CALIBRATED"])
                cal_style += status_style(5, i, None)
            else:
                cal_rows.append([
                    f, f"{p['measured_db']:.2f}", f"{p['reference_db']:.2f}",
                    f"{p['gain_correction_db']:+.2f}", f"{p['corrected_db']:.2f}", p["status"]
                ])
                cal_style += status_style(5, i, p["status"])
        cal_table = Table(cal_rows, colWidths=[26 * mm, 28 * mm, 28 * mm, 34 * mm, 28 * mm, 34 * mm])
        cal_table.setStyle(TableStyle(cal_style))
        cal_block.append(cal_table)
        cal_block.append(Spacer(1, 2))
        cal_block.append(Paragraph(
            "Gain Correction = Reference - Measured. Corrected = Measured + Gain Correction.", small
        ))
        elements.append(KeepTogether(cal_block))

        # Completeness grid
        grid_block = [Paragraph("Data Completeness (Frequency × Level)", h2)]
        grid_rows = [["Frequency"] + [f"{l} dB" for l in TEST_LEVELS_DB]]
        grid_style = base_table_style()
        for i, f in enumerate(IEC_FREQUENCIES, start=1):
            row = [f"{f} Hz"]
            for j, level in enumerate(TEST_LEVELS_DB, start=1):
                r = data["coverage"][(f, float(level))]
                status = None if r is None else r["overall_status"]
                row.append(status or "MISSING")
                grid_style += status_style(j, i, status)
            grid_rows.append(row)
        grid_table = Table(grid_rows)
        grid_table.setStyle(TableStyle(grid_style))
        grid_block.append(grid_table)
        elements.append(KeepTogether(grid_block))

        # Detailed results
        elements.append(Paragraph("Measurement Results", h2))
        result_rows = [[
            "Freq (Hz)", "Measured\nFreq (Hz)", "Freq",
            "Level (dB)", "Calibrated\nLevel (dB)", "Level",
            "THD (%)", "THD", "Overall"
        ]]
        result_style = base_table_style()
        results = sorted(data["results"], key=lambda r: (r["frequency"], r["level_db"]))
        for i, r in enumerate(results, start=1):
            result_rows.append([
                r["frequency"], f"{r['measured_frequency']:.1f}", r["frequency_status"],
                f"{r['level_db']:.0f}", f"{r['calibrated_db']:.1f}", r["level_status"],
                f"{r['thd']:.2f}", r["thd_status"], r["overall_status"]
            ])
            for col, key in [(2, "frequency_status"), (5, "level_status"),
                             (7, "thd_status"), (8, "overall_status")]:
                result_style += status_style(col, i, r[key])
        if not results:
            result_rows.append(["No measurement results"] + [""] * 8)
            result_style.append(("SPAN", (0, 1), (-1, 1)))
        result_table = Table(result_rows, repeatRows=1)
        result_table.setStyle(TableStyle(result_style))
        elements.append(result_table)

        # Sign-off
        technician = escape(info["technician"]) or "____________________"
        sign_rows = [
            ["Calibrated by", "Signature", "Date"],
            [technician, "", info["calibration_date"] or ""]
        ]
        sign_table = Table(sign_rows, colWidths=[60 * mm, 60 * mm, 50 * mm], rowHeights=[None, 18 * mm])
        sign_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa5b1")),
            ("VALIGN", (0, 1), (-1, 1), "BOTTOM"),
        ]))
        elements.append(Spacer(1, 12))
        elements.append(KeepTogether([sign_table]))

        doc.build(elements)
