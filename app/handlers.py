from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, URLInputFile, InputMediaPhoto
from aiogram.filters import CommandStart, Filter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.utils import get_admins, get_masters, get_channels, get_settings, check_time, check_index
from app.keyboards import *
from app.scenario import *
from utils.parser import get_pinterest_images
from app.forms import Channel
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio

#init router
router = Router()

#states
class Wait(StatesGroup):
    parser_query = State()
    channel_menu = State()
    loading_pins = State()
    post_generator = State()
    channel_time_edit = State()
    post_queue = State()
    new_channel_info = State()

#filters
class IsAdmin(Filter):
    async def __call__(self, msg: Message):
        ADMINS = await get_admins()
        MASTERS = await get_masters()
        return (msg.from_user.id in ADMINS) or (msg.from_user.id in MASTERS)

class IsMaster(Filter):
    async def __call__(self, msg: Message):
        MASTERS = await get_masters()
        return msg.from_user.id in MASTERS

class ChannelCall(Filter):
    async def __call__(self, call: CallbackQuery):
        CHANNELS = await get_channels()
        return call.data in CHANNELS.keys()

class RemoveTimeCall(Filter):
    async def __call__(self, call: CallbackQuery):
        data = call.data
        return data.split("_")[0] == "removetime"

class SessionExpired(Filter):
    async def __call__(self, call: CallbackQuery):
        time = datetime.now(ZoneInfo("UTC"))
        msg_time = call.message.date
        return (time - msg_time).days >= 1

class ForwardedChannelMessage(Filter):
    async def __call__(self, msg: Message):
        return msg.forward_from_chat is not None and msg.forward_from_chat.type == "channel"

#handlers
@router.message(Command("id"))
async def id_coommand_handler(msg: Message):
    await msg.delete()
    await msg.answer(text=f"Your id: {msg.from_user.id}")

@router.message(ForwardedChannelMessage())
async def forwarded_message_handler(msg: Message):
        channel_id = msg.forward_from_chat.id
        await msg.answer(f"<b>channel ID:</b> <code>{channel_id}</code>")

@router.message(IsAdmin(), CommandStart())
async def start_handler(msg: Message, state: FSMContext):
    await state.clear()
    await msg.delete()
    await msg.answer(text="♦️ <b>Choose menu:</b>", reply_markup=await start_menu())

@router.callback_query(IsAdmin(), SessionExpired())
async def session_expired_handler(call: CallbackQuery):
    await call.answer(text="Session expired, write /start", show_alert=True)

@router.callback_query(IsAdmin(), F.data == "channels_menu")
async def channels_menu_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    if call.message.photo:
        await call.message.delete()
        await call.message.answer(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu(id=call.from_user.id))
    else:
        await call.message.edit_text(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu(id=call.from_user.id))

@router.callback_query(IsAdmin(), ChannelCall())
async def channel_call_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Wait.channel_menu)
    channels = await get_channels()
    chnl = channels[call.data]
    channel = Channel(key=call.data, id=chnl["id"])
    info = await channel.info
    if info != None:
        info_text = f"📌 <b>{info.full_name}</b> - <b>@{info.username}</b>\n🆔 <code>{channel.id}</code>"
    else:
        info_text = f"📌 <b> {channel.key} </b>\n🆔 <code>{channel.id}</code>"
    await call.message.delete()
    false_perms = ""
    if not await channel.check_perms(): false_perms = "\n⛔️ <b>The bot can't post in the channel. Give him admin rights.</b>\n"
    text = f"{info_text}\n\n<b>✅ Post ready:</b> {len(await channel.posts)} ({await channel.days}d)\n{false_perms}\n♦️ <b>Choose option:</b>"
    bot_msg = await call.message.answer(text=text, 
                                reply_markup= await channel_menu())
    await state.update_data(channel=channel, bot_message=bot_msg)

@router.message(IsMaster(), Wait.channel_menu, Command("new_id"))
async def edit_channel_id_handler(msg: Message, state: FSMContext):
    data = msg.text.split()
    if len(data) == 2 and len(data[1]) == 14:
        state_data : dict = await state.get_data()
        chnl: Channel = state_data["channel"]
        new_id = int(msg.text.split()[1])
        channels = await get_channels()
        if all(map(lambda x: channels[x]["id"] != new_id, channels.keys())):
            await chnl.edit_id(new_id=new_id)
            await msg.answer(text=f"<b>{chnl.key} ID successfully changed!</b>")
        else:
            await msg.answer(text="<b>Error. Channel with this ID already in the bot.</b>")
    else:
        await msg.answer(text="<b>Error. Invalid ID value</b>")

@router.message(IsMaster(), Wait.channel_menu, Command("delete_channel"))
async def delete_channel_handler(msg: Message, state: FSMContext):
    state_data : dict = await state.get_data()
    chnl: Channel = state_data["channel"]
    data = msg.text.split()
    if len(data) == 2 and data[1] == chnl.key:
        bot_message: Message = state_data["bot_message"]
        await bot_message.delete()
        await chnl.delete()
        await msg.answer(text=f"<b>{chnl.key} successfully deleted!</b>")
    else:
        await msg.answer(text=f"<b>To confirm the delete, write <code>/delete_channel {chnl.key}</code></b>")

@router.callback_query(IsMaster(), Wait.new_channel_info, F.data == "confirm")
async def confirm_info_handler(call: CallbackQuery, state: FSMContext):
    state_data : dict = await state.get_data()
    cId, cKey, cTime = state_data["cId"], state_data["cKey"], state_data["cTime"]
    channels = await get_channels()
    if not (cKey in channels):
        if all(map(lambda x: channels[x]["id"] != cId, channels.keys())):
            channels[cKey] = {
                "id": cId,
                "time": cTime,
                "posts": []
            }
            await update_channels(channels)
            await call.answer("The channel is connected to the bot")
            await call.message.edit_text(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu(id=call.from_user.id))
        else:
            await call.answer("Error. Channel with this ID already in the bot.", show_alert=True)
    else:
        await call.answer("Error. Channel with this KEY already in the bot.", show_alert=True)

@router.message(IsMaster(), Wait.new_channel_info)
async def channel_info_handler(msg: Message, state: FSMContext):
    state_data = await state.get_data()
    bot_msg: Message = state_data["bot_message"]
    data: list[str] = msg.text.split("\n")
    await msg.delete()
    try:
        cId, cKey, cTime = data[:3]
        cTime = cTime.replace(" ", "").split(",")
        text = ("📝<b>Check the correctness of the entered data:</b>\n"+
               f"\n<b>ID:</b> {cId}\n<b>KEY:</b> {cKey}\n<b>POSTING TIME:</b> {', '.join(cTime)}")
        await bot_msg.edit_text(text=text, reply_markup=await confirm_info())
        await state.update_data(cId=int(cId), cKey=cKey, cTime=cTime)
    except ValueError:
        pass

@router.callback_query(IsMaster(), F.data == "add_channel")
async def add_channel_handler(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(Wait.new_channel_info)
    text = ("♦️<b>For add channel in posting bot, write the following data:</b>\n"+
            "- channel id\n- channel key\n- posting time\n"+
            "\n🧾<b>Example:</b>\n"+
            "-1002896777542\nkittens\n07:00, 12:00, 17:00, 22:00")
    bot_message = await call.message.answer(text=text)
    await state.update_data(bot_message=bot_message)
    await call.answer()

@router.callback_query(IsAdmin(), Wait.channel_menu, F.data == "posts_queue")
async def post_queue_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(Wait.post_queue)
    state_data = await state.get_data()
    channel: Channel = state_data["channel"]
    posts = await channel.posts
    index = len(posts)*-1
    await state.update_data(index=index)
    await call.message.delete()
    bot_message = await call.message.answer_photo(photo=posts[index]["id"], 
                                    caption=posts[index]["caption"], 
                                    reply_markup=await posts_queue_menu(channel, index, posts))
    await state.update_data(bot_message=bot_message)

@router.message(IsAdmin(), Wait.post_queue, Command("index"))
async def post_edit_index_handler(msg: Message, state: FSMContext):
    await msg.delete()
    msg_arr = msg.text.split(" ")
    if len(msg_arr) == 2 and check_index(msg_arr[1]):
        state_data = await state.get_data()
        bot_msg: Message = state_data["bot_message"]
        channel: Channel = state_data["channel"]
        index = state_data["index"]
        posts = await channel.posts
        if 0 < int(msg_arr[1]) <= len(posts):
            new_index = ((len(posts)*-1) + (int(msg_arr[1])))-1
            true_index = int(msg_arr[1])-1
            await channel.edit_index(old_index=index, new_index=true_index)
            await state.update_data(index=new_index)
            posts = await channel.posts
            await bot_msg.edit_reply_markup(reply_markup=await posts_queue_menu(channel, new_index, posts))

@router.message(IsAdmin(), Wait.post_queue, Command("delete_caption"))
async def post_remove_caption_handler(msg: Message, state: FSMContext):
    await msg.delete()
    state_data = await state.get_data()
    bot_msg = state_data["bot_message"]
    channel: Channel = state_data["channel"]
    index = state_data["index"]
    posts = await channel.posts
    await channel.update_caption(post_index=index)
    await bot_msg.edit_caption(caption=None, reply_markup=await posts_queue_menu(channel, index, posts))

@router.message(IsAdmin(), Wait.post_queue)
async def post_edit_caption_handler(msg: Message, state: FSMContext):
    await msg.delete()
    state_data = await state.get_data()
    bot_msg = state_data["bot_message"]
    channel: Channel = state_data["channel"]
    index = state_data["index"]
    posts = await channel.posts
    await channel.update_caption(caption=msg.text, post_index=index)
    await bot_msg.edit_caption(caption=msg.text, reply_markup=await posts_queue_menu(channel, index, posts))

@router.callback_query(IsAdmin(), Wait.post_queue, F.data == "delete")
async def delete_post_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(Wait.post_queue)
    state_data = await state.get_data()
    channel: Channel = state_data["channel"]
    index = state_data["index"]
    await channel.delete_post(index)
    posts = await channel.posts
    await call.answer(text="Post was deleted")
    if index == (len(posts)+1)*-1:
        index += 1
    await state.update_data(index=index)
    await call.message.edit_media(media=InputMediaPhoto(media=posts[index]["id"],
                                                            caption=posts[index]["caption"]), 
                                    reply_markup=await posts_queue_menu(channel, index, posts))
    

@router.callback_query(IsAdmin(), Wait.post_queue, F.data=="prev")
async def prev_post_handler(call: CallbackQuery, state: FSMContext):
    await posts_queue_move(call=call, state=state, index_difference=-1)

@router.callback_query(IsAdmin(), Wait.post_queue, F.data=="prev_10")
async def prev_post_handler(call: CallbackQuery, state: FSMContext):
    await posts_queue_move(call=call, state=state, index_difference=-10)

@router.callback_query(IsAdmin(), Wait.post_queue, F.data=="next")
async def prev_post_handler(call: CallbackQuery, state: FSMContext):
    await posts_queue_move(call=call, state=state, index_difference=1)

@router.callback_query(IsAdmin(), Wait.post_queue, F.data=="next_10")
async def prev_post_handler(call: CallbackQuery, state: FSMContext):
    await posts_queue_move(call=call, state=state, index_difference=10)

@router.callback_query(IsAdmin(), Wait.channel_menu, F.data == "publication_time")
async def time_edit_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(Wait.channel_time_edit)
    state_data = await state.get_data()
    channel: Channel = state_data["channel"]
    info = await channel.info
    await call.message.edit_text(text=f'📌 <b>{info.full_name}</b> - <b>@{info.username}</b>\n\n♦️ <b>To add time (Moscow), write in chat\nthe format "hh:mm": <u>06:06</u> / <u>12:30</u></b>', 
                                reply_markup=await times_menu(channel))    

@router.callback_query(IsAdmin(), Wait.channel_time_edit, RemoveTimeCall())
async def remove_time_handler(call: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    channel: Channel = state_data["channel"]
    index = int(call.data.split("_")[1])
    await channel.remove_time(index)
    info = await channel.info
    await call.message.edit_text(text=f'📌 <b>{info.full_name}</b> - <b>@{info.username}</b>\n\n♦️ <b>To add time (Moscow), write in chat\nthe format "hh:mm": <u>06:06</u> / <u>12:30</u></b>', 
                                reply_markup=await times_menu(channel)) 

@router.message(IsAdmin(), Wait.channel_time_edit)
async def add_time_handler(msg: Message, state: FSMContext):
    data = msg.text
    await msg.delete()
    state_data = await state.get_data()
    channel: Channel = state_data["channel"]
    check = await check_time(data)
    if check:
        await channel.add_time(data)
        bot_msg = state_data["bot_message"]
        info = await channel.info
        await bot_msg.edit_text(text=f'📌 <b>{info.full_name}</b> - <b>@{info.username}</b>\n\n♦️ <b>To add time (Moscow), write in chat\nthe format "hh:mm": <u>06:06</u> / <u>12:30</u></b>', 
                                reply_markup=await times_menu(channel))

@router.callback_query(IsAdmin(), Wait.channel_menu, F.data == "parser_query")
async def parser_query_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(Wait.parser_query)
    state_data = await state.get_data()
    await call.message.edit_text(text="📝 <b>Enter a search query for pins</b>", reply_markup= await leave_btn(state_data["channel"].key))

@router.message(IsAdmin(), Wait.parser_query)
async def parser_query_handler(msg: Message, state: FSMContext):
    await state.set_state(Wait.loading_pins)
    state_data = await state.get_data()
    bot_msg = state_data["bot_message"]
    await msg.delete()
    await bot_msg.edit_text(text="📥 <b>Loading pins...</b>")
    SETTINGS = await get_settings()
    pins = await asyncio.to_thread(get_pinterest_images, msg.text, SETTINGS["pins_parse"])
    if pins == None:
        await state.clear()
        await bot_msg.delete()
        await msg.answer(text="Error. Please try another query. (write /start)")
    else:
        await state.update_data(pins=pins, index=0)
        await bot_msg.delete()
        new_bot_msg = await msg.answer_photo(photo=URLInputFile(pins[0]), reply_markup= await post_menu(0, len(pins)))
        await state.update_data(bot_message=new_bot_msg)
        await state.set_state(Wait.post_generator)

@router.message(IsAdmin(), Wait.post_generator, Command("delete_caption"))
async def remove_caption_handler(msg: Message, state: FSMContext):
    await msg.delete()
    state_data = await state.get_data()
    bot_msg = state_data["bot_message"]
    await bot_msg.edit_caption(caption=None, reply_markup= await post_menu(state_data["index"], len(state_data["pins"])))

@router.message(IsAdmin(), Wait.post_generator)
async def post_caption_handler(msg: Message, state: FSMContext):
    await msg.delete()
    state_data = await state.get_data()
    bot_msg = state_data["bot_message"]
    await bot_msg.edit_caption(caption=msg.text, reply_markup= await post_menu(state_data["index"], len(state_data["pins"])))

@router.callback_query(IsAdmin(), F.data == "agree", Wait.post_generator)
async def post_agree_handler(call: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    pins = state_data["pins"]
    await agree_post(state_data["channel"], call.message.photo[-1].file_id , call.message.caption)
    if state_data["index"]+1 < len(pins):
        await call.message.edit_media(media=InputMediaPhoto(media=URLInputFile(url=pins[state_data["index"]+1])), reply_markup= await post_menu(state_data["index"]+1, len(state_data["pins"])))
        await state.update_data(index=state_data["index"]+1)
    else:
        await state.clear()
        await call.message.delete()
        await call.message.answer(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu(id=call.from_user.id))

@router.callback_query(IsAdmin(), F.data == "disagree", Wait.post_generator)
async def post_disagree_handler(call: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    pins = state_data["pins"]
    if state_data["index"]+1 < len(pins):
        await call.message.edit_media(media=InputMediaPhoto(media=URLInputFile(url=pins[state_data["index"]+1])), reply_markup= await post_menu(state_data["index"]+1, len(state_data["pins"])))
        await state.update_data(index=state_data["index"]+1)
    else:
        await state.clear()
        await call.message.delete()
        await call.message.answer(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu(id=call.from_user.id))

@router.callback_query(IsAdmin(), F.data == "leave")
async def post_leave_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer(text="♦️ <b>Choose menu:</b>", reply_markup=await start_menu())

@router.message()
async def other_msg_handler(msg: Message):
    await msg.delete()

@router.callback_query(F.data == "other")
async def other_call_handler(call: CallbackQuery):
    await call.answer()

@router.callback_query()
async def other_call_handler(call: CallbackQuery):
    await call.answer(text="In development... (OR you dont have permissions)", show_alert=True)