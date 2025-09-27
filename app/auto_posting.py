from zoneinfo import ZoneInfo
from datetime import datetime, time
import asyncio
from app.utils import get_channels, update_channels
from app.init_bot import bot
from app.forms import Channel

import logging
logger = logging.getLogger(__name__)

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

async def publish_post(key: str):
    channels = await get_channels()
    channel = Channel(key, channels[key]["id"])
    if await channel.check_perms():
        posts = await channel.posts
        post = posts[0]
        chat_info = await channel.info
        if post["caption"] != None:
            await bot.send_photo(chat_id=channel.id, 
                                photo=post["id"], 
                                caption=f"{post['caption']}\n\n<a href='t.me/{chat_info.username}'>📎 {chat_info.full_name}</a>")
        else:
            await bot.send_photo(chat_id=channel.id, 
                                photo=post["id"], 
                                caption=f"<a href='t.me/{chat_info.username}'>📎 {chat_info.full_name}</a>")
        channels[key]["posts"].pop(0)
        await update_channels(channels)
    else:
        logger.exception(f'Bot ({key}) dont does not have publishing rights!')

async def ticker():
    last_post_flags = {}
    while True:
        now = datetime.now(MOSCOW_TZ)
        current_time = now.time().replace(second=0, microsecond=0)
        today_str = now.date().isoformat()

        channels = await get_channels()
        for key, info in channels.items():
            channel_id = info["id"]
            post_times = info.get("time", [])
            posts = info.get("posts", [])

            for time_str in post_times:
                try:
                    post_time = time.fromisoformat(time_str)
                except ValueError:
                    continue

                if len(posts) < 1:
                    continue

                flag_key = f"{channel_id}_{post_time.isoformat()}_{today_str}"
                if current_time == post_time and flag_key not in last_post_flags:
                    await publish_post(key)
                    last_post_flags[flag_key] = True

        await asyncio.sleep(30)