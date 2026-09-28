from datetime import datetime

from core.constants import IEC_FREQUENCIES, TEST_LEVELS_DB, LEVEL_TOLERANCE_DB

REQUIRED_DEVICE_FIELDS = {
    "brand": "Brand",
    "model": "Model / Type",
    "serial_number": "Serial number",
    "technician": "Technician"
}


def level_tolerance_text():
    """'+/-3 dB (125-4000 Hz), +/-5 dB (8000 Hz)' - groups frequencies sharing a tolerance."""
    groups = {}
    for f in IEC_FREQUENCIES:
        groups.setdefault(LEVEL_TOLERANCE_DB[f], []).append(f)
    parts = []
    for tol, freqs in groups.items():
        span = f"{freqs[0]} Hz" if len(freqs) == 1 else f"{freqs[0]}-{freqs[-1]} Hz"
        parts.append(f"+/-{tol:g} dB ({span})")
    return "within " + ", ".join(parts) + " of target"


def missing_device_fields(info):
    return [label for key, label in REQUIRED_DEVICE_FIELDS.items() if not info.get(key)]


def collect_report_data(engine):
    points = engine.get_calibration_points()
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_info": engine.database.get_device_info(),
        "calibration_points": [points[f] for f in IEC_FREQUENCIES if f in points],
        "uncalibrated": engine.uncalibrated_frequencies(),
        "results": engine.get_results(),
        "coverage": engine.coverage(),
        "missing": engine.missing_points(),
        "summary": engine.summary()
    }


def _identity(text):
    return text


def missing_points_text(missing, tr=_identity):
    """Group missing (frequency, level) pairs per frequency: '125 Hz: 20, 40 dB'."""
    by_freq = {}
    for f, level in missing:
        by_freq.setdefault(f, []).append(level)

    parts = []
    for f in IEC_FREQUENCIES:
        levels = by_freq.get(f)
        if not levels:
            continue
        if len(levels) == len(TEST_LEVELS_DB):
            parts.append(f"{f} Hz: " + tr("all levels"))
        else:
            parts.append(f"{f} Hz: " + ", ".join(f"{l:.0f}" for l in sorted(levels)) + " dB")
    return "; ".join(parts)


def report_warnings(data, tr=_identity):
    """Human-readable issues. `tr` translates for the UI; reports stay in English."""
    warnings = []

    missing_fields = missing_device_fields(data["device_info"])
    if missing_fields:
        warnings.append(tr("Device information incomplete: {fields}").format(
            fields=", ".join(tr(f) for f in missing_fields)))

    if data["uncalibrated"]:
        warnings.append(tr("Not calibrated: {list}").format(
            list=", ".join(f"{f} Hz" for f in data["uncalibrated"])))

    if data["missing"]:
        summary = data["summary"]
        warnings.append(tr("{missing} of {planned} test points not measured — {list}").format(
            missing=summary["missing"], planned=summary["planned"],
            list=missing_points_text(data["missing"], tr)))

    failed = data["summary"]["failed"]
    if failed:
        warnings.append(tr("{n} test point(s) FAIL — retake them or note the reason").format(n=failed))

    return warnings
