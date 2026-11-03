"""Helpers for the English / Persian (fa) versions of the site."""
from decimal import Decimal

from django.conf import settings
from django.utils.dateformat import time_format
from django.utils.formats import date_format
from django.utils.translation import get_language

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
JALALI_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                 "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


def is_persian():
    return (get_language() or "").startswith("fa")


def localized(obj, field):
    """The Persian text of `obj.<field>_fa` on Persian pages; the English
    `obj.<field>` otherwise, or when the Persian text has not been written yet."""
    if is_persian():
        value = getattr(obj, f"{field}_fa", "")
        if value:
            return value
    return getattr(obj, field)


def digits(value):
    """Persian digits (۰۱۲۳...) on Persian pages, unchanged otherwise."""
    text = str(value)
    return text.translate(FA_DIGITS) if is_persian() else text


def clock(t):
    """A time of day: '9:00 AM' in English, '۰۹:۰۰' (24-hour) in Persian."""
    if is_persian():
        return digits(time_format(t, "H:i"))
    return time_format(t, "g:i A")


def gregorian_to_jalali(gy, gm, gd):
    """Convert a Gregorian date to the Persian (Jalali / Solar Hijri) calendar."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
            + gd + g_d_m[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def short_date(d):
    """'Nov 30' in English, '۹ آذر' (Persian calendar) in Persian."""
    if is_persian():
        _, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
        return f"{digits(jd)} {JALALI_MONTHS[jm - 1]}"
    return date_format(d, "M j")


# Well-known currency names and how they are written in Persian
KNOWN_FA = {"toman": "تومان", "tomans": "تومان", "rial": "ریال", "rials": "ریال", "irr": "ریال"}


def _plain_number(value, thousands=",", decimal="."):
    """85000.00 -> '85,000'   7.99 -> '7.99'   (whole amounts lose the .00)"""
    number = Decimal(str(value))
    if number == number.to_integral_value():
        text = f"{int(number):,}"
    else:
        text = f"{number:,.2f}"
    return text.replace(",", "\0").replace(".", decimal).replace("\0", thousands)


def money(value):
    """A price with its currency.

    English:  $7.99  (symbol before, the default)  or  85,000 Toman  (CURRENCY_SYMBOL_BEFORE = False)
    Persian:  ۷٫۹۹ $  /  ۸۵٬۰۰۰ تومان  (the amount first, then the currency)
    """
    symbol = getattr(settings, "CURRENCY_SYMBOL", "$")
    if not is_persian():
        if getattr(settings, "CURRENCY_SYMBOL_BEFORE", True):
            return f"{symbol}{value}"
        return f"{_plain_number(value)} {symbol}"
    symbol_fa = getattr(settings, "CURRENCY_SYMBOL_FA", symbol)
    if symbol_fa == symbol:                              # no separate Persian symbol set: translate known names
        symbol_fa = KNOWN_FA.get(symbol.strip().lower(), symbol)
    return f"{digits(_plain_number(value, thousands='٬', decimal='٫'))} {symbol_fa}"
