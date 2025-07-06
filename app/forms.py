from app.init_bot import bot
from app.utils import get_channels, update_channels

class Channel:
    def __init__(self, key: str, id: int):
        self.__key = key
        self.__id = id
    
    @property
    def key(self): return self.__key
    @property
    def id(self): return self.__id
    @property
    async def time(self): 
        channels = await get_channels()
        return channels[self.__key]["time"]
    @property
    async def posts(self): 
        channels = await get_channels()
        return channels[self.__key]["posts"]
    
    @property
    async def info(self):
        info = await bot.get_chat(chat_id=self.__id)
        return info
    
    @property
    async def days(self): 
        return len(await self.posts) // len(await self.time)
    
    async def remove_time(self, index: int):
        channels = await get_channels()
        channels[self.__key]["time"].pop(index)
        channels[self.__key]["time"] = sorted(channels[self.__key]["time"])
        await update_channels(channels)
    
    async def add_time(self, time: str):
        channels = await get_channels()
        channels[self.__key]["time"].append(time)
        channels[self.__key]["time"] = sorted(channels[self.__key]["time"])
        await update_channels(channels)

    async def delete_post(self, index: int):
        channels = await get_channels()
        channels[self.__key]["posts"].pop(index)
        await update_channels(channels)
    
    async def update_caption(self, post_index: int, caption: str = None):
        channels = await get_channels()
        channels[self.__key]["posts"][post_index]["caption"] = caption
        await update_channels(channels)

    async def edit_index(self, old_index: int, new_index: int):
        channels = await get_channels()
        channels[self.__key]["posts"].insert(new_index, channels[self.__key]["posts"].pop(old_index))
        await update_channels(channels)