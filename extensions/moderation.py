# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


import discord
from typing import Union, List
from dbOperations import dbOperations
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


class UserReport(discord.ui.Modal, title='Signalement'):
    def __init__(self, report_channel: int, user: discord.Member, target: discord.Member):
        super().__init__()
        self.report_channel = report_channel
        self.user = user
        self.target = target

    reason = discord.ui.TextInput(
        label='Raison du signalement',
        style=discord.TextStyle.long,
        placeholder='Tape ici...',
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f":white_check_mark: Merci pour ton signalement, {self.user.name}!", ephemeral=True)
        log_channel = interaction.guild.get_channel(self.report_channel)
        embed = discord.Embed(colour=discord.Colour.dark_red(), title=f"Utilisateur signalé")
        embed.description = f"{self.user.mention} signale {self.target.mention} :\n{self.reason.value}"
        embed.timestamp = interaction.created_at
        url_view = discord.ui.View()
        await log_channel.send(embed=embed, view=url_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(':exclamation: Oups! Quelque chose a mal tourné.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)


async def on_ready(self):
    self.scheduler.start()

async def daily_unban(client: discord.Client):
    # query = dbOperations.query_db(client.config.db, 'select user,until from infractions where type == "ban"')
    # for elem in query:
    #     if elem["until"] and datetime.today() > datetime.fromtimestamp():
    #         user = await client.fetch_user(elem["user"])
    #         guild.unban(user, reason='Levée de sanction automatique')
    pass

async def setup(client):
    @client.tree.command(description="Supprimer des messages")
    async def clear(interaction: discord.Interaction, quantity: int = 1):
        if not client.check_user_has_rights(interaction.user):
            return
        await interaction.response.send_message(f":arrows_counterclockwise: Suppression de {quantity} messages en cours ...", ephemeral=True)
        await interaction.channel.purge(limit=quantity)

    @client.tree.context_menu(name='Signaler un message')
    async def report_message(interaction: discord.Interaction, message: discord.Message):
        if not hasattr(client.config, 'report_channel'):
            return
        await interaction.response.send_message(f":white_check_mark: Merci d'avoir signalé ce message de {message.author.mention} à nos modérateurs.", ephemeral=True)
        log_channel = interaction.guild.get_channel(int(client.config.report_channel))
        embed = discord.Embed(colour=discord.Colour.dark_red(), title='Message signalé')
        if message.content:
            embed.description = message.content
        embed.set_author(name=f"Auteur : {message.author.display_name}, ID : {message.author.id}", icon_url=message.author.display_avatar.url)
        embed.timestamp = message.created_at
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Aller au message', style=discord.ButtonStyle.url, url=message.jump_url))
        await log_channel.send(embed=embed, view=url_view)

    @client.tree.context_menu(name='Signaler un utilisateur')
    async def report_user(interaction: discord.Interaction, user: discord.Member):
        if not hasattr(client.config, 'report_channel'):
            return
        await interaction.response.send_modal(UserReport(int(client.config.report_channel), interaction.user, user))

    async def fill_embed_with_infractions(query: List, embed: discord.Embed):
        for elem in query:
            match elem["type"]:
                case "warn":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem["time"])), style="d")} - `{elem["rowid"]:03d}`] :warning: <@{elem["author"]}> {elem["desc"][:30]}", inline=False)
                case "ban":
                    if elem["until"]:
                        embed.add_field(name='', value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem["time"])), style="d")} - `{elem["rowid"]:03d}`] :hammer: <@{elem["author"]}> {elem["desc"][:30]} - {discord.utils.format_dt(datetime.fromtimestamp(int(elem["until"])), style="d")}", inline=False)
                    else:
                        embed.add_field(name='', value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem["time"])), style="d")} - `{elem["rowid"]:03d}`] :hammer: <@{elem["author"]}> {elem["desc"][:30]}", inline=False)
                case "unban":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem["time"])), style="d")} - `{elem["rowid"]:03d}`] :green_square: <@{elem["author"]}> {elem["desc"][:30]}", inline=False)
                case "mute":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem["time"])), style="d")} - `{elem["rowid"]:03d}`] :mute: <@{elem["author"]}> {elem["desc"][:30]} - {discord.utils.format_dt(datetime.fromtimestamp(int(elem["until"])), style="d")}", inline=False)
                case "kick":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem["time"])), style="d")} - `{elem["rowid"]:03d}`] :door: <@{elem["author"]}> {elem["desc"][:30]}", inline=False)

    async def fill_embed_with_notes(query: List, embed: discord.Embed):
        for elem in query:
            embed.add_field(name='', value=f"[{discord.utils.format_dt(datetime.fromtimestamp(int(elem["time"])), style="d")} - `{elem["rowid"]:03d}`] <@{elem["author"]}> {elem["note"]}", inline=False)

    @client.tree.command(description="Obtenir des informations sur un utilisateur")
    async def userinfo(interaction: discord.Interaction, user: discord.Member):
        if not client.check_user_has_rights(interaction.user):
            return
        infoembed = discord.Embed(colour=discord.Colour.blurple(), title=f"Infos utilisateur")
        infoembed.set_author(name=f"{user.name} ({user.id})", icon_url=user.display_avatar.url)
        infoembed.description = f"Créé : {discord.utils.format_dt(user.created_at)}\nRejoint : {discord.utils.format_dt(user.joined_at)} ({discord.utils.format_dt(user.joined_at, style='R')})"
        roles = ''
        for role in user.roles:
            if role.name != '@everyone':
                roles += role.mention + ' '
        infoembed.add_field(name='Rôles', value=roles)
        infembed = discord.Embed(colour=discord.Colour.dark_red(), title=f"Dernières infractions utilisateur")
        query = dbOperations.query_db(client.config.db, 'select rowid,type,author,time,desc,until from infractions where user == ?', [user.id])
        if not query:
            infembed.add_field(name='', value='Aucune infraction')
        else:
            await fill_embed_with_infractions(query[:5], infembed)
            if len(query) > 5:
                infembed.add_field(name='', value='...')
        notesembed = discord.Embed(colour=discord.Colour.dark_blue(), title=f"Dernières notes utilisateur")
        query = dbOperations.query_db(client.config.db, 'select rowid,note,author,time from notes where user == ?', [user.id])
        if not query:
            notesembed.add_field(name='', value='Aucune note')
        else:
            await fill_embed_with_notes(query[:5], notesembed)
            if len(query) > 5:
                notesembed.add_field(name='', value='...')
        await interaction.response.send_message(embeds=[infoembed, infembed, notesembed])

    @client.tree.command(description="Obtenir toutes les notes d'un utilisateur")
    async def notes(interaction: discord.Interaction, user: discord.Member):
        if not client.check_user_has_rights(interaction.user):
            return
        embed = discord.Embed(colour=discord.Colour.dark_blue(), title=f"Toutes les notes utilisateur")
        query = dbOperations.query_db(client.config.db, 'select rowid,note,author,time from notes where user == ?', [user.id])
        if not query:
            embed.add_field(name='', value='Aucune note')
        else:
            await fill_embed_with_notes(query, embed)
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Obtenir toutes les infractions d'un utilisateur")
    async def inf(interaction: discord.Interaction, user: discord.Member):
        if not client.check_user_has_rights(interaction.user):
            return
        embed = discord.Embed(colour=discord.Colour.dark_red(), title=f"Toutes les infractions utilisateur")
        query = dbOperations.query_db(client.config.db, 'select rowid,type,author,time,desc,until from infractions where user == ?', [user.id])
        if not query:
            embed.add_field(name='', value='Aucune infraction')
        else:
            await fill_embed_with_infractions(query, embed)
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Ajouter une note à un utilisateur")
    async def note(interaction: discord.Interaction, user: discord.Member, note : str):
        dbOperations.query_db(client.config.db, 'insert into notes (user,time,author,note) values ( ?, ?, ?, ?)', [user.id, int(datetime.now().timestamp()), interaction.user.id, note])
        embed = discord.Embed(colour=discord.Colour.dark_blue(), title='Note')
        embed.description = f":notepad_spiral: Vous avez ajouté une note à {user.mention} :\n> {note}"
        await interaction.response.send_message(embed=embed)

    @client.tree.command(description="Avertir un utilisateur")
    async def warn(interaction: discord.Interaction, user: discord.Member, reason : str):
        dbOperations.query_db(client.config.db, 'insert into infractions (user,type,time,author,desc) values ( ?, "warn", ?, ?, ?)', [user.id, int(datetime.now().timestamp()), interaction.user.id, reason])
        embed = discord.Embed(colour=discord.Colour.yellow(), title='Avertissement')
        embed.description = f":warning: Vous avez reçu un avertissement sur le serveur `{interaction.guild.name}` pour la raison suivante :\n> {reason}"
        await user.send(embed=embed)
        embed.description = f":warning: Utilisateur {user.mention} averti pour la raison suivante :\n> {reason}"
        await interaction.response.send_message(embed=embed)

    client.scheduler = AsyncIOScheduler()
    client.scheduler.add_job(daily_unban, CronTrigger(hour=0, minute=0, second=0), args=[client])