import logging
import json
import io
import discord

from utils import ConfigManager, RoleManager, ChannelManager

class BotClient(discord.Client):
    """Main bot client that handles events."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the bot client with the provided arguments and keyword arguments.

        Args:
            *args: Positional arguments passed to the discord.Client constructor.
            **kwargs: Keyword arguments passed to the discord.Client constructor.
        """
        super().__init__(*args, **kwargs)
        self.dev_mode = True
        self.config = ConfigManager()
        self.role_manager = RoleManager(self)
        self.channel_manager = ChannelManager(self)

    async def on_ready(self):
        """
        Called when the bot has successfully logged in and is ready.

        Logs the bot's username and posts or updates the role selection message.
        """
        logging.info(f"🌐 Logged in as {self.user}")
        await self.role_manager.post_or_update_role_message()

    async def on_message(self, message):
        """
        Handles incoming messages.

        Args:
            message (discord.Message): The message received from Discord.

        If the message content is "$愛姆露", it sends a response. If the content is "!list_emojis", it sends a list of emoji IDs.
        """
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == "!愛姆露":
            await message.channel.send("桑樂SUN 桑樂SUN")

        if message.content == "!list_emojis":
            if not message.author.guild_permissions.administrator:
                await message.channel.send("⛔ 你沒有權限使用這個指令！")
                return

            emoji_mapping = {str(e.id): e.name for e in message.guild.emojis}
            json_data = json.dumps({"emoji_ids": emoji_mapping}, indent=4, ensure_ascii=False)
            file = discord.File(io.BytesIO(json_data.encode()), filename="emoji_list.json")
            await message.channel.send("🔍 這是伺服器的表情 ID 列表：", file=file)
        
        if message.content.startswith("!dump_channel_msg"):
            if not message.author.guild_permissions.administrator:
                await message.channel.send("⛔ 你沒有權限使用這個指令！")
                return

            await self.fetch_channel_msg(message.channel.id)
            

    async def on_raw_reaction_add(self, payload):
        """
        Handles adding a reaction to a message.

        Args:
            payload (discord.RawReactionActionEvent): The payload containing information about the reaction added.

        Calls the role manager to handle the role assignment.
        """
        await self.role_manager.handle_role(payload, add=True)

    async def on_raw_reaction_remove(self, payload):
        """
        Handles removing a reaction from a message.

        Args:
            payload (discord.RawReactionActionEvent): The payload containing information about the reaction removed.

        Calls the role manager to handle the role removal.
        """
        await self.role_manager.handle_role(payload, add=False)

    async def fetch_channel_msg(self, channel_id):
        self.channel_manager.channel_id = channel_id
        await self.channel_manager.handle_channel(save_file=f"{channel_id}_dump.json")

if __name__ == '__main__':
    ACESS_TOKEN = 'YOUR_ACESS_TOKEN'

    ''' Variables to control bot permissions for different intents '''
    # message_content: allow read msg.
    # guilds: allow read server's info.
    # members(required): allow server's member.
    # reactions(required): allow read emoji reaction.
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    intents.reactions = True

    client = BotClient(intents=intents)
    client.run(ACESS_TOKEN)