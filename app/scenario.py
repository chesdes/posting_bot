from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from app.utils import get_channels, update_channels
from app.forms import Channel
from app.keyboards import posts_queue_menu

async def agree_post(channel: Channel, id: str, caption: str):
    data = await get_channels()
    data[channel.key]["posts"].append({"id": id, "caption": caption})
    await update_channels(data)
    
async def posts_queue_move(call: CallbackQuery, 
                           state: FSMContext, 
                           index_difference: int):
    state_data = await state.get_data()
    index = state_data["index"]
    channel: Channel = state_data["channel"]
    posts = await channel.posts
    true_index = len(posts)+index
    if (
        (true_index > abs(index_difference)-1 and index_difference < 0) 
        or 
        (true_index < len(posts)-abs(index_difference) and index_difference > 0)
        ):
        channel: Channel = state_data["channel"]
        posts = await channel.posts
        index += index_difference
        await state.update_data(index=index)
        await call.message.edit_media(media=InputMediaPhoto(media=posts[index]["id"],
                                                            caption=posts[index]["caption"]), 
                                    reply_markup=await posts_queue_menu(channel, index, posts))
    else:
        await call.answer(text="Error: Looks like the queue has changed")