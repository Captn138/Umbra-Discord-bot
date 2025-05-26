"""
extensions/voice.py (Umbra-Discord-Bot)
:license: AGPL-3.0,see LICENSE for details

This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later.

Temporary voice channel module for the Discord application. 
"""

from random import choice
import discord
from utils import DbOperations
from extensions.settings import Confirm


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


def get_new_voice_channel_name(db):
    """
    Gets a random temporary voice channel name from MariaDB
    
    Parameters
    ----------
    db : mariadb.connections.Connection
        The connexion to MariaDB
    
    Returns
    -------
    str
        The randomly chosen name among all candidates in MariaDB
    """
    query = DbOperations.query_db(db, "select name from voice_channel_names")
    if not query:
        return "liste vide - contactez la modération"
    names_list = []
    for elem in query:
        names_list.append(elem["name"])
    return choice(names_list)


async def setup(client):
    """
    Function run when module loaded as an extension.
    """
    @client.event
    async def on_voice_state_update(member, before, after):
        """
        Method run when a user changes their voice status, overridden from discord.Client.
        If the user lands in a watched channel, creates a new temporary voice channel and moves the user.
        The the user leaves a temporary channel and was the last user from that channel, deletes the channel.
        """
        if after.channel and after.channel.id in client.config.voice_watch_list:
            guild = after.channel.guild
            new_channel = await guild.create_voice_channel(
                name=get_new_voice_channel_name(DbOperations.get_db(client.config)),
                overwrites=after.channel.overwrites,
                category=after.channel.category
            )
            client.config.temp_voice_list.append(new_channel.id)
            await member.move_to(new_channel)
        if before.channel and before.channel.id in client.config.temp_voice_list:
            if len(before.channel.members) == 0:
                await before.channel.delete()
                client.config.temp_voice_list.remove(before.channel.id)

    @client.tree.command(description="Commandes de debug")
    @discord.app_commands.check(client.check_user_has_rights)
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="delete_voice", value="delete_voice"),
        discord.app_commands.Choice(name="register_temp_voice", value="register_temp_voice")
    ])
    async def debug(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: discord.VoiceChannel):
        """
        Debug commands for when the application has to restart while temporary voice channels are active.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        """
        match operation.value:
            case "delete_voice":
                view = Confirm()
                await interaction.response.send_message(f":exclamation: Si vous continuez, `{channel.name}` sera supprimé. Continuer ?", ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    await channel.delete()
            case "register_temp_voice":
                view = Confirm()
                await interaction.response.send_message(f":exclamation: Si vous continuez, `{channel.name}` sera défini comme salon temporaire. Continuer ?", ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    client.config.temp_voice_list.append(channel.id)
