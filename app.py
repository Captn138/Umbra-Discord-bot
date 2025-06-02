"""
app.py (Umbra-Discord-Bot)
:license: AGPL-3.0,see LICENSE for details

This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later.

Main file for the creation of the Discord application.
"""

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
    """
    This class contains base Discord application instance, along with methods that need calling from multiple places.
    
    Attributes
    ----------
    config : utils.UmbraClientConfig
        A custom object to store configurations
    
    Parameters
    ----------
    intents : discord.Intents
        The defined Discord intents for the application
    initial_extensions : List[str]
        An array of extensions to load from the extensions directory
    config : Dict[str, str]
        A dictionary containing configs loaded from a .env file for example
    """
    def __init__(self, *, intents: discord.Intents, initial_extensions: List[str], config: Dict[str, str]):
        super().__init__(intents=intents)
        self.config = UmbraClientConfig(initial_extensions, config)
        self.tree = discord.app_commands.CommandTree(self)

    def load_config_from_db(self, query: str, key: str, value: str):
        """
        Method to load configuration elements from the database to the bot config.
        
        Parameters
        ----------
        query : str
            The query to select the elements
        key : str
            The name of the key element in the query to retrieve 
        value : str
            The name of the value element in the query to retrieve
        """
        query = DbOperations.query_db(DbOperations.get_db(self.config), query)
        for elem in query:
            setattr(self.config, elem[key], elem[value])

    def load_elems_from_db(self, query: str, elem_name: str, target_list: List[int]):
        """
        Method to load configuration elements from the database to a config list.
        
        Parameters
        ----------
        query : str
            The query to select the elements
        elem_name : str
            The mane of the element in the query to retrieve
        target_list : List[int]
            The target list in which to store data
        """
        query = DbOperations.query_db(DbOperations.get_db(self.config), query)
        for elem in query:
            target_list.append(int(elem[elem_name]))

    def load_dict_from_db(self, query: str, key: str, value: str, target_dict: Dict[str, str]):
        """
        Method to load configuration elements from the database to a config dict.
        
        Parameters
        ----------
        query : str
            The query to select the elements
        key : str
            The name of the key element in the query to retrieve 
        value : str
            The name of the value element in the query to retrieve
        target_dict : Disct[str, str]
            The target dict in which to store data
        """
        query = DbOperations.query_db(DbOperations.get_db(self.config), query)
        for elem in query:
            target_dict.update({str(elem[key]): elem[value]})

    def check_user_has_rights(self, interaction: discord.Interaction):
        """
        Method to check if the user interacting with the application has elevated rights.
        Rights include :
        - Being administrator of the guild
        - Having the manager role assigned (if defined)
        
        This method is written as a discord.app_commands.check and its parameters should not be modified.
        
        Parameters
        ----------
        interaction : discord.Interaction
            The interaction from which the rights are to be checked
        """
        if hasattr(self.config, "manager_id"):
            return any([interaction.user.guild_permissions.administrator, any(role.id == int(self.config.manager_id) for role in interaction.user.roles)])
        return interaction.user.guild_permissions.administrator

    async def setup_hook(self):
        """
        Method run to setup the Discord application, overridden from discord.Client.
        """
        self.load_config_from_db("select skey, svalue from settings", "skey", "svalue")
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
        """
        Method run when the Discord application has finished setupping, overridden from discord.Client.
        """
        self.config.launch_time = int(datetime.now().timestamp())
        del self.config.token
        logger.info("%s (id: %s) logged in !", self.user.name, self.user.id)
        for extension in self.config.initial_extensions:
            mod = import_module(f"extensions.{extension}")
            if hasattr(mod, "on_ready") and callable(getattr(mod, "on_ready")):
                await mod.on_ready(self)
        if self.config.game:
            game = discord.Game(self.config.game)
            await self.change_presence(activity=game)


custom_intents = discord.Intents.default()
custom_intents.message_content = True
custom_intents.reactions = True
exts = ["general", "moderation", "voice", "settings", "reactions"]
client = UmbraClient(intents=custom_intents, initial_extensions=exts, config=dotenv_values(".env"))


@client.tree.error
async def on_tree_error(interaction, error):
    """
    Function run when the Discord application encounters an Exception during an interaction runtime.
    """
    if isinstance(error, discord.app_commands.CheckFailure):
        await interaction.response.send_message(":exclamation: Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        await interaction.response.send_message(":exclamation: Une erreur est survenue.", ephemeral=True)
        if client.status == discord.Status.online:
            await client.change_presence(status=discord.Status.idle)
        logger.error("[on_tree_error] %s: %s", type(error).__name__, error)
        traceback.print_exc()

@client.event
async def on_error(event, *args, **kwargs): # pylint: disable=W0613
    """
    Function run when the Discord application encounters an Exception not during an interaction runtime, overridden from discord.Client.
    """
    await client.change_presence(status=discord.Status.dnd)
    logger.error("[on_error] %s: %s", event, traceback.print_exc())

@client.event
async def on_interaction(interaction):
    """
    Function run when any interaction ends, overridden from discord.Client.
    """
    if client.config.debug is True and hasattr(interaction.command, "name"):
        logger.info("DEBUG: User %s (%s) used interaction %s", interaction.user.name, interaction.user.id, interaction.command.name)


if __name__ == "__main__":
    client.run(client.config.token)
