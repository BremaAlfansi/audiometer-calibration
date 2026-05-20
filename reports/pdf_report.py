from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime


class PDFReport:
    @staticmethod
    def export_calibration_report(
        file_path,
        calibration_results,
        summary
    ):
        doc = SimpleDocTemplate(file_path)
        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph(
                "AudiCalPro Calibration Certificate",
                styles["Title"]
            )
        )

        elements.append(
            Paragraph(
                "Kelompok 212",
                styles["Heading2"]
            )
        )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"]
            )
        )

        elements.append(Spacer(1, 20))

        table_data = [
            [
                "Frequency (Hz)",
                "Measured dB",
                "Reference dB",
                "Correction dB",
                "Status"
            ]
        ]

        for item in calibration_results:
            table_data.append([
                str(item["frequency"]),
                f"{item['measured_db']:.2f}",
                f"{item['reference_db']:.2f}",
                f"{item['correction_db']:.2f}",
                item["status"]
            ])

        table = Table(table_data)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("ALIGN", (0, 0), (-1, -1), "CENTER"),

            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

            ("GRID", (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        elements.append(Spacer(1, 30))

        summary_text = (
            f"Total Frequencies: {summary['total']}<br/>"
            f"PASS: {summary['passed']}<br/>"
            f"FAIL: {summary['failed']}<br/>"
            f"Overall Result: {summary['overall']}"
        )

        elements.append(
            Paragraph(
                summary_text,
                styles["Heading3"]
            )
        )

        elements.append(Spacer(1, 40))

        elements.append(
            Paragraph(
                "Operator Signature: ____________________",
                styles["Normal"]
            )
        )

        doc.build(elements)