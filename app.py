# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

import logging
import logging.handlers
import traceback
from typing import List, Dict
from datetime import datetime
from importlib import import_module
import discord
from dotenv import dotenv_values
from utils import DbOperations, UmbraClientConfig


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename=f"{__file__}.log",
    encoding="utf-8",
    maxBytes=32*1024*1024,
    backupCount=5
)
formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


class UmbraClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, initial_extensions: List[str], config):
        super().__init__(intents=intents)
        self.config = UmbraClientConfig(initial_extensions, config)
        self.tree = discord.app_commands.CommandTree(self)

    def load_config_from_db(self):
        query = DbOperations.query_db(DbOperations.get_db(self.config), "select skey, svalue from settings")
        for elem in query:
            setattr(self.config, elem["skey"], elem["svalue"])

    def load_elems_from_db(self, query: str, elem_name: str, target_list: List[int]):
        query = DbOperations.query_db(DbOperations.get_db(self.config), query)
        for elem in query:
            target_list.append(int(elem[elem_name]))

    def load_dict_from_db(self, query: str, key: str, value: str, target_dict: Dict[str, str]):
        query = DbOperations.query_db(DbOperations.get_db(self.config), query)
        for elem in query:
            target_dict.update({str(elem[key]): elem[value]})

    def check_user_has_rights(self, interaction: discord.Interaction):
        if hasattr(self.config, "manager_id"):
            return any([interaction.user.guild_permissions.administrator, any(role.id == int(self.config.manager_id) for role in interaction.user.roles)])
        return interaction.user.guild_permissions.administrator

    async def setup_hook(self):
        self.load_config_from_db()
        if not hasattr(self.config, "guild_id"):
            raise RuntimeError("guild_id is a required parameter")
        self.load_elems_from_db("select id from voice_watch_list", "id", self.config.voice_watch_list)
        self.load_elems_from_db("select id from here_allowed_channels", "id", self.config.here_allowed_channels)
        self.load_dict_from_db("select emoji_id,message from emoji_reacts", "emoji_id", "message", self.config.emoji_reacts)
        for extension in self.config.initial_extensions:
            mod = import_module(f"extensions.{extension}")
            if hasattr(mod, "setup"):
                await mod.setup(self)
            logger.info("Loaded extension %s.py", extension)
        umbra_guild = discord.Object(id=self.config.guild_id)
        self.tree.copy_global_to(guild=umbra_guild)
        await self.tree.sync(guild=umbra_guild)

    async def on_ready(self):
        self.config.launch_time = int(datetime.now().timestamp())
        del self.config.token
        logger.info("%s (id: %s) logged in !", client.user.name, client.user.id)
        for extension in self.config.initial_extensions:
            mod = import_module(f"extensions.{extension}")
            if hasattr(mod, "on_ready") and callable(getattr(mod, "on_ready")):
                await mod.on_ready(self)


custom_intents = discord.Intents.default()
custom_intents.message_content = True
custom_intents.reactions = True
exts = ["general", "moderation", "voice", "settings", "reactions"]
client = UmbraClient(intents=custom_intents, initial_extensions=exts, config=dotenv_values(".env"))


@client.tree.error
async def on_tree_error(interaction, error):
    if isinstance(error, discord.app_commands.CheckFailure):
        await interaction.response.send_message(":exclamation: Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        await interaction.response.send_message(":exclamation: Une erreur est survenue.", ephemeral=True)
        await client.change_presence(status=discord.Status.idle)
        logger.error("[on_app_command_error] %s: %s", type(error).__name__, error)
        traceback.print_exc()

@client.event
async def on_error(event, *args, **kwargs):
    await client.change_presence(status=discord.Status.dnd)
    logger.error("[on_error] %s: %s", event, traceback.print_exc())

@client.event
async def on_interaction(interaction):
    if client.config.debug is True and hasattr(interaction.command, "name"):
        logger.info("DEBUG: User %s (%s) used interaction %s", interaction.user.name, interaction.user.id, interaction.command.name)


if __name__ == "__main__":
    client.run(client.config.token)
