"""
extensions/general.py (Umbra-Discord-Bot)
:license: AGPL-3.0,see LICENSE for details

This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later.

General commands for the Discord application.
Can be used by everyone. 
"""

import traceback
from typing import Optional
from datetime import datetime
import discord


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


class Feedback(discord.ui.Modal, title="Feedback"):
    """
    Custom class to store and send a feedback, inherits discord.ui.Modal.
    
    Attributes
    ----------
    report_channel : int
        The channel in which to send the feedback, once completed
    name : discord.ui.TextInput
        The chosen name for the author of the feedback
    feedback : discord.ui.TextInput
        The feedback text
    
    Parameters
    ----------
    report_channel : int
        The channel in which to send the feedback, once completed
    """
    def __init__(self, report_channel: int):
        super().__init__()
        self.report_channel = report_channel

    name = discord.ui.TextInput(
        label="Tag Discord",
        placeholder="Ton tag Discord ici...",
    )
    feedback = discord.ui.TextInput(
        label="Que penses-tu du bot ?",
        style=discord.TextStyle.long,
        placeholder="Tape ton feedback ici...",
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):    # pylint: disable=W0221
        await interaction.response.send_message(f":white_check_mark: Merci pour ton feedback, {self.name.value}!", ephemeral=True)
        log_channel = interaction.guild.get_channel(self.report_channel)
        embed = discord.Embed(colour=discord.Colour.blue(), title="Feedback")
        embed.description = self.feedback.value
        embed.set_author(name=self.name.value)
        embed.timestamp = interaction.created_at
        url_view = discord.ui.View()
        await log_channel.send(embed=embed, view=url_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:   # pylint: disable=W0221
        await interaction.response.send_message(":exclamation: Oups! Quelque chose a mal tourné.", ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)


async def setup(client):
    """
    Function run when module loaded as an extension.
    """
    @client.tree.command(description="Bonjour !")
    async def hello(interaction: discord.Interaction):
        """
        Simple commands that answers the user.
        """
        await interaction.response.send_message(f"Salut, {interaction.user.mention} !", ephemeral=True)

    @client.tree.command(description="Envoyer un feedback")
    async def feedback(interaction: discord.Interaction):
        """
        Command to send a feedback.
        """
        await interaction.response.send_modal(Feedback(int(client.config.report_channel)))

    @client.tree.command(description="Mentionner here avec un message personnalisé")
    async def here(interaction: discord.Interaction, message: str):
        """
        Command to send @here in a channel.
        Will also send a mention of the author, their voice channel if available and a custom message.
        
        Parameters
        ----------
        message : str
            The custom message to send
        """
        if interaction.channel_id in client.config.here_allowed_channels:
            if "@everyone" in message or "@here" in message:
                await interaction.response.send_message(":exclamation: Tu ne peux pas mentionner everyone ou here dans ton message.", ephemeral=True)
                return
            try:
                voice_status = await interaction.user.fetch_voice()
            except discord.NotFound:
                voice_status = None
            if not voice_status or not voice_status.channel:
                await interaction.response.send_message(f"@here\nDe {interaction.user.mention} : {message}", allowed_mentions=discord.AllowedMentions(everyone=True))
            else:
                await interaction.response.send_message(f"@here\nDe {interaction.user.mention} dans <#{voice_status.channel.id}>: {message}", allowed_mentions=discord.AllowedMentions(everyone=True))

    @client.tree.command(name="help", description="Affiche l'aide pour une commande")
    @discord.app_commands.describe(command="Commande à propos de laquelle afficher l'aide")
    async def help_command(interaction: discord.Interaction, command: Optional[str] = None):
        """
        Command to list description of all possible interactions with the application.
        Dynamically shows commands based on the user rights.
        
        Parameters
        ----------
        command : Optional[str]
            optional name of the interaction to get more details about
        """
        chat_commands = client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.chat_input)
        if command:
            embed = discord.Embed(colour=discord.Colour.blurple(), title="Aide commande")
            for cmd in chat_commands:
                if cmd.name == command and (not cmd.checks or client.check_user_has_rights(interaction)):
                    embed.add_field(name="", value=f"**/{cmd.name}** : {cmd.description}", inline=False)
            if embed.fields:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(":exclamation: Cette commande n'existe pas ou tu n'y as pas accès", ephemeral=True)
        else:
            userembed = discord.Embed(colour=discord.Colour.blurple(), title="Commandes utilisateur")
            modoembed = discord.Embed(colour=discord.Colour.brand_red(), title="Commandes modérateurs")
            modoembed.description = "Commandes réservées aux utilisateurs disposant des droits de gestion"
            appembed = discord.Embed(colour=discord.Colour.blurple(), title="Interaction application")
            for cmd in chat_commands:
                if cmd.checks:
                    modoembed.add_field(name="", value=f"**/{cmd.name}** : {cmd.description}", inline=False)
                else:
                    userembed.add_field(name="", value=f"**/{cmd.name}** : {cmd.description}", inline=False)
            for inter in client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.user):
                appembed.add_field(name="En interagissant avec un utilisateur", value=f"{inter.name}", inline=False)
            for inter in client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.message):
                appembed.add_field(name="En interagissant avec un message", value=f"{inter.name}", inline=False)
            embedslist = []
            if userembed.fields:
                embedslist.append(userembed)
            if modoembed.fields and client.check_user_has_rights(interaction):
                embedslist.append(modoembed)
            if appembed.fields:
                embedslist.append(appembed)
            await interaction.response.send_message(embeds=embedslist, ephemeral=True)

    @help_command.autocomplete("command")
    async def help_autocomplete(interaction: discord.Interaction, current: str):
        """
        Auto completer for the help command.
        """
        chat_commands = client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.chat_input)
        return [
            discord.app_commands.Choice(name=cmd.name, value=cmd.name)
            for cmd in chat_commands
            if current.lower() in cmd.name.lower() and (not cmd.checks or client.check_user_has_rights(interaction))
        ]

    @client.tree.command(description="Affiche les infos du bot")
    async def botinfo(interaction: discord.Interaction):
        """
        Command to get some publicly available information about the application.
        """
        embed = discord.Embed(colour=discord.Colour.blurple(), title=f"Infos {client.user.name}")
        embed.add_field(name="En ligne depuis", value=discord.utils.format_dt(datetime.fromtimestamp(client.config.launch_time)), inline=False)
        application_info = await client.application_info()
        embed.add_field(name="Propriétaire", value=application_info.owner.mention, inline=False)
        embed.add_field(name="Version", value=client.config.version, inline=False)
        embed.add_field(name="Code source", value=client.config.source, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
