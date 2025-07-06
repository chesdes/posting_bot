from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, URLInputFile, InputMediaPhoto
from aiogram.filters import CommandStart, Filter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.utils import get_admins, get_channels, get_settings, check_time, check_index
from app.keyboards import *
from app.scenario import agree_post
from utils.parser import get_pinterest_images
from app.forms import Channel
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

#filters
class IsAdmin(Filter):
    async def __call__(self, msg: Message):
        ADMINS = await get_admins()
        return msg.from_user.id in ADMINS

class ChannelCall(Filter):
    async def __call__(self, call: CallbackQuery):
        CHANNELS = await get_channels()
        return call.data in CHANNELS.keys()

class RemoveTimeCall(Filter):
    async def __call__(self, call: CallbackQuery):
        data = call.data
        return data.split("_")[0] == "removetime"

#handlers
try:
    @router.message(IsAdmin(), CommandStart())
    async def start_handler(msg: Message):
        await msg.delete()
        await msg.answer(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu())

    @router.callback_query(IsAdmin(), ChannelCall())
    async def channel_call_handler(call: CallbackQuery, state: FSMContext):
        await state.clear()
        await state.set_state(Wait.channel_menu)
        channels = await get_channels()
        chnl = channels[call.data]
        channel = Channel(key=call.data, id=chnl["id"])
        info = await channel.info
        await call.message.delete()
        bot_msg = await call.message.answer(text=f"📌 <b>{info.full_name}</b> - <b>@{info.username}</b>\n<b>✅ Post ready:</b> {len(await channel.posts)} ({await channel.days}d)\n\n♦️ <b>Choose option:</b>", 
                                    reply_markup= await channel_menu())
        await state.update_data(channel=channel, bot_message=bot_msg)

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
        await call.message.edit_media(media=InputMediaPhoto(media=posts[index]["id"],
                                                                caption=posts[index]["caption"]), 
                                        reply_markup=await posts_queue_menu(channel, index, posts))

    @router.callback_query(IsAdmin(), Wait.post_queue, F.data=="prev")
    async def prev_post_handler(call: CallbackQuery, state: FSMContext):
        state_data = await state.get_data()
        index = state_data["index"]
        channel: Channel = state_data["channel"]
        posts = await channel.posts
        true_index = len(posts)+index
        if true_index > 0:
            channel: Channel = state_data["channel"]
            posts = await channel.posts
            index -= 1
            await state.update_data(index=index)
            await call.message.edit_media(media=InputMediaPhoto(media=posts[index]["id"],
                                                                caption=posts[index]["caption"]), 
                                        reply_markup=await posts_queue_menu(channel, index, posts))
        else:
            await call.answer(text="Error: Looks like the queue has changed")

    @router.callback_query(IsAdmin(), Wait.post_queue, F.data=="prev_10")
    async def prev_post_handler(call: CallbackQuery, state: FSMContext):
        state_data = await state.get_data()
        index = state_data["index"]
        channel: Channel = state_data["channel"]
        posts = await channel.posts
        true_index = len(posts)+index
        if true_index > 9:
            channel: Channel = state_data["channel"]
            posts = await channel.posts
            index -= 10
            await state.update_data(index=index)
            await call.message.edit_media(media=InputMediaPhoto(media=posts[index]["id"],
                                                                caption=posts[index]["caption"]), 
                                        reply_markup=await posts_queue_menu(channel, index, posts))
        else:
            await call.answer(text="Error: Looks like the queue has changed")

    @router.callback_query(IsAdmin(), Wait.post_queue, F.data=="next")
    async def prev_post_handler(call: CallbackQuery, state: FSMContext):
        state_data = await state.get_data()
        index = state_data["index"]
        channel: Channel = state_data["channel"]
        posts = await channel.posts
        true_index = len(posts)+index
        if true_index < len(posts)-1:
            channel: Channel = state_data["channel"]
            posts = await channel.posts
            index += 1
            await state.update_data(index=index)
            await call.message.edit_media(media=InputMediaPhoto(media=posts[index]["id"],
                                                                caption=posts[index]["caption"]), 
                                        reply_markup=await posts_queue_menu(channel, index, posts))
        else:
            await call.answer(text="Error: Looks like the queue has changed")

    @router.callback_query(IsAdmin(), Wait.post_queue, F.data=="next_10")
    async def prev_post_handler(call: CallbackQuery, state: FSMContext):
        state_data = await state.get_data()
        index = state_data["index"]
        channel: Channel = state_data["channel"]
        posts = await channel.posts
        true_index = len(posts)+index
        if true_index < len(posts)-10:
            channel: Channel = state_data["channel"]
            posts = await channel.posts
            index += 10
            await state.update_data(index=index)
            await call.message.edit_media(media=InputMediaPhoto(media=posts[index]["id"],
                                                                caption=posts[index]["caption"]), 
                                        reply_markup=await posts_queue_menu(channel, index, posts))
        else:
            await call.answer(text="Error: Looks like the queue has changed")

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
            await call.message.answer(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu())

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
            await call.message.answer(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu())

    @router.callback_query(IsAdmin(), F.data == "leave")
    async def post_leave_handler(call: CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.delete()
        await call.message.answer(text="♦️ <b>Choose channel:</b>", reply_markup=await channels_menu())

    @router.message()
    async def other_msg_handler(msg: Message):
        await msg.delete()

    @router.callback_query(F.data == "other")
    async def other_call_handler(call: CallbackQuery):
        await call.answer()

    @router.callback_query()
    async def other_call_handler(call: CallbackQuery):
        await call.answer(text="In development...", show_alert=True)
except Exception as ex:
    @router.callback_query()
    async def other_call_handler(call: CallbackQuery):
        await call.answer(text=f"Error: {ex}, write /start", show_alert=True)