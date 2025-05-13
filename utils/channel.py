
import os
import json
import logging
import aiohttp
import asyncio
from tqdm import tqdm

class ChannelManager():
    def __init__(self, bot_client):
        self.bot_client = bot_client
        self.save_path = None
        self.channel_id = None
        self.save_path = "download"

    async def fetch_channel(self):
        logging.info("🚧 Running in dev mode!")
        return self.bot_client.get_channel(self.channel_id)
    
    async def download_image(self, session, url, file_path):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())
                else:
                    logging.error(f"❌ Failed to download {url} (HTTP {response.status})")
        except Exception as e:
            logging.error(f"download fail {url}:{e}")


    async def fetch_all_messages(self):
        channel = await self.fetch_channel()

        logging.info(f"start fetch channel msgs...")
        raw_msg = [ msg async for msg  in channel.history(limit=None, oldest_first=True) ]

        logging.info(f"fetch # of msg:{len(raw_msg)}")
        logging.info(f"start processing...")

        msg_data = list()
        download_task = list()

        async with aiohttp.ClientSession() as session:
            for msg in tqdm(raw_msg, desc="downloading msgs"):
                msg_info = {
                    'id':msg.id,
                    'author': str(msg.author),
                    'timestamp': str(msg.created_at),
                    'content': msg.content,
                    'attachments': []
                }

                for attachment in msg.attachments:
                    url = attachment.url
                    file_path = os.path.join(self.save_path, f"{msg.id}_{attachment.filename}")
                    # await self.download_image(url, file_path)
                    msg_info['attachments'].append({
                        'url':url,
                        'save_as':file_path
                    })

                    download_task.append(self.download_image(session, url, file_path))
                msg_data.append(msg_info)

            await asyncio.gather(*download_task)

        return msg_data

    async def save_to_json(self):
        msg = await self.fetch_all_messages()
        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(msg, f, ensure_ascii=False, indent=4)
        logging.info(f"✅Successfully saved messages and images data:{self.save_file}")

    async def handle_channel(self, save_file='channel_dump.json'):
        if self.channel_id is None:
            logging.error("❌ channel_id is not setting.")
            return
        if os.path.exists(self.save_path) == False:
            os.mkdir(self.save_path)
        self.save_file = save_file
        await self.save_to_json()