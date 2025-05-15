# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


import discord, traceback


class Feedback(discord.ui.Modal, title='Feedback'):
    def __init__(self, report_channel: int):
        super().__init__()
        self.report_channel = report_channel

    name = discord.ui.TextInput(
        label='Tag Discord',
        placeholder='Ton tag Discord ici...',
    )
    feedback = discord.ui.TextInput(
        label='Que penses-tu du bot ?',
        style=discord.TextStyle.long,
        placeholder='Tape ton feedback ici...',
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f":white_check_mark: Merci pour ton feedback, {self.name.value}!", ephemeral=True)
        log_channel = interaction.guild.get_channel(self.report_channel)
        embed = discord.Embed(colour=discord.Colour.blue(), title='Feedback')
        embed.description = self.feedback.value
        embed.set_author(name=self.name.value)
        embed.timestamp = interaction.created_at
        url_view = discord.ui.View()
        await log_channel.send(embed=embed, view=url_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(':exclamation: Oups! Quelque chose a mal tourné.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)


async def setup(client):
    @client.tree.command(description="Bonjour !")
    async def hello(interaction: discord.Interaction):
        await interaction.response.send_message(f"Salut, {interaction.user.mention} !", ephemeral=True)

    @client.tree.command(description="Envoyer un feedback")
    async def feedback(interaction: discord.Interaction):
        if not hasattr(client.config, 'report_channel'):
            return
        await interaction.response.send_modal(Feedback(int(client.config.report_channel)))

    @client.tree.command(description="Mentionner here avec un message personnalisé")
    async def here(interaction: discord.Interaction, message: str):
        if interaction.channel_id in client.config.here_allowed_channels:
            try:
                voice_status = await interaction.user.fetch_voice()
            except:
                voice_status = None
            if not voice_status or not voice_status.channel:
                await interaction.response.send_message(f"@here\nDe {interaction.user.mention} : {message}", allowed_mentions=discord.AllowedMentions(everyone=True))
            else:
                await interaction.response.send_message(f"@here\nDe {interaction.user.mention} dans <#{voice_status.channel.id}>: {message}", allowed_mentions=discord.AllowedMentions(everyone=True))

    @client.tree.command(name="help", description="Affiche l'aide pour une commande")
    @discord.app_commands.describe(command="Commande à propos de laquelle afficher l'aide")
    async def help_command(interaction: discord.Interaction, command: str = None):
        chat_commands = client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.chat_input)
        if command:
            embed = discord.Embed(colour=discord.Colour.blurple(), title=f"Aide commande")
            for cmd in chat_commands:
                if cmd.name == command and (not cmd.checks or client.check_user_has_rights(interaction)):
                    embed.add_field(name='', value=f"**/{cmd.name}** : {cmd.description}", inline=False)
            if embed.fields:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(":exclamation: Cette commande n'existe pas ou tu n'y as pas accès", ephemeral=True)
        else:
            userembed = discord.Embed(colour=discord.Colour.blurple(), title=f"Commandes utilisateur")
            modoembed = discord.Embed(colour=discord.Colour.brand_red(), title=f"Commandes modérateurs")
            modoembed.description = "Commandes réservées aux utilisateurs disposant des droits de gestion"
            appembed = discord.Embed(colour=discord.Colour.blurple(), title=f"Interaction application")
            for cmd in chat_commands:
                if cmd.checks:
                    modoembed.add_field(name='', value=f"**/{cmd.name}** : {cmd.description}", inline=False)
                else:
                    userembed.add_field(name='', value=f"**/{cmd.name}** : {cmd.description}", inline=False)
            for inter in client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.user):
                appembed.add_field(name='En interagissant avec un utilisateur', value=f"{inter.name}", inline=False)
            for inter in client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.message):
                appembed.add_field(name='En interagissant avec un message', value=f"{inter.name}", inline=False)
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
        chat_commands = client.tree.get_commands(guild=interaction.guild, type=discord.AppCommandType.chat_input)
        return [
            discord.app_commands.Choice(name=cmd.name, value=cmd.name)
            for cmd in chat_commands
            if current.lower() in cmd.name.lower() and (not cmd.checks or client.check_user_has_rights(interaction))
        ]