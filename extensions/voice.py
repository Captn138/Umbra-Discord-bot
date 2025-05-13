# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


import discord
from random import choice
from dbOperations import dbOperations
from extensions.settings import Confirm


def get_new_voice_channel_name(db):
    query = dbOperations.query_db(db, 'select name from voice_channel_names')
    if not query:
        return "liste vide - contactez la modération"
    list = []
    for elem in query:
        list.append(elem['name'])
    return choice(list)

async def setup(client):
    @client.event
    async def on_voice_state_update(member, before, after):
        if after.channel and after.channel.id in client.config.voice_watch_list:
            guild = after.channel.guild
            new_channel = await guild.create_voice_channel(
                name=get_new_voice_channel_name(client.config.db),
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
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="delete_voice", value="delete_voice"),
        discord.app_commands.Choice(name="register_temp_voice", value="register_temp_voice")
    ])
    async def debug(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: discord.VoiceChannel):
        if not client.check_user_has_rights(interaction.user):
            return
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