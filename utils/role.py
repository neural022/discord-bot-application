
import logging
import discord

class RoleManager:
    """Handles role assignment and reaction-based role management."""

    def __init__(self, bot_client):
        """
        Initialize the RoleManager with the given bot client.

        Args:
            bot_client (discord.Client): The bot client used to interact with Discord.
        """
        self.bot = bot_client
        self.config = bot_client.config
        self.dev_mode = self.config.get("dev_mode")
        self.rule_msg = self.config.get("default_rule_msg", "")
        self.role_message_id = self.config.get("role_message_id", 0)
        self.emoji_ids = self.config.get("emoji_ids", {})
        self.emoji_to_role = self.config.get("emoji_to_role", {})

    async def post_or_update_role_message(self):
        """
        Send or update the role selection message in the Discord channel.

        If a message with the role selection already exists, it will be updated.
        Otherwise, a new message will be sent.

        Raises:
            ValueError: If the channel ID is not set in the configuration or the channel cannot be found.
        """
        if self.dev_mode:
            logging.info("🚧 Running in dev mode!")
            channel_id = self.config.get("test_command_channel_id")
        else:
            channel_id = self.config.get("bot_command_channel_id")

        if not channel_id:
            raise ValueError("Channel ID not set in config.json")

        channel = self.bot.get_channel(channel_id)
        if not channel:
            logging.error(f"⚠️ Channel with ID {channel_id} not found.")
            return

        content = self.rule_msg
        for emoji_id, role_info in self.emoji_to_role.items():
            role = channel.guild.get_role(role_info['role_id'])
            if role:
                content += f"> 🔹 {role_info['role_name']} → <:{self.emoji_ids[emoji_id]}:{emoji_id}>\n"

        message = None
        if self.role_message_id:
            try:
                message = await channel.fetch_message(self.role_message_id)
                await message.edit(content=content)
                logging.info("📝 Updated existing role message.")
            except discord.NotFound:
                logging.warning("💬 Role message not found. Sending a new one.")
            except discord.HTTPException as e:
                logging.error(f"❌ Failed to update role message: {e}")
                return

        if message is None:
            message = await channel.send(content)
            self.role_message_id = message.id
            self.config.set("role_message_id", message.id)
            logging.info("⚡ Posted new role message.")

        if message:
            for emoji_id in self.emoji_to_role.keys():
                emoji = f"<:{self.emoji_ids[emoji_id]}:{emoji_id}>"
                try:
                    await message.add_reaction(emoji)
                    logging.info(f"✅ Successfully added reaction: {emoji}")
                except discord.HTTPException as e:
                    logging.error(f"❌ Failed to add emoji {emoji}: {e}")
                except Exception as e:
                    logging.error(f"⚠️ Unexpected error with emoji {emoji}: {e}")

    async def handle_role(self, payload, add=True):
        if payload.message_id != self.role_message_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            logging.info("⚠️ No guild found.")
            return
        
        # confirm emoji in emoji_to_role mapping
        emoji = str(payload.emoji.id)
        if emoji not in self.emoji_to_role.keys():
            logging.info(f"⚠️ Emoji Key[{emoji}] not in emoji_to_role mapping.")
            return

        role_id = self.emoji_to_role[emoji]['role_id']
        if not role_id:
            logging.info(f"⚠️ No role_id found for emoji {emoji}.")
            return

        role = guild.get_role(role_id)
        if not role:
            logging.info(f"⚠️ Role {role_id} not found in guild.")
            return

        member = (payload.member if add else guild.get_member(payload.user_id))
        if not member:
            logging.info(f"⚠️ Member {payload.user_id} not found.")
            return

        # don't reaction to ourselves
        if member == self.bot.user:
            return

        try:
            if add:
                await member.add_roles(role)
                logging.info(f"➕ Added role {role.name} for {member.display_name}.")
            else:
                await member.remove_roles(role)
                logging.info(f"➖ Removed role {role.name} from {member.display_name}.")
        except discord.HTTPException as e:
            logging.error(f"❌ Failed to {'add' if add else 'remove'} role: {e}")
