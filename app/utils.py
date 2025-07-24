from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

async def get_admins() -> list:
    with open('json/admins.json') as admins:
        ADMINS = json.load(admins)
    return ADMINS

async def get_masters() -> list:
    with open('json/masters.json') as masters:
        MASTERS = json.load(masters)
    return MASTERS

async def get_channels() -> dict:
    with open('json/channels.json') as channels:
        CHANNELS = json.load(channels)
    return CHANNELS

async def update_channels(data: dict):
    with open("json/channels.json", "w") as file:
        json.dump(data, file, indent=4)

async def get_settings() -> dict:
    with open('json/settings.json') as settings:
        SETTINGS = json.load(settings)
    return SETTINGS

async def check_index(index: str) -> bool:
    if all(x in "0123456789" for x in index):
        return True
    return False

async def check_time(time: str) -> bool:
    if len(time) == 5 and time[2] == ":" and all(x in "0123456789" for x in time[:2]+time[3:]):
        first = int(time[:2])
        second = int(time[3:])
        if first < 24 and second < 60:
            return True
    return False

def get_posting_time(time_arr: list, post_index: int):
    MOSCOW_TZ = ZoneInfo("Europe/Moscow")
    cur = datetime.now(MOSCOW_TZ)
    arr = [datetime(year=cur.year, 
                    month=cur.month, 
                    day=cur.day, 
                    hour=int(n.split(":")[0]), 
                    minute=int(n.split(":")[1]),
                    second=cur.second,
                    microsecond=cur.microsecond,
                    tzinfo=MOSCOW_TZ) for n in time_arr]
    start_index = 0
    index = 0
    for j in arr:
        if cur < j:
            start_index = index
            break
        index += 1
    m = (post_index-((post_index//len(time_arr)))*len(time_arr))+start_index
    res_time = time_arr[m-((m//len(time_arr))*len(time_arr))]
    post_day = (cur + timedelta(days=post_index//len(time_arr)))
    return res_time, post_day.day, datetime.strptime(str(post_day.month), "%m").strftime("%b")