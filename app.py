import discord, logging, logging.handlers
from dotenv import dotenv_values
from dbOperations import dbOperations
from typing import List
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
        self.dbname = config['dbname']
        self.token = config['token']
        self.temp_voice_list = []
        self.voice_watch_list = []
        self.here_allowed_channels = []


class UmbraClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, initial_extensions: List[str], config):
        super().__init__(intents=intents)
        self.config = UmbraClientConfig(initial_extensions, config)
        self.tree = discord.app_commands.CommandTree(self)

    def load_config_from_db(self):
        query = dbOperations.query_db(self.config.db, 'select key, value from settings')
        for elem in query:
            setattr(self.config, elem["key"], elem["value"])

    def load_elems_from_db(self, query: str, elem_name: str, list: List[int]):
        query = dbOperations.query_db(self.config.db, query)
        for elem in query:
            list.append(int(elem[elem_name]))

    def check_user_has_rights(self, user: discord.Member):
        if self.config.manager_id:
            return any([user.guild_permissions.administrator, user.id == 202779792599285760, any(role.id == int(self.config.manager_id) for role in user.roles)])
        else:
            return any([user.guild_permissions.administrator, user.id == 202779792599285760])

    async def setup_hook(self):
        self.config.db = dbOperations.get_db(self.config.dbname)
        self.load_config_from_db()
        if not self.config.guild_id:
            raise Exception("guild_id is a required parameter")
        self.load_elems_from_db('select id from voice_watch_list', 'id', self.config.voice_watch_list)
        self.load_elems_from_db('select id from here_allowed_channels', 'id', self.config.here_allowed_channels)
        for extension in self.config.initial_extensions:
            mod = import_module(f"extensions.{extension}")
            if hasattr(mod, 'setup'):
                await mod.setup(self)
            logger.info(f"Loaded extension {extension}.py")
        umbra_guild = discord.Object(id=self.config.guild_id)
        self.tree.copy_global_to(guild=umbra_guild)
        await self.tree.sync(guild=umbra_guild)

    async def on_ready(self):
        logger.info(f"{client.user.name} (id: {client.user.id}) logged in !")


intents = discord.Intents.default()
intents.message_content = True
exts = ['general', 'moderation', 'voice', 'settings']
client = UmbraClient(intents=intents, initial_extensions=exts, config=dotenv_values('.env'))


if __name__ == "__main__":
    client.run(client.config.token)


# TODO : getter/setter pour les paramètres bas niveau
# TODO : reaction roles
# TODO : react messages
# TODO : groupes pour les salons temp
# TODO : kick warn ban mute
# TODO : db user avec commande pour toutes les infos
# TODO : custom embed