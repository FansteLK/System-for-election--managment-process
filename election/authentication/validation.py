"""Input validation for user registration."""

import calendar
import re

# Weights applied to digits 1-12 when computing the JMBG control digit.
JMBG_WEIGHTS = (7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def jmbg_control_digit(first_twelve):
    total = sum(int(d) * w for d, w in zip(first_twelve, JMBG_WEIGHTS, strict=False))
    m = 11 - total % 11
    # By definition, a remainder that maps to 10 or 11 gives a control digit of 0.
    return 0 if m > 9 else m


def is_valid_jmbg(jmbg):
    """Validate a Serbian JMBG in the DDMMYYYRRBBBK format.

    DD/MM must form a real calendar date, RR is a region in Serbia (70-99)
    and K must match the checksum of the first twelve digits.
    """
    if len(jmbg) != 13 or not jmbg.isdigit():
        return False
    day, month, year = int(jmbg[0:2]), int(jmbg[2:4]), int(jmbg[4:7])
    region = int(jmbg[7:9])
    # YYY holds the last three digits of the year: 9xx is 19xx, 0xx is 20xx.
    year += 1000 if year >= 900 else 2000
    if not 1 <= month <= 12:
        return False
    if not 1 <= day <= calendar.monthrange(year, month)[1]:
        return False
    if not 70 <= region <= 99:
        return False
    return jmbg_control_digit(jmbg[:12]) == int(jmbg[12])


def is_valid_password(password):
    return (
        8 <= len(password) <= 256
        and re.search(r"[a-z]", password) is not None
        and re.search(r"[A-Z]", password) is not None
        and re.search(r"[0-9]", password) is not None
    )
