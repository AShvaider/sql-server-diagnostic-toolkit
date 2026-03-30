"""Thresholds for classifying findings. Tune for your environment."""

# Index fragmentation (avg_fragmentation_in_percent)
FRAG_CRITICAL = 30.0
FRAG_WARNING = 10.0

# Page Life Expectancy (seconds)
PLE_CRITICAL = 300
PLE_WARNING = 1000

# Virtual Log File count
VLF_CRITICAL = 10_000
VLF_WARNING = 1_000

# Hours since last full backup
BACKUP_FULL_CRITICAL_H = 7 * 24
BACKUP_FULL_WARNING_H = 24

# Hours since last log backup (for FULL recovery model)
BACKUP_LOG_CRITICAL_H = 24
BACKUP_LOG_WARNING_H = 6

# Missing index improvement_measure
MISSING_INDEX_CRITICAL = 1_000_000
MISSING_INDEX_WARNING = 50_000

# Buffer cache hit ratio (percent)
BCHR_CRITICAL = 90.0
BCHR_WARNING = 95.0

# Average CPU time (ms) for "top slow queries"
SLOW_QUERY_CRITICAL_MS = 5_000
SLOW_QUERY_WARNING_MS = 1_000

# Unused index write ratio threshold
UNUSED_INDEX_WRITE_MIN = 100


def level_from_frag(pct: float) -> str:
    if pct >= FRAG_CRITICAL:
        return "rebuild"
    if pct >= FRAG_WARNING:
        return "reorganize"
    return "skip"
