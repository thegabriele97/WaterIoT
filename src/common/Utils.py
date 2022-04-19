
from datetime import datetime, timezone, timedelta
from xmlrpc.client import DateTime
from zoneinfo import ZoneInfo

class Utils:

    def __init__(self) -> None:
        pass

    @staticmethod
    def get_user_datetime(timestamp: int, zone, format: str = '%Y-%m-%d %H:%M:%S') -> str:


        dt = datetime.fromtimestamp(timestamp)

        user_tz = ZoneInfo(zone)
        dt = dt.replace(tzinfo=user_tz)
        # print(f"zone = {zone}, dt = {dt}, dt.tzinfo = {dt.tzinfo}, dt.tzinfo.zone = {dt.tzinfo}, dt.tzinfo.utcoffset = {dt.tzinfo.utcoffset}")
        return dt.strftime(format)

    def get_user_dt_woffset(timestamp: int, zone, format: str = '%Y-%m-%d %H:%M:%S') -> str:

        dt = datetime.fromtimestamp(timestamp)

        user_tz = ZoneInfo(zone)
        dt = dt.replace(tzinfo=user_tz)
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S+%z")
        last = int(dt_str[dt_str.rfind('+'):])
        dt += timedelta(hours=int(last/100), minutes=int(last%100))
        return dt.strftime(format)
