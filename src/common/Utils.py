
from datetime import datetime, timezone, timedelta
import math
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

    def convert_size(size_bytes):
        if size_bytes == 0:
            return "0B"

        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])