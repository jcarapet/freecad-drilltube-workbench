"""Circle-packing-in-a-circle math: how wide must a tube be to bundle N
equal-diameter drill bits packed together in cross-section?

Ratios for small N are the known optimal "packing N unit circles inside the
smallest enclosing circle" constants (R/r, see e.g. Packomania). For N beyond
the table we fall back to the asymptotic hexagonal-packing approximation and
add a small safety margin, since the asymptotic formula underestimates the
enclosing radius for finite N.
"""

import math

# R/r ratios for N = 1..19 packed circles inside the smallest enclosing circle.
_ENCLOSING_RATIO = {
    1: 1.0,
    2: 2.0,
    3: 2.1547005384,
    4: 2.4142135624,
    5: 2.7013016167,
    6: 3.0,
    7: 3.0,
    8: 3.3047481028,
    9: 3.6130493287,
    10: 3.8130429016,
    11: 3.9238044002,
    12: 4.0291576822,
    13: 4.2360679915,
    14: 4.3284738491,
    15: 4.5214817951,
    16: 4.6152998149,
    17: 4.7912747674,
    18: 4.8631880077,
    19: 4.8631880077,
}

# Hexagonal packing density, used for the large-N asymptotic estimate.
_HEX_PACKING_DENSITY = math.pi / (2 * math.sqrt(3))
_LARGE_N_MARGIN = 1.08


def enclosing_diameter_ratio(count):
    """Ratio of (smallest enclosing circle diameter) / (single bit diameter)
    for `count` equal-diameter circles packed together."""
    if count < 1:
        raise ValueError("count must be >= 1")
    if count in _ENCLOSING_RATIO:
        return _ENCLOSING_RATIO[count]
    # Asymptotic estimate for large N, with a margin since the asymptote
    # underestimates the enclosing radius at finite N.
    ratio = 2 * math.sqrt(count / _HEX_PACKING_DENSITY) * _LARGE_N_MARGIN
    # Never return less than the largest tabulated ratio's growth trend.
    return max(ratio, _ENCLOSING_RATIO[19] * math.sqrt(count / 19))


def bore_diameter(bit_diameter, count, clearance=0.0):
    """Minimum bore diameter to bundle `count` bits of `bit_diameter`,
    each given `clearance` of extra slack."""
    if bit_diameter <= 0:
        raise ValueError("bit_diameter must be > 0")
    effective = bit_diameter + clearance
    return enclosing_diameter_ratio(count) * effective
