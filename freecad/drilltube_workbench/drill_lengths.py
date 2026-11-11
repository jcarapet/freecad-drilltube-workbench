"""Stub/jobber/long drill length lookup, driven by an editable JSON table.

The bundled drill_lengths.json ships representative/approximate jobber-length
calibration points -- NOT a precise reproduction of any single manufacturer's
catalog. Treat the output as a modeling convenience and verify exact lengths
against your supplier's spec sheet before manufacturing. Edit the JSON file
to plug in your own reference data if you need better accuracy.
"""

import json
import os

CATEGORY_STUB = "Stub"
CATEGORY_JOBBER = "Jobber"
CATEGORY_LONG = "Long"
CATEGORIES = [CATEGORY_STUB, CATEGORY_JOBBER, CATEGORY_LONG]

_DATA_PATH = os.path.join(os.path.dirname(__file__), "drill_lengths.json")


def _load_table(path=_DATA_PATH):
    with open(path, "r") as f:
        data = json.load(f)
    points = sorted((float(d), float(L)) for d, L in data["jobber_length_mm"])
    return points, float(data["stub_ratio"]), float(data["long_ratio"])


_POINTS, _STUB_RATIO, _LONG_RATIO = _load_table()


def jobber_length_mm(diameter_mm, points=None):
    points = points or _POINTS
    if diameter_mm <= 0:
        raise ValueError("diameter_mm must be > 0")

    first_d, first_l = points[0]
    last_d, last_l = points[-1]

    if diameter_mm <= first_d:
        return diameter_mm / first_d * first_l

    if diameter_mm >= last_d:
        prev_d, prev_l = points[-2]
        slope = (last_l - prev_l) / (last_d - prev_d)
        return last_l + slope * (diameter_mm - last_d)

    for (d0, l0), (d1, l1) in zip(points, points[1:]):
        if d0 <= diameter_mm <= d1:
            t = (diameter_mm - d0) / (d1 - d0)
            return l0 + t * (l1 - l0)

    raise AssertionError("unreachable: diameter_mm not bracketed")


def length_for(diameter_mm, category):
    jobber = jobber_length_mm(diameter_mm)
    if category == CATEGORY_JOBBER:
        return jobber
    if category == CATEGORY_STUB:
        return jobber * _STUB_RATIO
    if category == CATEGORY_LONG:
        return jobber * _LONG_RATIO
    raise ValueError("Unknown length category: {}".format(category))
