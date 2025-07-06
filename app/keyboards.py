from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils import get_channels
from app.forms import Channel

async def channels_menu():
    CHANNELS = await get_channels()
    builder = InlineKeyboardBuilder()
    for key in CHANNELS.keys():
        days = len(CHANNELS[key]["posts"])//len(CHANNELS[key]["time"])
        if days < 30: emoji = "⚠️" 
        else: emoji = "✅" 
        builder.button(text=f"📣 {key} | {len(CHANNELS[key]['posts'])} ({days}d) {emoji}", callback_data=key)
    builder.button(text="➕ Add channel", callback_data="add_channel")
    builder.adjust(1)
    return builder.as_markup()

async def post_menu(index: int, len: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="♦️ To add a caption, write it in the chat", callback_data="other")
    builder.button(text='♦️ To delete a caption, write "/delete_caption"', callback_data="other")
    builder.button(text="❌", callback_data="disagree")
    builder.button(text=f"{index+1} / {len}", callback_data="other")
    builder.button(text="✅", callback_data="agree")
    builder.button(text="◀️ Leave", callback_data="leave")
    builder.adjust(1,1,3,1)
    return builder.as_markup()

async def channel_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Leave", callback_data="leave")
    builder.button(text="📝 Post generator", callback_data="parser_query")
    builder.button(text="🗓 Posts queue", callback_data="posts_queue")
    builder.button(text="⏰ Publication time", callback_data="publication_time")
    builder.adjust(1)
    return builder.as_markup()

async def posts_queue_menu(channel: Channel, index: int, posts: list):
    true_index = len(posts)+index
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Leave", callback_data=channel.key)
    builder.button(text=f"{true_index+1}/{len(posts)}", callback_data="other")
    adjust = [1,1,0]
    if true_index > 9:
        builder.button(text="⬅️🔟", callback_data="prev_10")
        adjust[len(adjust)-1] += 1
    if true_index > 0:
        builder.button(text="⬅️", callback_data="prev")
        adjust[len(adjust)-1] += 1
    if true_index < len(posts)-1:
        builder.button(text="➡️", callback_data="next")
        adjust[len(adjust)-1] += 1
    if true_index < len(posts)-10:
        builder.button(text="🔟➡️", callback_data="next_10")
        adjust[len(adjust)-1] += 1
    builder.button(text="🗑", callback_data="delete")
    adjust.append(1)
    builder.button(text='♦️ To edit post index, write "/index [new index]"', callback_data="other")
    adjust.append(1)
    builder.button(text="♦️ To edit a caption, write it in the chat", callback_data="other")
    adjust.append(1)
    builder.button(text='♦️ To delete a caption, write "/delete_caption"', callback_data="other")
    adjust.append(1)
    builder.adjust(*adjust)
    return builder.as_markup()


async def times_menu(channel: Channel):
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Leave", callback_data=channel.key)
    adjust = [1]
    index = 0
    times = await channel.time
    for time in times:
        builder.button(text=f"🕘{time}", callback_data="other")
        builder.button(text="➖", callback_data=f"removetime_{index}")
        index += 1
        adjust.append(2)
    builder.adjust(*adjust)
    return builder.as_markup()

async def leave_btn(call_data: str = "leave"):
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Leave", callback_data=call_data)
    return builder.as_markup()