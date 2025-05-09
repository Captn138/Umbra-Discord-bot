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
        await interaction.response.send_message(f'Hi, {interaction.user.mention}', ephemeral=True)

    @client.tree.command(description="Envoyer un feedback")
    async def feedback(interaction: discord.Interaction):
        await interaction.response.send_modal(Feedback(int(client.config.report_channel)))

    commands_info = {
        "hello": "Commande pour tester si le bot est allumé",
        "feedback": "Permet d'envoyer un feedback au développeur",
        "clear": "Supprime X messages, 1 message par défaut",
        "add_watched_channel": "Ajoute un salon à la liste de salons vocaux automatiques",
        "remove_watched_channel": "Supprime un salon de la liste de salons vocaux automatiques",
        "purge_watched_channels": "Supprime la liste de salons vocaux automatiques",
        "print_watched_channels": "Affiche la liste de salons vocaux automatiques",
        "add_temp_name": "Ajoute un nom de salon vocal automatique",
        "remove_temp_name": "Supprime un nom de salon vocal automatique",
        "purge_temp_names": "Supprime tous les noms de salons vocaux automatiques",
        "print_temp_names": "Affiche les noms de salons vocaux automatiques"
    }

    @client.tree.command(name="help", description="Affiche l'aide pour une commande.")
    @discord.app_commands.describe(command="Commande à propos de laquelle afficher l'aide")
    async def help_command(interaction: discord.Interaction, command: str):
        description = commands_info.get(command, "Aucune information disponible.")
        await interaction.response.send_message(f"**/{command}** — {description}", ephemeral=True)

    @help_command.autocomplete("command")
    async def help_autocomplete(interaction: discord.Interaction, current: str):
        return [
            discord.app_commands.Choice(name=cmd, value=cmd)
            for cmd in commands_info
            if current.lower() in cmd.lower()
        ]

    # @client.tree.command(name="debug")
    # async def debug_command(interaction: discord.Interaction):
    #     if interaction.user.id == 202779792599285760:
    #         await interaction.guild.get_channel(1370104081040801834).delete() # delete bugged channel
    #         await interaction.response.send_message('done', ephemeral=True)