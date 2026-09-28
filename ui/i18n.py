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
    "Spectrum": "Spektrum",
    "Only confirms that a tone is coming in.": "Hanya untuk memastikan nada masuk.",
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
    "For each frequency: present a tone on the audiometer, read the true level on the reference "
    "sound level meter, type it as Reference, then press Calibrate.":
        "Untuk tiap frekuensi: bunyikan nada di audiometer, baca level sebenarnya di sound level "
        "meter referensi, isi sebagai Referensi, lalu tekan Kalibrasi.",
    "Calibrate one frequency": "Kalibrasi satu frekuensi",
    "Frequency": "Frekuensi",
    "Reference (dB)": "Referensi (dB)",
    "Measured (dB)": "Terukur (dB)",
    "Gain correction (dB)": "Koreksi gain (dB)",
    "Gain correction = Reference − Measured.\n"
    "It is added to every later reading at this frequency:\n"
    "Corrected = Measured + Gain correction.\n"
    "PASS when Corrected equals Reference ({res} dB resolution).":
        "Koreksi gain = Referensi − Terukur.\n"
        "Nilai ini ditambahkan ke setiap pembacaan berikutnya di frekuensi ini:\n"
        "Terkoreksi = Terukur + Koreksi gain.\n"
        "PASS jika Terkoreksi sama dengan Referensi (resolusi {res} dB).",
    "from reference meter": "dari meter referensi",
    "start live signal": "mulai sinyal live",
    "type measured dB": "ketik dB terukur",
    "Enter manually": "Isi manual",
    "Calibrate": "Kalibrasi",
    "Calibration points": "Titik kalibrasi",
    "Frequency (Hz)": "Frekuensi (Hz)",
    "Gain Correction (dB)": "Koreksi Gain (dB)",
    "Corrected (dB)": "Terkoreksi (dB)",
    "Status": "Status",
    "Recalibrate": "Kalibrasi Ulang",
    "Delete": "Hapus",
    "Live is off: press Start Live, or tick “Enter manually”.":
        "Live mati: tekan Mulai Live, atau centang “Isi manual”.",
    "Reference missing": "Referensi kosong",
    "Enter the level read from the reference sound level meter.":
        "Isi level yang terbaca di sound level meter referensi.",
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
    "Calibrated at {time}": "Dikalibrasi {time}",
    "Not calibrated yet: {list}": "Belum dikalibrasi: {list}",
    "All frequencies calibrated.": "Semua frekuensi sudah dikalibrasi.",

    # Measurement
    "Set the audiometer to the chosen frequency and level, present the tone, check the result "
    "per parameter, then press Save Result.\n"
    "Saving the same frequency + level again replaces the old result.":
        "Atur audiometer ke frekuensi dan level yang dipilih, bunyikan nada, cek hasil per "
        "parameter, lalu tekan Simpan Hasil.\n"
        "Menyimpan frekuensi + level yang sama akan mengganti hasil lama.",
    "Test point": "Titik uji",
    "Level": "Level",
    "Gain correction": "Koreksi gain",
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
    "{freq} Hz is not calibrated yet. Calibrate it first.":
        "{freq} Hz belum dikalibrasi. Kalibrasi dulu.",
    "Already saved. Saving again replaces it.": "Sudah tersimpan. Menyimpan lagi akan menggantinya.",
    "Live is off: press Start Live.": "Live mati: tekan Mulai Live.",
    "Not calibrated": "Belum dikalibrasi",
    "{freq} Hz is not calibrated yet. Go to Calibration now?":
        "{freq} Hz belum dikalibrasi. Buka tab Kalibrasi sekarang?",
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
    "{raw:.2f} dB (raw) {corr:+.2f} dB (gain correction) = {cal:.2f} dB  ·  saved {time}":
        "{raw:.2f} dB (mentah) {corr:+.2f} dB (koreksi gain) = {cal:.2f} dB  ·  disimpan {time}",

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
    "Delete all calibration points and measurement results":
        "Hapus semua titik kalibrasi dan hasil pengukuran",
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
    "This deletes ALL calibration points and measurement results.\n"
    "Device information is kept. Export the report first if you need it.\n\nContinue?":
        "Ini menghapus SEMUA titik kalibrasi dan hasil pengukuran.\n"
        "Informasi alat tetap disimpan. Ekspor laporan dulu jika masih diperlukan.\n\nLanjutkan?",

    # Report warnings
    "all levels": "semua level",
    "Device information incomplete: {fields}": "Informasi alat belum lengkap: {fields}",
    "Not calibrated: {list}": "Belum dikalibrasi: {list}",
    "{missing} of {planned} test points not measured — {list}":
        "{missing} dari {planned} titik uji belum diukur — {list}",
    "{n} test point(s) FAIL — retake them or note the reason":
        "{n} titik uji FAIL — ukur ulang atau catat alasannya",
}
