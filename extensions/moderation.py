import discord
from typing import Union, List
from dbOperations import dbOperations


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

    async def fill_embed_with_infractions(query: List, embed: discord.Embed, client: discord.Client):
        for elem in query:
            match elem["type"]:
                case "warn":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(elem["time"], style="d")} - {elem["id"]:03d}] :warning: {await client.fetch_user(elem["author"])} {elem["desc"][:15]}")
                case "ban":
                    if elem["until"]:
                        embed.add_field(name='', value=f"[{discord.utils.format_dt(elem["time"], style="d")} - {elem["id"]:03d}] :hammer: {await client.fetch_user(elem["author"])} {elem["desc"][:15]} - {discord.utils.format_dt(elem["until"], style="d")}")
                    else:
                        embed.add_field(name='', value=f"[{discord.utils.format_dt(elem["time"], style="d")} - {elem["id"]:03d}] :hammer: {await client.fetch_user(elem["author"])} {elem["desc"][:15]}")
                case "unban":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(elem["time"], style="d")} - {elem["id"]:03d}] :green_square: {await client.fetch_user(elem["author"])} {elem["desc"][:15]}")
                case "mute":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(elem["time"], style="d")} - {elem["id"]:03d}] :mute: {await client.fetch_user(elem["author"])} {elem["desc"][:15]} - {discord.utils.format_dt(elem["until"], style="d")}")
                case "kick":
                    embed.add_field(name='', value=f"[{discord.utils.format_dt(elem["time"], style="d")} - {elem["id"]:03d}] :door: {await client.fetch_user(elem["author"])} {elem["desc"][:15]}")

    async def fill_embed_with_notes(query: List, embed: discord.Embed, client: discord.Client):
        for elem in query:
                notesembed.add_field(name='', value=f"[{discord.utils.format_dt(elem["time"], style="d")} - {elem["id"]:03d}] {await client.fetch_user(elem["author"])} {elem["note"]}")

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
        query = dbOperations.query_db(client.config.db, 'select id,type,author,time,desc,until from infractions where user == ?', [user.id])
        if not query:
            infembed.add_field(name='', value='Aucune infraction')
        else:
            fill_embed_with_infractions(query[:5], infembed, client)
            if len(query) > 5:
                infembed.add_field(name='', value='...')
        notesembed = discord.Embed(colour=discord.Colour.dark_blue(), title=f"Dernières notes utilisateur")
        query = dbOperations.query_db(client.config.db, 'select id,note,author,time from notes where user == ?', [user.id])
        if not query:
            notesembed.add_field(name='', value='Aucune note')
        else:
            fill_embed_with_notes(query[:5], notesembed, client)
            if len(query) > 5:
                notesembed.add_field(name='', value='...')
        await interaction.response.send_message(embeds=[infoembed, infembed, notesembed])