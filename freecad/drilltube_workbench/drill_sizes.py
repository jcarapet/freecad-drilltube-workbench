"""Drill bit diameter lookups for the supported sizing systems.

Fractional sizes are computed directly (a "1/4 inch" fractional drill IS
4/16"=0.25", by definition — no lookup table needed). Number-gauge and
letter-gauge sizes are the long-standing ANSI wire-gauge drill chart values,
reproduced here for convenience: double-check them against a caliper or your
supplier's chart before relying on them for manufacturing.
"""

INCH_TO_MM = 25.4

SYSTEM_METRIC = "Metric"
SYSTEM_FRACTIONAL = "Fractional"
SYSTEM_NUMBER = "Number"
SYSTEM_LETTER = "Letter"
SYSTEM_CUSTOM = "Custom"

SYSTEMS = [SYSTEM_METRIC, SYSTEM_FRACTIONAL, SYSTEM_NUMBER, SYSTEM_LETTER, SYSTEM_CUSTOM]

# Reference only — verify against a caliper/chart before manufacturing.
NUMBER_GAUGE_SIZES_IN = {
    "#1": 0.2280, "#2": 0.2210, "#3": 0.2130, "#4": 0.2090, "#5": 0.2055,
    "#6": 0.2040, "#7": 0.2010, "#8": 0.1990, "#9": 0.1960, "#10": 0.1935,
    "#11": 0.1910, "#12": 0.1890, "#13": 0.1850, "#14": 0.1820, "#15": 0.1800,
    "#16": 0.1770, "#17": 0.1730, "#18": 0.1695, "#19": 0.1660, "#20": 0.1610,
    "#21": 0.1590, "#22": 0.1570, "#23": 0.1540, "#24": 0.1520, "#25": 0.1495,
    "#26": 0.1470, "#27": 0.1440, "#28": 0.1405, "#29": 0.1360, "#30": 0.1285,
    "#31": 0.1200, "#32": 0.1160, "#33": 0.1130, "#34": 0.1110, "#35": 0.1100,
    "#36": 0.1065, "#37": 0.1040, "#38": 0.1015, "#39": 0.0995, "#40": 0.0980,
    "#41": 0.0960, "#42": 0.0935, "#43": 0.0890, "#44": 0.0860, "#45": 0.0820,
    "#46": 0.0810, "#47": 0.0785, "#48": 0.0760, "#49": 0.0730, "#50": 0.0700,
    "#51": 0.0670, "#52": 0.0635, "#53": 0.0595, "#54": 0.0550, "#55": 0.0520,
    "#56": 0.0465, "#57": 0.0430, "#58": 0.0420, "#59": 0.0410, "#60": 0.0400,
    "#61": 0.0390, "#62": 0.0380, "#63": 0.0370, "#64": 0.0360, "#65": 0.0350,
    "#66": 0.0330, "#67": 0.0320, "#68": 0.0310, "#69": 0.0292, "#70": 0.0280,
    "#71": 0.0260, "#72": 0.0250, "#73": 0.0240, "#74": 0.0225, "#75": 0.0210,
    "#76": 0.0200, "#77": 0.0180, "#78": 0.0160, "#79": 0.0145, "#80": 0.0135,
}

# Reference only — verify against a caliper/chart before manufacturing.
LETTER_GAUGE_SIZES_IN = {
    "A": 0.234, "B": 0.238, "C": 0.242, "D": 0.246, "E": 0.250,
    "F": 0.257, "G": 0.261, "H": 0.266, "I": 0.272, "J": 0.277,
    "K": 0.281, "L": 0.290, "M": 0.295, "N": 0.302, "O": 0.316,
    "P": 0.323, "Q": 0.332, "R": 0.339, "S": 0.348, "T": 0.358,
    "U": 0.368, "V": 0.377, "W": 0.386, "X": 0.397, "Y": 0.404, "Z": 0.413,
}


def fractional_sizes_in():
    """Standard fractional drill sizes from 1/64" to 1", in 64ths.

    Returns an ordered dict-like list of (label, inches) pairs.
    """
    sizes = []
    for n in range(1, 65):
        label = _fraction_label(n, 64)
        sizes.append((label, n / 64.0))
    return sizes


def _fraction_label(numerator, denominator):
    while numerator % 2 == 0 and denominator % 2 == 0:
        numerator //= 2
        denominator //= 2
    if denominator == 1:
        return '{}"'.format(numerator)
    return '{}/{}"'.format(numerator, denominator)


def fractional_sizes_lookup_in():
    return {label: value for label, value in fractional_sizes_in()}


def resolve_diameter_mm(system, value):
    """Resolve a diameter in mm for the given sizing system.

    - Metric: `value` is already a diameter in mm (float).
    - Custom: same as Metric (free numeric mm entry).
    - Fractional: `value` is a fractional label, e.g. '1/4"', or a bare inch float.
    - Number: `value` is a label like '#30'.
    - Letter: `value` is a label like 'Q'.
    """
    if system in (SYSTEM_METRIC, SYSTEM_CUSTOM):
        return float(value)
    if system == SYSTEM_FRACTIONAL:
        table = fractional_sizes_lookup_in()
        inches = table[value] if isinstance(value, str) else float(value)
        return inches * INCH_TO_MM
    if system == SYSTEM_NUMBER:
        return NUMBER_GAUGE_SIZES_IN[value] * INCH_TO_MM
    if system == SYSTEM_LETTER:
        return LETTER_GAUGE_SIZES_IN[value] * INCH_TO_MM
    raise ValueError("Unknown sizing system: {}".format(system))
