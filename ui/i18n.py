"""UI translation. English is the source text; other languages map from it.

Use tr("English text") for every user-visible string. Templates with
placeholders are translated first, then formatted:
    tr("{n} results deleted").format(n=3)
"""

from PyQt6.QtCore import QSettings

LANGUAGES = {
    "en": "English",
    "id": "Bahasa Indonesia",
}

_settings = QSettings("Kelompok212", "AudiCalPro")
_language = _settings.value("language", "en")
if _language not in LANGUAGES:
    _language = "en"


def get_language():
    return _language


def set_language(language):
    global _language
    _language = language if language in LANGUAGES else "en"
    _settings.setValue("language", _language)


def tr(text):
    if _language == "id":
        return ID.get(text, text)
    return text


ID = {
    # Navigation / titles
    "Device Info": "Info Alat",
    "Device Information": "Informasi Alat",
    "Calibration": "Kalibrasi",
    "Measurement": "Pengukuran",
    "Report": "Laporan",
    "Live Signal": "Sinyal Live",
    "Input": "Input",
    "Reading from device": "Hasil baca alat",

    # Live panel
    "Input device (measurement microphone / coupler)": "Perangkat input (mikrofon ukur / coupler)",
    "Refresh device list": "Muat ulang daftar perangkat",
    "Start Live": "Mulai Live",
    "Stop Live": "Stop Live",
    "Level (raw)": "Level (mentah)",
    "Uncorrected input level (dBFS).": "Level input sebelum koreksi (dBFS).",
    "Live is off": "Live mati",
    "Waiting for signal…": "Menunggu sinyal…",
    "Octave bands (dB, calibrated)": "Pita oktaf (dB, terkalibrasi)",
    "Octave bands (dBFS, raw)": "Pita oktaf (dBFS, mentah)",
    "Level per 1-octave band, 125 Hz – 8 kHz.\n"
    "Before calibration: raw dBFS. After calibration: calibrated dB "
    "(raw + total correction of each band).\n"
    "Dashed frame = band of the selected test frequency.\n"
    "The strongest band lights up; it turns red when it is not the framed band.":
        "Level per pita 1-oktaf, 125 Hz – 8 kHz.\n"
        "Sebelum kalibrasi: dBFS mentah. Setelah kalibrasi: dB terkalibrasi "
        "(mentah + koreksi total tiap pita).\n"
        "Bingkai putus-putus = pita frekuensi uji yang dipilih.\n"
        "Pita terkuat menyala; berubah merah jika bukan pita yang dibingkai.",
    "No input device found. Connect a microphone and press ↻.":
        "Perangkat input tidak ditemukan. Sambungkan mikrofon lalu tekan ↻.",
    "Select an input device first.": "Pilih perangkat input dulu.",
    "Signal detected": "Sinyal terdeteksi",
    "No tone detected. Check the audiometer output.": "Nada tidak terdeteksi. Periksa output audiometer.",
    "Could not list audio devices: {error}": "Gagal membaca perangkat audio: {error}",
    "Live stopped: {error}": "Live berhenti: {error}",

    # Device info
    "Audiometer under test": "Audiometer yang dikalibrasi",
    "Room conditions, coupler / transducer, remarks": "Kondisi ruang, coupler / transduser, catatan",
    "Brand": "Merek",
    "Model / Type": "Model / Tipe",
    "Serial number": "Nomor seri",
    "Calibration date": "Tanggal kalibrasi",
    "Technician": "Pelaksana kalibrasi",
    "Notes": "Catatan",
    "Save": "Simpan",
    "required for the report": "wajib untuk laporan",
    "Device information saved.": "Informasi alat tersimpan.",
    "Saved, but still missing: {fields}": "Tersimpan, tapi masih kosong: {fields}",

    # Calibration
    "1. Put the acoustic calibrator on the microphone (1 kHz).\n"
    "2. Enter the calibrator level (usually 94 dB or 114 dB) and press Calibrate.\n"
    "3. If the microphone response is not flat, enter its correction per frequency "
    "in the Calibration points table.":
        "1. Pasang kalibrator akustik pada mikrofon (1 kHz).\n"
        "2. Isi level kalibrator (biasanya 94 dB atau 114 dB) lalu tekan Kalibrasi.\n"
        "3. Jika respon mikrofon tidak flat, isi koreksinya per frekuensi "
        "di tabel Titik kalibrasi.",
    "Reference calibration": "Kalibrasi referensi",
    "Fixed: acoustic calibrators work at 1 kHz.": "Tetap: kalibrator akustik bekerja di 1 kHz.",
    "Frequency": "Frekuensi",
    "Calibrator level (dB)": "Level kalibrator (dB)",
    "e.g. 94 or 114": "mis. 94 atau 114",
    "Use {level:g} dB": "Pakai {level:g} dB",
    "Measured (dB)": "Terukur (dB)",
    "Gain correction (dB)": "Koreksi gain (dB)",
    "Gain correction = Calibrator level − Measured.\n"
    "PASS when Measured + Gain correction equals the calibrator level ({res} dB resolution).":
        "Koreksi gain = Level kalibrator − Terukur.\n"
        "PASS jika Terukur + Koreksi gain sama dengan level kalibrator (resolusi {res} dB).",
    "start live signal": "mulai sinyal live",
    "type measured dB": "ketik dB terukur",
    "Enter manually": "Isi manual",
    "Calibrate": "Kalibrasi",
    "Calibration points": "Titik kalibrasi",
    "Microphone frequency-response correction, in dB relative to 1 kHz.\n"
    "Take it from the microphone's calibration certificate. Leave 0.00 if the response is flat.\n"
    "Example: the microphone reads 1.5 dB too low at 8000 Hz → enter +1.5.\n"
    "Total correction = Gain correction + Response correction.":
        "Koreksi respon frekuensi mikrofon, dalam dB relatif terhadap 1 kHz.\n"
        "Ambil dari sertifikat kalibrasi mikrofon. Biarkan 0.00 jika responnya flat.\n"
        "Contoh: mikrofon membaca 1.5 dB terlalu rendah di 8000 Hz → isi +1.5.\n"
        "Koreksi total = Koreksi gain + Koreksi respon.",
    "Double-click a value to edit it.": "Klik dua kali nilai untuk mengubahnya.",
    "Double-click to edit": "Klik dua kali untuk mengubah",
    "Frequency (Hz)": "Frekuensi (Hz)",
    "Response correction (dB)": "Koreksi respon (dB)",
    "Total correction (dB)": "Koreksi total (dB)",
    "reference": "referensi",
    "Status": "Status",
    "Delete": "Hapus",
    "Live is off: press Start Live, or tick “Enter manually”.":
        "Live mati: tekan Mulai Live, atau centang “Isi manual”.",
    "Calibrator level missing": "Level kalibrator kosong",
    "Enter the calibrator level, e.g. 94 dB or 114 dB.": "Isi level kalibrator, mis. 94 dB atau 114 dB.",
    "Invalid value": "Nilai tidak valid",
    "Enter a number in dB between −30 and +30, e.g. 1.5 or -0.8.":
        "Isi angka dalam dB antara −30 dan +30, mis. 1.5 atau -0.8.",
    "Measured level missing": "Level terukur kosong",
    "Start Live (left panel), or tick “Enter manually” and type it.":
        "Mulai Live (panel kiri), atau centang “Isi manual” lalu ketik nilainya.",
    "No signal": "Tidak ada sinyal",
    "No tone detected. Check the audiometer output and the microphone.":
        "Nada tidak terdeteksi. Periksa output audiometer dan mikrofon.",
    "Frequency mismatch": "Frekuensi tidak cocok",
    "Selected {selected} Hz, but the detected tone is {detected:.1f} Hz.\n\nContinue anyway?":
        "Dipilih {selected} Hz, tapi nada yang terdeteksi {detected:.1f} Hz.\n\nTetap lanjutkan?",
    "Replace calibration": "Ganti kalibrasi",
    "{freq} Hz is already calibrated. Replace it?": "{freq} Hz sudah dikalibrasi. Ganti?",
    "Select a row": "Pilih baris",
    "Select a row in the table first.": "Pilih baris di tabel dulu.",
    "Delete calibration": "Hapus kalibrasi",
    "Delete the calibration for {freq} Hz?": "Hapus kalibrasi untuk {freq} Hz?",
    "NOT CALIBRATED": "BELUM DIKALIBRASI",
    "Not calibrated yet. Calibrate at 1 kHz with the calibrator.":
        "Belum dikalibrasi. Lakukan kalibrasi di 1 kHz dengan kalibrator.",
    "{ref:.2f} dB calibrator · measured {meas:.2f} dB · gain correction {gain:+.2f} dB · {time}":
        "kalibrator {ref:.2f} dB · terukur {meas:.2f} dB · koreksi gain {gain:+.2f} dB · {time}",

    # Measurement
    "Set the audiometer to the chosen frequency and level, present the tone, check the result "
    "per parameter, then press Save Result.\n"
    "Saving the same frequency + level again replaces the old result.":
        "Atur audiometer ke frekuensi dan level yang dipilih, bunyikan nada, cek hasil per "
        "parameter, lalu tekan Simpan Hasil.\n"
        "Menyimpan frekuensi + level yang sama akan mengganti hasil lama.",
    "Test point": "Titik uji",
    "Level": "Level",
    "Save Result": "Simpan Hasil",
    "Live result": "Hasil live",
    "Saved results": "Hasil tersimpan",
    "Sort": "Urutkan",
    "Frequency, then Level": "Frekuensi, lalu Level",
    "Level, then Frequency": "Level, lalu Frekuensi",
    "Failures first": "FAIL dulu",
    "Newest first": "Terbaru dulu",
    "Level (dB)": "Level (dB)",
    "Measured freq (Hz)": "Frek. terukur (Hz)",
    "Corrected level (dB)": "Level terkoreksi (dB)",
    "Overall": "Keseluruhan",
    "Details": "Detail",
    "Retake": "Ukur Ulang",
    "Already saved. Saving again replaces it.": "Sudah tersimpan. Menyimpan lagi akan menggantinya.",
    "Live is off: press Start Live.": "Live mati: tekan Mulai Live.",
    "Not calibrated": "Belum dikalibrasi",
    "Not calibrated yet. Go to Calibration now?": "Belum dikalibrasi. Buka tab Kalibrasi sekarang?",
    "No live reading": "Belum ada pembacaan live",
    "Start Live (left panel) and present the tone before saving.":
        "Mulai Live (panel kiri) dan bunyikan nada sebelum menyimpan.",
    "Replace result": "Ganti hasil",
    "{freq} Hz / {level:.0f} dB is already saved. Replace it?":
        "{freq} Hz / {level:.0f} dB sudah tersimpan. Ganti?",
    "Saved at {time}": "Disimpan {time}",
    "Delete results": "Hapus hasil",
    "Delete {n} result(s)?": "Hapus {n} hasil?",

    # Result detail
    "Parameter": "Parameter",
    "Target": "Target",
    "Result": "Hasil",
    "Criterion": "Kriteria",
    "Close": "Tutup",
    "{raw:.2f} dB (raw) {corr:+.2f} dB (total correction) = {cal:.2f} dB  ·  saved {time}":
        "{raw:.2f} dB (mentah) {corr:+.2f} dB (koreksi total) = {cal:.2f} dB  ·  disimpan {time}",

    # Report
    "Measured": "Terukur",
    "Missing": "Kosong",
    "Data completeness": "Kelengkapan data",
    "Each cell is one test point (frequency × level).\n"
    "— = not measured yet. Double-click a cell to see details, retake or delete it.":
        "Tiap sel adalah satu titik uji (frekuensi × level).\n"
        "— = belum diukur. Klik dua kali sel untuk melihat detail, mengukur ulang, atau menghapus.",
    "Data complete. Ready to export.": "Data lengkap. Siap diekspor.",
    "Export PDF": "Ekspor PDF",
    "Export CSV": "Ekspor CSV",
    "Export Excel": "Ekspor Excel",
    "New Calibration": "Kalibrasi Baru",
    "Delete the calibration and all measurement results":
        "Hapus kalibrasi dan semua hasil pengukuran",
    "Report date": "Tanggal laporan",
    "Date printed at the signature and used in the file name":
        "Tanggal yang dicetak di bagian tanda tangan dan dipakai di nama file",
    "Not measured": "Belum diukur",
    "{freq} Hz / {level:.0f} dB has no result yet. Measure it now?":
        "{freq} Hz / {level:.0f} dB belum ada hasil. Ukur sekarang?",
    "Report is incomplete": "Laporan belum lengkap",
    "Export anyway? The issues will be listed in the report.":
        "Tetap ekspor? Kekurangannya akan dicantumkan di laporan.",
    "Nothing to export": "Tidak ada yang bisa diekspor",
    "There is no calibration or measurement data yet.": "Belum ada data kalibrasi atau pengukuran.",
    "Save report": "Simpan laporan",
    "Export failed": "Ekspor gagal",
    "Could not write the file:": "Gagal menulis file:",
    "Exported": "Berhasil diekspor",
    "Saved to:": "Disimpan di:",
    "This deletes the calibration and ALL measurement results.\n"
    "Device information and microphone response corrections are kept.\n"
    "Export the report or save the session first if you need it.\n\nContinue?":
        "Ini menghapus kalibrasi dan SEMUA hasil pengukuran.\n"
        "Informasi alat dan koreksi respon mikrofon tetap disimpan.\n"
        "Ekspor laporan atau simpan sesi dulu jika masih diperlukan.\n\nLanjutkan?",

    # Session files
    "Load Session": "Muat Sesi",
    "Save Session": "Simpan Sesi",
    "AudiCalPro session": "Sesi AudiCalPro",
    "Continue a session saved earlier (*{ext})": "Lanjutkan sesi yang disimpan sebelumnya (*{ext})",
    "Save all current work to a file to continue later (*{ext})":
        "Simpan semua pekerjaan ke file untuk dilanjutkan nanti (*{ext})",
    "Loading a session replaces the current device info, calibration and results.\n"
    "Save the current session first if you still need it.\n\nContinue?":
        "Memuat sesi akan mengganti info alat, kalibrasi, dan hasil yang sekarang.\n"
        "Simpan sesi yang sekarang dulu jika masih diperlukan.\n\nLanjutkan?",
    "Session saved": "Sesi tersimpan",
    "Save failed": "Gagal menyimpan",
    "Cannot load session": "Sesi tidak bisa dimuat",
    "Session loaded": "Sesi dimuat",
    "Session saved at {time} is loaded.": "Sesi yang disimpan pada {time} sudah dimuat.",

    # Report warnings
    "all levels": "semua level",
    "Device information incomplete: {fields}": "Informasi alat belum lengkap: {fields}",
    "Not calibrated: no 1 kHz calibrator measurement": "Belum dikalibrasi: belum ada pengukuran kalibrator 1 kHz",
    "{missing} of {planned} test points not measured — {list}":
        "{missing} dari {planned} titik uji belum diukur — {list}",
    "{n} test point(s) FAIL — retake them or note the reason":
        "{n} titik uji FAIL — ukur ulang atau catat alasannya",
}
