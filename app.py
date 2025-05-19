# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

import discord, logging, logging.handlers, traceback
from dotenv import dotenv_values
from dbOperations import dbOperations
from typing import List, Dict
from importlib import import_module


logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename=f"{__file__}.log",
    encoding='utf-8',
    maxBytes=32*1024*1024,
    backupCount=5
)
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', '%Y-%m-%d %H:%M:%S', style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)


class UmbraClientConfig:
    def __init__(self, initial_extensions: List[str], config: dict):
        self.initial_extensions = initial_extensions
        self.dbname = config.get('dbname', 'umbra')
        self.dbuser = config.get('dbuser', 'root')
        self.dbpass = config.get('dbpass', '')
        self.dbhost = config.get('dbhost', '127.0.0.1')
        self.dbport = int(config.get('dbport', '3306'))
        self.token = config.get('token', None)
        self.temp_voice_list = []
        self.voice_watch_list = []
        self.here_allowed_channels = []
        self.emoji_reacts = {}


class UmbraClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, initial_extensions: List[str], config):
        super().__init__(intents=intents)
        self.config = UmbraClientConfig(initial_extensions, config)
        self.tree = discord.app_commands.CommandTree(self)

    def load_config_from_db(self):
        query = dbOperations.query_db(dbOperations.get_db(self.config), 'select skey, svalue from settings')
        for elem in query:
            setattr(self.config, elem['skey'], elem['svalue'])

    def load_elems_from_db(self, query: str, elem_name: str, list: List[int]):
        query = dbOperations.query_db(dbOperations.get_db(self.config), query)
        for elem in query:
            list.append(int(elem[elem_name]))

    def load_dict_from_db(self, query: str, key: str, value: str, dict: Dict[int, str]):
        query = dbOperations.query_db(dbOperations.get_db(self.config), query)
        for elem in query:
            dict.update({str(elem[key]): elem[value]})

    def check_user_has_rights(self, interaction: discord.Interaction):
        if hasattr(self.config, 'manager_id'):
            return any([interaction.user.guild_permissions.administrator, any(role.id == int(self.config.manager_id) for role in interaction.user.roles)])
        else:
            return interaction.user.guild_permissions.administrator

    async def setup_hook(self):
        self.load_config_from_db()
        if not self.config.guild_id:
            raise Exception("guild_id is a required parameter")
        self.load_elems_from_db('select id from voice_watch_list', 'id', self.config.voice_watch_list)
        self.load_elems_from_db('select id from here_allowed_channels', 'id', self.config.here_allowed_channels)
        self.load_dict_from_db('select emoji_id,message from emoji_reacts', 'emoji_id', 'message', self.config.emoji_reacts)
        for extension in self.config.initial_extensions:
            mod = import_module(f"extensions.{extension}")
            if hasattr(mod, 'setup'):
                await mod.setup(self)
            logger.info(f"Loaded extension {extension}.py")
        umbra_guild = discord.Object(id=self.config.guild_id)
        self.tree.copy_global_to(guild=umbra_guild)
        await self.tree.sync(guild=umbra_guild)

    async def on_ready(self):
        del self.config.token
        logger.info(f"{client.user.name} (id: {client.user.id}) logged in !")
        for extension in self.config.initial_extensions:
            mod = import_module(f"extensions.{extension}")
            if hasattr(mod, 'on_ready') and callable(getattr(mod, 'on_ready')):
                await mod.on_ready(self)


intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
exts = ['general', 'moderation', 'voice', 'settings', 'reactions']
client = UmbraClient(intents=intents, initial_extensions=exts, config=dotenv_values('.env'))

@client.tree.error
async def on_tree_error(interaction, error):
    if isinstance(error, discord.app_commands.CheckFailure):
        await interaction.response.send_message(":exclamation: Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        await interaction.response.send_message(":exclamation: Une erreur est survenue.", ephemeral=True)
        logger.error(f"[on_app_command_error] {type(error).__name__}: {error}")
        traceback.print_exc()


if __name__ == "__main__":
    client.run(client.config.token)