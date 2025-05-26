"""
extensions/moderation.py (Umbra-Discord-Bot)
:license: AGPL-3.0,see LICENSE for details

This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later.

Moderation commands and functions for the Discord application. 
"""

from typing import List, Optional
from datetime import datetime, timedelta
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils import DbOperations


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


class UserReport(discord.ui.Modal, title="Signalement"):
    """
    Custom class to store and send a user report, inherits discord.ui.Modal.
    
    Attributes
    ----------
    report_channel : int
        The channel in which to send the feedback, once completed
    user : discord.Member
        The reporting user
    target : discord.Member
        The reported user
    reason : discord.ui.TextInput
        The reason of the report
    
    Parameters
    ----------
    report_channel : int
        The channel in which to send the feedback, once completed
    user : discord.Member
        The reporting user
    target : discord.Member
        The reported user
    """
    def __init__(self, report_channel: int, user: discord.Member, target: discord.Member):
        super().__init__()
        self.report_channel = report_channel
        self.user = user
        self.target = target

    reason = discord.ui.TextInput(
        label="Raison du signalement",
        style=discord.TextStyle.long,
        placeholder="Tape ici...",
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):    # pylint: disable=W0221
        await interaction.response.send_message(f":white_check_mark: Merci pour ton signalement, {self.user.name}!", ephemeral=True)
        log_channel = interaction.guild.get_channel(self.report_channel)
        embed = discord.Embed(colour=discord.Colour.dark_red(), title="Utilisateur signalé")
        embed.description = f"{self.user.mention} signale {self.target.mention} :\n{self.reason.value}"
        embed.timestamp = interaction.created_at
        url_view = discord.ui.View()
        await log_channel.send(embed=embed, view=url_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:   # pylint: disable=W0221
        await interaction.response.send_message(":exclamation: Oups! Quelque chose a mal tourné.", ephemeral=True)


async def on_ready(self):
    """
    Function run when the module has been loaded by the application.
    """
    self.scheduler.start()


async def setup(client):
    """
    Function run when module loaded as an extension.
    """
    async def daily_unban():
        """
        Unbans all members whose ban duration has expired.
        Should be run using a scheduler.
        """
        query = DbOperations.query_db(DbOperations.get_db(client.config), "select user,until from infractions where type = 'ban'")
        for elem in query:
            if elem["until"] and datetime.now() > datetime.fromtimestamp(int(elem["until"])):
                user = await client.fetch_user(elem["user"])
                guild = await client.fetch_guild(client.config.guild_id)
                reason = "Levée de sanction automatique"
                DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description) values ( ?, 'unban', ?, ?, ?)", [user.id, int(datetime.now().timestamp()), client.user.id, reason])
                await guild.unban(user, reason=reason)

    @client.tree.command(description="Supprimer des messages")
    @discord.app_commands.check(client.check_user_has_rights)
    async def clear(interaction: discord.Interaction, quantity: int = 1):
        """
        Command to delete a number of messages in a channel.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        quantity : int
            The quantity of messages to remove, defaults to 1
        """
        await interaction.response.send_message(f":arrows_counterclockwise: Suppression de {quantity} messages en cours ...", ephemeral=True)
        await interaction.channel.purge(limit=quantity)

    @client.tree.context_menu(name="Signaler un message")
    async def report_message(interaction: discord.Interaction, message: discord.Message):
        """
        Context action to report a message.
        Can only be interacted from a message.
        """
        if not hasattr(client.config, "report_channel"):
            return
        await interaction.response.send_message(f":white_check_mark: Merci d'avoir signalé ce message de {message.author.mention} à nos modérateurs.", ephemeral=True)
        log_channel = interaction.guild.get_channel(int(client.config.report_channel))
        embed = discord.Embed(colour=discord.Colour.dark_red(), title="Message signalé")
        if message.content:
            embed.description = message.content
        embed.set_author(name=f"Auteur : {message.author.display_name}, ID : {message.author.id}", icon_url=message.author.display_avatar.url)
        embed.timestamp = message.created_at
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label="Aller au message", style=discord.ButtonStyle.url, url=message.jump_url))
        await log_channel.send(embed=embed, view=url_view)

    @client.tree.context_menu(name="Signaler un utilisateur")
    async def report_user(interaction: discord.Interaction, user: discord.Member):
        """
        Context action to report a user.
        Can only be interacted from a user.
        """
        if not hasattr(client.config, "report_channel"):
            return
        await interaction.response.send_modal(UserReport(int(client.config.report_channel), interaction.user, user))

    async def fill_embed_with_infractions(query: List, embed: discord.Embed):
        """
        Dynamically fill an embed with the content of infractions.
        
        Parameters
        ----------
        query : List
            The list of results of the query
        embed : discord.Embed
            The embed to fill
        """
        for elem in query:
            match elem["type"]:
                case "warn":
                    embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] :warning: <@{elem['author']}> {elem['desc'][:30]}", inline=False)
                case "ban":
                    if elem["until"]:
                        embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] :hammer: <@{elem['author']}> {elem['desc'][:30]} - {discord.utils.format_dt(datetime.fromtimestamp(int(elem['until'])), style='d')}", inline=False)
                    else:
                        embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] :hammer: <@{elem['author']}> {elem['desc'][:30]}", inline=False)
                case "unban":
                    embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] :green_square: <@{elem['author']}> {elem['desc'][:30]}", inline=False)
                case "mute":
                    embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] :mute: <@{elem['author']}> {elem['desc'][:30]} - {discord.utils.format_dt(datetime.fromtimestamp(int(elem['until'])), style='d')}", inline=False)
                case "unmute":
                    embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] :loud_sound: <@{elem['author']}> {elem['desc'][:30]}", inline=False)
                case "kick":
                    embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] :door: <@{elem['author']}> {elem['desc'][:30]}", inline=False)

    async def fill_embed_with_notes(query: List, embed: discord.Embed):
        """
        Dynamically fill an embed with the content of notes.
        
        Parameters
        ----------
        query : List
            The list of results of the query
        embed : discord.Embed
            The embed to fill
        """
        for elem in query:
            embed.add_field(name="", value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem['time'])), style='d')} - `{elem['id']:03d}`] <@{elem['author']}> {elem['note']}", inline=False)

    @client.tree.command(description="Obtenir des informations sur un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def userinfo(interaction: discord.Interaction, user: discord.User):
        """
        Command to get all available information about a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.User
            The targeted user, can also be replaced by their ID
        """
        infoembed = discord.Embed(colour=discord.Colour.blurple(), title="Infos utilisateur")
        infoembed.set_author(name=f"{user.name} ({user.id})", icon_url=user.display_avatar.url)
        infoembed.description = f"Créé : {discord.utils.format_dt(user.created_at)}\nRejoint : "
        if hasattr(user, "joined_at"):
            infoembed.description += discord.utils.format_dt(user.joined_at, style="R")
            roles = ""
            for role in user.roles:
                if role.name != "@everyone":
                    roles += role.mention + " "
            infoembed.add_field(name="Rôles", value=roles)
        else:
            infoembed.description += "Not in server"
        infembed = discord.Embed(colour=discord.Colour.dark_red(), title="Dernières infractions utilisateur")
        query = DbOperations.query_db(DbOperations.get_db(client.config), "select id,type,author,time,description,until from infractions where user = ? order by id desc", [user.id])
        if not query:
            infembed.add_field(name="", value="Aucune infraction")
        else:
            await fill_embed_with_infractions(query[:5], infembed)
            if len(query) > 5:
                infembed.add_field(name="", value="...")
        notesembed = discord.Embed(colour=discord.Colour.dark_blue(), title="Dernières notes utilisateur")
        query = DbOperations.query_db(DbOperations.get_db(client.config), "select id,note,author,time from notes where user = ? order by id desc", [user.id])
        if not query:
            notesembed.add_field(name="", value="Aucune note")
        else:
            await fill_embed_with_notes(query[:5], notesembed)
            if len(query) > 5:
                notesembed.add_field(name="", value="...")
        await interaction.response.send_message(embeds=[infoembed, infembed, notesembed])

    @client.tree.command(description="Obtenir toutes les notes d'un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def notes(interaction: discord.Interaction, user: discord.User):
        """
        Command to get all notes for a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.User
            The targeted user, can also be replaced by their ID
        """
        embed = discord.Embed(colour=discord.Colour.dark_blue(), title="Toutes les notes utilisateur")
        query = DbOperations.query_db(DbOperations.get_db(client.config), "select id,note,author,time from notes where user = ? order by id desc", [user.id])
        if not query:
            embed.add_field(name="", value="Aucune note")
        else:
            await fill_embed_with_notes(query, embed)
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Obtenir toutes les infractions d'un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def inf(interaction: discord.Interaction, user: discord.Member):
        """
        Command to get all infractions for a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.User
            The targeted user, can also be replaced by their ID
        """
        embed = discord.Embed(colour=discord.Colour.dark_red(), title="Toutes les infractions utilisateur")
        query = DbOperations.query_db(DbOperations.get_db(client.config), "select id,type,author,time,description,until from infractions where user = ? order by id desc", [user.id])
        if not query:
            embed.add_field(name="", value="Aucune infraction")
        else:
            await fill_embed_with_infractions(query, embed)
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Obtenir toutes les infos sur une infraction")
    @discord.app_commands.check(client.check_user_has_rights)
    async def infinfo(interaction: discord.Interaction, infraction: int):
        """
        Command to get all information about an infraction for a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        infraction : int
            The targeted infraction ID
        """
        query = DbOperations.query_db(DbOperations.get_db(client.config), "select user,type,author,time,description,until from infractions where id = ?", [infraction])
        embed = discord.Embed(colour=discord.Colour.dark_red(), title="Infraction")
        if query:
            embed.add_field(name="ID", value=infraction, inline=False)
            user = await client.fetch_user(query[0]["user"])
            embed.add_field(name="Destinataire", value=f"{user.name} ({user.id}) {user.mention}", inline=False)
            embed.add_field(name="Type", value=query[0]["type"], inline=False)
            embed.add_field(name="Auteur", value=f"<@{query[0]['author']}>", inline=False)
            embed.add_field(name="Raison", value=query[0]["description"], inline=False)
            embed.add_field(name="Date", value=discord.utils.format_dt(datetime.fromtimestamp(int(query[0]["time"])), style="d"), inline=False)
            if query[0]["until"]:
                embed.add_field(name="Jusqu'à", value=discord.utils.format_dt(datetime.fromtimestamp(int(query[0]["until"])), style="d"), inline=False)
        else:
            embed.description = "L'infraction demandée n'existe pas"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Ajouter une note à un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def note(interaction: discord.Interaction, user: discord.User, note: str):
        """
        Command to attach a note to a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.User
            The targeted user, can also be replaced by their ID
        note : str
            The note text
        """
        DbOperations.query_db(DbOperations.get_db(client.config), "insert into notes (user,time,author,note) values ( ?, ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, note])
        embed = discord.Embed(colour=discord.Colour.dark_blue(), title="Note")
        embed.description = f":notepad_spiral: Vous avez ajouté une note à {user.mention} :\n> {note}"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Obtenir toutes les infos sur une note")
    @discord.app_commands.check(client.check_user_has_rights)
    async def noteinfo(interaction: discord.Interaction, note: int):
        """
        Command to get all information about a note for a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        infraction : int
            The targeted note ID
        """
        query = DbOperations.query_db(DbOperations.get_db(client.config), "select user,note,author,time from notes where id = ?", [note])
        embed = discord.Embed(colour=discord.Colour.dark_red(), title="Note")
        if query:
            embed.add_field(name="ID", value=note, inline=False)
            user = await client.fetch_user(query[0]["user"])
            embed.add_field(name="Sujet", value=f"{user.name} ({user.id}) {user.mention}", inline=False)
            embed.add_field(name="Auteur", value=f"<@{query[0]['author']}>", inline=False)
            embed.add_field(name="Note", value=query[0]["note"], inline=False)
            embed.add_field(name="Date", value=discord.utils.format_dt(datetime.fromtimestamp(int(query[0]["time"])), style="d"), inline=False)
        else:
            embed.description = "La note demandée n'existe pas"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Avertir un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
        """
        Command to send a warning to a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.Member
            The targeted user, can also be replaced by their ID
        reason : str
            The reason text
        """
        DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description) values ( ?, 'warn', ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, reason])
        embed = discord.Embed(colour=discord.Colour.yellow(), title="Avertissement")
        embed.description = f":warning: Vous avez reçu un avertissement sur le serveur `{interaction.guild.name}` pour la raison suivante :\n> {reason}"
        await user.send(embed=embed)
        embed.description = f":warning: Utilisateur {user.mention} averti pour la raison suivante :\n> {reason}"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Expulser un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
        """
        Command to kick a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.Member
            The targeted user, can also be replaced by their ID
        reason : str
            The reason text
        """
        DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description) values ( ?, 'kick', ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, reason])
        embed = discord.Embed(colour=discord.Colour.brand_red(), title="Expulsion")
        embed.description = f":door: Vous avez été expulsé du serveur `{interaction.guild.name}` pour la raison suivante :\n> {reason}"
        await user.send(embed=embed)
        await interaction.guild.kick(user, reason=reason)
        embed.description = f":door: Utilisateur {user.mention} expulsé pour la raison suivante :\n> {reason}"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Rendre un utilisateur muet")
    @discord.app_commands.check(client.check_user_has_rights)
    async def mute(interaction: discord.Interaction, user: discord.Member, reason: str, hours: int):
        """
        Command to mute a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.Member
            The targeted user, can also be replaced by their ID
        reason : str
            The reason text
        hours : int
            The quantity of time, in hours
        """
        td = timedelta(hours=hours)
        until = datetime.now() + td
        DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description,until) values ( ?, 'mute', ?, ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, reason, int(until.timestamp())])
        embed = discord.Embed(colour=discord.Colour.brand_red(), title="Silence")
        embed.description = f":mute: Vous avez été rendu muet sur le serveur `{interaction.guild.name}` pour la raison suivante :\n> {reason}"
        embed.add_field(name="", value=f"Jusqu'à : {discord.utils.format_dt(until)}")
        await user.send(embed=embed)
        await user.timeout(td, reason=reason)
        embed.description = f":mute: Utilisateur {user.mention} rendu muet pour la raison suivante :\n> {reason}"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Retirer le mutisme d'un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def unmute(interaction: discord.Interaction, user: discord.Member, reason: str):
        """
        Command to unmute a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.Member
            The targeted user, can also be replaced by their ID
        reason : str
            The reason text
        """
        DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description) values ( ?, 'unmute', ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, reason])
        embed = discord.Embed(colour=discord.Colour.green(), title="Mutisme désactivé")
        embed.description = f":loud_sound: Mutisme de l'utilisateur {user.mention} désactivé pour la raison suivante :\n> {reason}"
        await user.timeout(None, reason=reason)
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Bannir un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def ban(interaction: discord.Interaction, user: discord.Member, reason: str, days: Optional[int] = None):
        """
        Command to ban a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.Member
            The targeted user, can also be replaced by their ID
        reason : str
            The reason text
        days : Optional[int]
            The optional quantity of time, in days
        """
        embed = discord.Embed(colour=discord.Colour.dark_red(), title="Bannissement")
        embed.description = f":hammer: Vous avez été banni du serveur `{interaction.guild.name}` pour la raison suivante :\n> {reason}"
        if days is not None:
            until = datetime.now() + timedelta(days=days)
            DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description,until) values ( ?, 'ban', ?, ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, reason, int(until.timestamp())])
            embed.add_field(name="", value=f"Jusqu'à : {discord.utils.format_dt(until, style='d')}")
        else:
            DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description) values ( ?, 'ban', ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, reason])
        await user.send(embed=embed)
        await interaction.guild.ban(user, reason=reason)
        embed.description = f":hammer: Utilisateur {user.mention} banni pour la raison suivante :\n> {reason}"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Débannir un utilisateur")
    @discord.app_commands.check(client.check_user_has_rights)
    async def unban(interaction: discord.Interaction, user: discord.User, reason: str):
        """
        Command to unban a user.
        Requires permissions checked by UmbraClient.check_user_has_rights().
        
        Parameters
        ----------
        user : discord.Member
            The targeted user, can also be replaced by their ID
        reason : str
            The reason text
        """
        DbOperations.query_db(DbOperations.get_db(client.config), "insert into infractions (user,type,time,author,description) values ( ?, 'unban', ?, ?, ?)", [user.id, int(datetime.now().timestamp()), interaction.user.id, reason])
        await interaction.guild.unban(user, reason=reason)
        embed = discord.Embed(colour=discord.Colour.green(), title="Débannissement")
        embed.description = f":green_square: Utilisateur {user.mention} débanni pour la raison suivante :\n> {reason}"
        await interaction.response.send_message(embed=embed)

    client.scheduler = AsyncIOScheduler()
    client.scheduler.add_job(daily_unban, CronTrigger(hour=0, minute=0, second=0))
