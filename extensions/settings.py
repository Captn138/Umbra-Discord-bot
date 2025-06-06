"""
extensions/settings.py (Umbra-Discord-Bot)
:license: AGPL-3.0,see LICENSE for details

This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later.

Settings getters/setters for the Discord application. 
"""

import re
from typing import List, Dict, Optional
import discord
import emoji as em
from utils import DbOperations


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


class Confirm(discord.ui.View):
    """
    Custom class to ask for confirmation, inherits discord.ui.View.
    
    Attributes
    ----------
    value : bool
        The value of the confirmation
    """
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):   # pylint: disable=W0613
        """Confirm action"""
        self.value = True
        await interaction.response.send_message(":white_check_mark: Action confirmée.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):    # pylint: disable=W0613
        """Cancel action"""
        self.value = False
        await interaction.response.send_message(":exclamation: Action refusée.", ephemeral=True)
        self.stop()


class DropdownRemoveEmojiReacts(discord.ui.Select):
    """
    Custom class to remove an emoji reaction, inherits discord.ui.Select.
    
    Attributes
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    config_list : Dict[str, str]
        The dictionary containing all the emoji reactions
    
    Parameters
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    config_list : Dict[str, str]
        The dictionary containing all the emoji reactions
    choices_list : List[discord.SelectOption]
        The list of choices
    """
    def __init__(self, db, config_list: Dict[str, str], choices_list: List[discord.SelectOption]):
        super().__init__(placeholder="Choisissez une valeur ...", min_values=1, max_values=1, options=choices_list)
        self.db = db
        self.config_list = config_list

    async def callback(self, interaction: discord.Interaction):
        DbOperations.query_db(self.db, "delete from emoji_reacts where emoji_id = ?", [self.values[0]])
        del self.config_list[self.values[0]]
        await interaction.response.send_message(":white_check_mark: Emoji retiré de la liste des réactions d'emojis", ephemeral=True)


class DropdownRemoveHereChannel(discord.ui.Select):
    """
    Custom class to remove a here channel, inherits discord.ui.Select.
    
    Attributes
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    config_list : List[int]
        The list containing all the here channels IDs
    
    Parameters
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    config_list : List[int]
        The list containing all the here channels IDs
    choices_list : List[discord.SelectOption]
        The list of choices
    """
    def __init__(self, db, config_list: List[int], choices_list: List[discord.SelectOption]):
        super().__init__(placeholder="Choisissez une valeur ...", min_values=1, max_values=1, options=choices_list)
        self.db = db
        self.config_list = config_list

    async def callback(self, interaction: discord.Interaction):
        DbOperations.query_db(self.db, "delete from here_allowed_channels where id = ?", [self.values[0]])
        self.config_list.remove(int(self.values[0]))
        await interaction.response.send_message(":white_check_mark: Salon retiré de la liste des salons here", ephemeral=True)


class DropdownRemoveTempName(discord.ui.Select):
    """
    Custom class to remove a temporaty voice channel name, inherits discord.ui.Select.
    
    Attributes
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    
    Parameters
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    choices_list : List[discord.SelectOption]
        The list of choices
    """
    def __init__(self, db, choices_list: List[discord.SelectOption]):
        super().__init__(placeholder="Choisissez une valeur ...", min_values=1, max_values=1, options=choices_list)
        self.db = db

    async def callback(self, interaction: discord.Interaction):
        DbOperations.query_db(self.db, "delete from voice_channel_names where name = ?", [self.values[0]])
        await interaction.response.send_message(":white_check_mark: Nom de salon vocal temporaire supprimé", ephemeral=True)


class DropdownRemoveWatchedChannel(discord.ui.Select):
    """
    Custom class to remove a here channel, inherits discord.ui.Select.
    
    Attributes
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    config_list : List[int]
        The list containing all the watched channels IDs
    
    Parameters
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    config_list : List[int]
        The list containing all the watched channels IDs
    choices_list : List[discord.SelectOption]
        The list of choices
    """
    def __init__(self, db, config_list: List[int], choices_list: List[discord.SelectOption]):
        super().__init__(placeholder="Choisissez une valeur ...", min_values=1, max_values=1, options=choices_list)
        self.db = db
        self.config_list = config_list

    async def callback(self, interaction: discord.Interaction):
        DbOperations.query_db(self.db, "delete from voice_watch_list where id = ?", [self.values[0]])
        self.config_list.remove(int(self.values[0]))
        await interaction.response.send_message(":white_check_mark: Salon retiré de la liste de création de salons", ephemeral=True)


class DropdownView(discord.ui.View):
    """
    Custom dropdown class, inherits discord.ui.View.
    
    Parameters
    ----------
    dropdown : discord.ui.Select
        The custom dropdown selection
    """
    def __init__(self, dropdown: discord.ui.Select):
        super().__init__()
        self.add_item(dropdown)


async def setup(client):
    """
    Function run when module loaded as an extension.
    """
    @client.tree.command(description="Gérer les salons de la liste de création de salons")
    @discord.app_commands.check(client.check_user_has_rights)
    @discord.app_commands.describe(channel="Salon vocal requis si operation = add")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="add", value="add"),
        discord.app_commands.Choice(name="remove", value="remove"),
        discord.app_commands.Choice(name="purge", value="purge"),
        discord.app_commands.Choice(name="print", value="print")
    ])
    async def watched_channel(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: Optional[discord.VoiceChannel] = None):
        """
        Manages the watched channels.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        operation : discord.app_commands.Choice[str]
            The operation to perform among add, remove, print, purge
        channel : Optional[discord.VoiceChannel]
            The optional voice channel, only needed for add operation
        """
        match operation.value:
            case "add":
                if not channel:
                    await interaction.response.send_message(":exclamation: Un salon vocal est requis", ephemeral=True)
                elif channel.id in client.config.voice_watch_list:
                    await interaction.response.send_message(f":warning: `{channel.name}` appartient déjà à la liste de création de salons", ephemeral=True)
                else:
                    DbOperations.query_db(DbOperations.get_db(client.config), "insert into voice_watch_list (id) values ( ? )", [channel.id])
                    client.config.voice_watch_list.append(channel.id)
                    await interaction.response.send_message(f":white_check_mark: `{channel.name}` ajouté à la liste de création de salons", ephemeral=True)
            case "remove":
                if not client.config.voice_watch_list:
                    await interaction.response.send_message(":warning: La liste de création de salons est vide", ephemeral=True)
                else:
                    choices_list = []
                    for channel_id in client.config.voice_watch_list:
                        choices_list.append(discord.SelectOption(label=interaction.guild.get_channel(channel_id).name, value=channel_id))
                    view = DropdownView(DropdownRemoveWatchedChannel(DbOperations.get_db(client.config), client.config.voice_watch_list, choices_list))
                    await interaction.response.send_message("Choisissez salon à supprimer de la liste de création de salons :", ephemeral=True, view=view)
            case "purge":
                view = Confirm()
                await interaction.response.send_message(":exclamation: Si vous continuez, tous les salons seront retirés de la liste de création de salons. Continuer ?", ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from voice_watch_list")
                    client.config.voice_watch_list = []
            case "print":
                if not client.config.voice_watch_list:
                    await interaction.response.send_message(":warning: La liste de création de salons est vide", ephemeral=True)
                else:
                    msg = "Voici la liste de création de salons :\n"
                    for channel_id in client.config.voice_watch_list:
                        msg += f"- <#{channel_id}>\n"   # pylint: disable=R1713
                    await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Gérer les salons vocaux temporaires")
    @discord.app_commands.check(client.check_user_has_rights)
    @discord.app_commands.describe(name="Nom requis si operation = add")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="add", value="add"),
        discord.app_commands.Choice(name="remove", value="remove"),
        discord.app_commands.Choice(name="purge", value="purge"),
        discord.app_commands.Choice(name="print", value="print")
    ])
    async def temp_name(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], name: Optional[str] = None):
        """
        Manages the temporary voice channels names.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        operation : discord.app_commands.Choice[str]
            The operation to perform among add, remove, print, purge
        name : Optional[str]
            The optional temporary voice channel name, only needed for add operation
        """
        match operation.value:
            case "add":
                if not name:
                    await interaction.response.send_message(":exclamation: Un nom est requis", ephemeral=True)
                else:
                    DbOperations.query_db(DbOperations.get_db(client.config), "insert into voice_channel_names (name) values ( ? )", [name])
                    await interaction.response.send_message(f":white_check_mark: `{name}` ajouté à la liste des noms de salons vocaux temporaires", ephemeral=True)
            case "remove":
                query = DbOperations.query_db(DbOperations.get_db(client.config), "select name from voice_channel_names")
                if not query:
                    await interaction.response.send_message(":warning: La liste des noms de salons vocaux temporaires est vide", ephemeral=True)
                else:
                    choices_list = []
                    for elem in query:
                        choices_list.append(discord.SelectOption(label=elem["name"]))
                    view = DropdownView(DropdownRemoveTempName(DbOperations.get_db(client.config), choices_list))
                    await interaction.response.send_message("Choisissez le nom de salon vocal temporaire à supprimer :", ephemeral=True, view=view)
            case "purge":
                view = Confirm()
                await interaction.response.send_message(":exclamation: Si vous continuez, tous les noms seront retirés de la liste de noms de salons vocaux temporaires. Continuer ?", ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from voice_channel_names")
            case "print":
                query = DbOperations.query_db(DbOperations.get_db(client.config), "select name from voice_channel_names")
                if not query:
                    await interaction.response.send_message(":warning: La liste des noms de salons vocaux temporaires est vide", ephemeral=True)
                else:
                    msg = "Voici la liste des noms de salons vocaux temporaires :\n"
                    for elem in query:
                        msg += f"- {elem['name']}\n"
                    await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Gérer les salons de la liste des salons here")
    @discord.app_commands.check(client.check_user_has_rights)
    @discord.app_commands.describe(channel="Salon requis si operation = add")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="add", value="add"),
        discord.app_commands.Choice(name="remove", value="remove"),
        discord.app_commands.Choice(name="purge", value="purge"),
        discord.app_commands.Choice(name="print", value="print")
    ])
    async def here_channel(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: Optional[discord.TextChannel] = None):
        """
        Manages the here channels.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        operation : discord.app_commands.Choice[str]
            The operation to perform among add, remove, print, purge
        channel : Optional[discord.TextChannel]
            The optional text channel, only needed for add operation
        """
        match operation.value:
            case "add":
                if not channel:
                    await interaction.response.send_message(":exclamation: Un salon est requis", ephemeral=True)
                elif channel.id in client.config.here_allowed_channels:
                    await interaction.response.send_message(f":warning: `{channel.name}` appartient déjà à la liste des salons here", ephemeral=True)
                else:
                    DbOperations.query_db(DbOperations.get_db(client.config), "insert into here_allowed_channels (id) values ( ? )", [channel.id])
                    client.config.here_allowed_channels.append(channel.id)
                    await interaction.response.send_message(f":white_check_mark: `{channel.name}` ajouté à la liste des salons here", ephemeral=True)
            case "remove":
                if not client.config.here_allowed_channels:
                    await interaction.response.send_message(":warning: La liste des salons here est vide", ephemeral=True)
                else:
                    choices_list = []
                    for channel_id in client.config.here_allowed_channels:
                        choices_list.append(discord.SelectOption(label=interaction.guild.get_channel(channel_id).name, value=channel_id))
                    view = DropdownView(DropdownRemoveHereChannel(DbOperations.get_db(client.config), client.config.here_allowed_channels, choices_list))
                    await interaction.response.send_message("Choisissez le salon à supprimer de la liste des salons here :", ephemeral=True, view=view)
            case "purge":
                view = Confirm()
                await interaction.response.send_message(":exclamation: Si vous continuez, tous les salons seront retirés de la liste des salons here. Continuer ?", ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from here_allowed_channels")
                    client.config.here_allowed_channels = []
            case "print":
                if not client.config.here_allowed_channels:
                    await interaction.response.send_message(":warning: La liste des salons here est vide", ephemeral=True)
                else:
                    msg = "Voici la liste des salons here :\n"
                    for channel_id in client.config.here_allowed_channels:
                        msg += f"- <#{channel_id}>\n"   # pylint: disable=R1713
                    await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Gérer le rôle de manager")
    @discord.app_commands.check(client.check_user_has_rights)
    @discord.app_commands.describe(role="Rôle requis si operation = set")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="get", value="get"),
        discord.app_commands.Choice(name="set", value="set"),
        discord.app_commands.Choice(name="unset", value="unset")
    ])
    async def manager(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], role: Optional[discord.Role] = None):
        """
        Manages the manager role.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        operation : discord.app_commands.Choice[str]
            The operation to perform among get, set, unset
        role : Optional[discord.Role]
            The optional manager role, only needed for set operation
        """
        match operation.value:
            case "get":
                if not hasattr(client.config, "manager_id"):
                    await interaction.response.send_message(":warning: Le rôle de manager n'est pas défini", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Le rôle de manager est : {interaction.guild.get_role(int(client.config.manager_id)).mention}", ephemeral=True)
            case "set":
                if not role:
                    await interaction.response.send_message(":exclamation: Un rôle est requis", ephemeral=True)
                else:
                    client.config.manager_id = str(role.id)
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from settings where skey = 'manager_id'")
                    DbOperations.query_db(DbOperations.get_db(client.config), "insert into settings (skey, svalue) values ('manager_id', ? )", [role.id])
                    await interaction.response.send_message(f":white_check_mark: {role.mention} est le nouveau rôle de manager", ephemeral=True)
            case "unset":
                if not hasattr(client.config, "manager_id"):
                    await interaction.response.send_message(":warning: Le rôle de manager n'est pas défini", ephemeral=True)
                else:
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from settings where skey = 'manager_id'")
                    del client.config.manager_id
                    await interaction.response.send_message(":white_check_mark: Le rôle de manager à été désattribué", ephemeral=True)

    @client.tree.command(description="Gérer le salon de report")
    @discord.app_commands.check(client.check_user_has_rights)
    @discord.app_commands.describe(channel="Salon requis si operation = set")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="get", value="get"),
        discord.app_commands.Choice(name="set", value="set"),
        discord.app_commands.Choice(name="unset", value="unset")
    ])
    async def report_channel(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: Optional[discord.TextChannel] = None):
        """
        Manages the report channel.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        operation : discord.app_commands.Choice[str]
            The operation to perform among get, set, unset
        channel : Optional[discord.TextChannel]
            The optional text channel, only needed for set operation
        """
        match operation.value:
            case "get":
                if not hasattr(client.config, "report_channel"):
                    await interaction.response.send_message(":warning: Le salon de report n'est pas défini", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Le salon de report est : {interaction.guild.get_channel(int(client.config.report_channel)).mention}", ephemeral=True)
            case "set":
                if not channel:
                    await interaction.response.send_message(":exclamation: Un salon est requis", ephemeral=True)
                else:
                    client.config.report_channel = str(channel.id)
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from settings where skey = 'report_channel'")
                    DbOperations.query_db(DbOperations.get_db(client.config), "insert into settings (skey, svalue) values ('report_channel', ? )", [channel.id])
                    await interaction.response.send_message(f":white_check_mark: {channel.mention} est le nouveau salon de report", ephemeral=True)
            case "unset":
                if not hasattr(client.config, "report_channel"):
                    await interaction.response.send_message(":warning: Le salon de report n'est pas défini", ephemeral=True)
                else:
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from settings where skey = 'report_channel'")
                    del client.config.report_channel
                    await interaction.response.send_message(":white_check_mark: Le salon de report à été désattribué", ephemeral=True)

    @client.tree.command(description="Gérer les réactions d'emojis")
    @discord.app_commands.check(client.check_user_has_rights)
    @discord.app_commands.describe(emoji="Emoji requis si operation = add")
    @discord.app_commands.describe(message="Message requis si operation = add")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="add", value="add"),
        discord.app_commands.Choice(name="remove", value="remove"),
        discord.app_commands.Choice(name="purge", value="purge"),
        discord.app_commands.Choice(name="print", value="print")
    ])
    async def emoji_reactions(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], emoji: Optional[str] = None, message: Optional[str] = None):
        """
        Manages the emoji reactions.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        operation : discord.app_commands.Choice[str]
            The operation to perform among add, remove, print, purge
        emoji : Optional[str]
            The emoji to trigger a message, only needed for add operation
        message : Optional[str]
            The message triggered by the emoji, only needed for add operation
        """
        match operation.value:
            case "add":
                if not emoji or not message:
                    await interaction.response.send_message(":exclamation: Un emoji et un message sont requis", ephemeral=True)
                elif re.compile(r"^<a?:\w+:\d+>$").match(emoji) or emoji in em.EMOJI_DATA:
                    for emoji_id, msg in client.config.emoji_reacts.items():
                        if emoji_id == emoji:
                            await interaction.response.send_message(f":warning: {emoji} appartient déjà à la liste des réactions d'emojis", ephemeral=True)
                            return
                    DbOperations.query_db(DbOperations.get_db(client.config), "insert into emoji_reacts (emoji_id,message) values ( ?, ? )", [emoji, message])
                    client.config.emoji_reacts.update({emoji: message})
                    await interaction.response.send_message(f":white_check_mark: {emoji} ajouté à la liste des réactions d'emojis", ephemeral=True)
                else:
                    await interaction.response.send_message(":exclamation: Emoji invalide", ephemeral=True)
            case "remove":
                if not client.config.emoji_reacts:
                    await interaction.response.send_message(":warning: La liste des réactions d'emojis est vide", ephemeral=True)
                else:
                    choices_list = []
                    for emoji_id, text in client.config.emoji_reacts.items():
                        choices_list.append(discord.SelectOption(label=emoji_id, value=emoji_id))
                    view = DropdownView(DropdownRemoveEmojiReacts(DbOperations.get_db(client.config), client.config.emoji_reacts, choices_list))
                    await interaction.response.send_message("Choisissez l'emoji à supprimer de la liste des réactions d'emojis :", ephemeral=True, view=view)
            case "purge":
                view = Confirm()
                await interaction.response.send_message(":exclamation: Si vous continuez, tous les emojis seront retirés de la liste des réactions d'emojis. Continuer ?", ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    DbOperations.query_db(DbOperations.get_db(client.config), "delete from emoji_reacts")
                    client.config.emoji_reacts = {}
            case "print":
                if not client.config.emoji_reacts:
                    await interaction.response.send_message(":warning: La liste des réactions d'emojis est vide", ephemeral=True)
                else:
                    msg = "Voici la liste des réactions d'emojis :\n"
                    for emoji_id, text in client.config.emoji_reacts.items():
                        msg += f"- {emoji_id} : {text}\n"
                    await interaction.response.send_message(msg, ephemeral=True)
