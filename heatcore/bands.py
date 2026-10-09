"""Exceedance -> rest minutes per hour.

This is the project's OWN planning rule, inspired by NIOSH work/rest guidance
and Singapore's 10/15 min-per-hour structure. It is not a quoted standard.
Change it here only; everything else reads this table.
"""

# (upper bound of exceedance in deg C, rest minutes per hour, status)
# An hour falls in the first band whose upper bound is >= E.
BANDS: tuple[tuple[float, int, str], ...] = (
    (0.0, 0, "normal"),
    (1.0, 15, "caution"),
    (2.0, 30, "high"),
    (3.0, 45, "very_high"),
    (float("inf"), 60, "stop"),
)

STATUS_ORDER = {status: i for i, (_, _, status) in enumerate(BANDS)}
