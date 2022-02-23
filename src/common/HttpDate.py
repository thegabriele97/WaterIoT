from datetime import datetime

class Httpdate:
    """Return a string representation of a date according to RFC 1123
    (HTTP/1.1).

    The supplied date must be in UTC.

    """

    def __init__(self, dt: datetime) -> None:
        self._dt = dt

    @staticmethod
    def from_timestamp(ts: int) -> str:
        return str(Httpdate(datetime.fromtimestamp(ts)))

    def __str__(self) -> str:
        dt = self._dt
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month - 1]

        return f"{weekday}, {dt.day:02} {month} {dt.year:02}, {dt.hour:02}:{dt.minute:02}:{dt.second:02} GMT"
