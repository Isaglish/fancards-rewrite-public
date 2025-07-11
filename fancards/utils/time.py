import re
import datetime


__all__ = (
    "str_to_timedelta",
    "seconds_to_human"
)


def str_to_timedelta(string: str) -> datetime.timedelta:
    """A helper function that converts ``string`` to :class:`datetime.timedelta`.

    Example::

        ╔═══════════════════════╦══════════════════════════════════════════════╗
        ║        string         ║                   result                     ║
        ╠═══════════════════════╬══════════════════════════════════════════════╣
        ║ "1 hour 30 minutes"   ║   datetime.timedelta(seconds=5400)           ║
        ╠═══════════════════════╬══════════════════════════════════════════════╣
        ║ "6h45m"               ║   datetime.timedelta(seconds=24300)          ║
        ╠═══════════════════════╬══════════════════════════════════════════════╣
        ║ "3 weeks and 40 days" ║   datetime.timedelta(days=61)                ║
        ╠═══════════════════════╬══════════════════════════════════════════════╣
        ║ "3days 59mins"        ║   datetime.timedelta(days=3, seconds=3540)   ║
        ╠═══════════════════════╬══════════════════════════════════════════════╣
        ║ "3.5d"                ║   datetime.timedelta(days=3, seconds=43200)  ║
        ╚═══════════════════════╩══════════════════════════════════════════════╝
    
    Parameters
    ----------
    string: :class:`str`
        The string to convert.

        Supported units::

            Weeks: "weeks", "wks" and "w";
            Days: "days" and "d"
            Hours: "hours", "hrs" and "h"
            Minutes: "minutes", "mins" and "m"
            Seconds: "seconds", "secs" and "s"
    
    Raises
    ------
    ValueError
        ``string`` could not be converted to :class:`datetime.timedelta`
    
    Returns
    -------
    :class:`datetime.timedelta`
        The converted string.
    """
    pattern = re.compile(
        r"""
        (?:(?P<weeks>\d+(\.\d+)*)\s*(weeks?|wks?|w))?
        (?:(?P<days>\d+(\.\d+)*)\s*(days?|d))?
        (?:(?P<hours>\d+(\.\d+)*)\s*(hours?|hrs?|h))?
        (?:(?P<minutes>\d+(\.\d+)*)\s*(minutes?|mins?|m))?
        (?:(?P<seconds>\d+(\.\d+)*)\s*(seconds?|secs?|s))?
        """,
        flags=re.VERBOSE | re.IGNORECASE
    )
    matches = pattern.finditer(string)

    if not matches:
        raise ValueError("String could not be converted.")
    
    parameters: dict[str, float] = {}
    for match in matches:
        if not match:
            continue

        for unit, value in match.groupdict().items():
            if value is not None:
                parameters[unit] = float(value)
    
    return datetime.timedelta(**parameters)


def seconds_to_human(seconds: float) -> str:
    """A helper function that converts ``seconds`` into a human-readable string.
    
    Parameters
    ----------
    seconds: :class:`float`
        The seconds to convert.
    
    Returns
    -------
    :class:`str`
        The human-readable representation of ``seconds``.
    """
    units = {
        "year": 31536000,
        "month": 2592000,
        "week": 604800,
        "day": 86400,
        "hour": 3600,
        "minute": 60,
        "second": 1,
    }
    seconds = int(seconds)

    human_parts: list[str] = []
    for unit_name, unit_seconds in units.items():
        if seconds >= unit_seconds:
            count, seconds = divmod(seconds, unit_seconds)
            human_parts.append(f"{count} {unit_name}{'s' if count != 1 else ''}")
            
    if not human_parts:
        human_parts.append("0 seconds")

    return " and ".join(", ".join(human_parts).rsplit(", ", 1))
