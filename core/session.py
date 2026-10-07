"""Save / open a whole calibration session as one file (*.audical, JSON inside).

A session holds device info, the 1 kHz calibration, the microphone response
corrections and every measurement result, so unfinished work can be stored,
moved to another PC and continued later.
"""

import json
from datetime import datetime

SESSION_EXTENSION = ".audical"
SESSION_FORMAT = "AudiCalPro session"
SESSION_VERSION = 1


class SessionError(Exception):
    pass


def save_session(path, engine):
    db = engine.database
    data = {
        "format": SESSION_FORMAT,
        "version": SESSION_VERSION,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_info": db.get_device_info(),
        "reference_point": engine.get_reference_point(),
        "response_corrections": {str(f): c for f, c in engine.get_response_corrections().items()},
        # Row ids are internal to the database; the file only needs the measured data.
        "results": [{k: v for k, v in r.items() if k != "id"} for r in engine.get_results()],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_session(path, engine):
    """Replace all current data with the session in `path`."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise SessionError(str(e)) from e

    if not isinstance(data, dict) or data.get("format") != SESSION_FORMAT:
        raise SessionError("Not an AudiCalPro session file.")
    if data.get("version", 0) > SESSION_VERSION:
        raise SessionError("This session was saved by a newer version of the software.")

    db = engine.database
    db.clear_calibration_points()
    db.clear_verification_results()
    db.clear_response_corrections()

    db.save_device_info({k: data.get("device_info", {}).get(k, "") for k in db.DEVICE_FIELDS})

    point = data.get("reference_point")
    if point:
        db.upsert_calibration_point(point)

    for frequency, correction in data.get("response_corrections", {}).items():
        engine.set_response_correction(int(frequency), float(correction))

    for result in data.get("results", []):
        db.upsert_verification_result(result)

    return data.get("saved_at", "")
