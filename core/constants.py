APP_NAME = "AudiCalPro"
ORG_NAME = "Kelompok 212"

# Pure-tone test plan: every (frequency, level) pair is one verification point.
# The report flags any pair that has no saved result.
IEC_FREQUENCIES = [
    125,
    250,
    500,
    1000,
    2000,
    4000,
    8000
]

TEST_LEVELS_DB = [
    20,
    40,
    60,
    80,
    100
]

DEFAULT_SAMPLE_RATE = 48000
DEFAULT_BLOCK_SIZE = 4096

# Pass/fail criteria, one per parameter.
# Calibration has no tolerance: measured must equal reference once both are
# rounded to this resolution (0.1 dB = the precision shown on screen).
LEVEL_RESOLUTION_DB = 0.1
# Measurement level tolerance (IEC 60645-1 / ANSI S3.6):
# +/-3 dB up to 4 kHz, +/-5 dB above 4 kHz.
LEVEL_TOLERANCE_DB = {
    125: 3.0,
    250: 3.0,
    500: 3.0,
    1000: 3.0,
    2000: 3.0,
    4000: 3.0,
    8000: 5.0
}
# Frequency accuracy, percent of the nominal frequency (IEC 60645-1, type 1/2).
FREQUENCY_TOLERANCE_PCT = 1.0
# Maximum total harmonic distortion, percent (IEC 60645-1, air conduction).
THD_MAX_PCT = 2.5

# "Tone detected" needs all three: loud enough, above the sub-audio range,
# and a spectral peak standing clearly above the noise (a pure tone, not room noise).
MIN_SIGNAL_DB = -80.0
MIN_TONE_FREQUENCY_HZ = 50.0
MIN_TONE_PROMINENCE_DB = 30.0

PASS = "PASS"
FAIL = "FAIL"
