from app.utils import get_channels, update_channels
from app.forms import Channel

async def agree_post(channel: Channel, id: str, caption: str):
    data = await get_channels()
    data[channel.key]["posts"].append({"id": id, "caption": caption})
    await update_channels(data)
    