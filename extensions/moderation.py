import discord


async def setup(client):
    @client.tree.command(description="Supprimer des messages")
    async def clear(interaction: discord.Interaction, quantity: int = 1):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            await interaction.response.send_message(f"Suppression de {quantity} messages en cours ...", ephemeral=True)
            await interaction.channel.purge(limit=quantity)

    @client.tree.context_menu(name='Signaler un message')
    async def report_message(interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_message(f"Merci d'avoir signalé ce message de {message.author.mention} à nos modérateurs.", ephemeral=True)
        log_channel = interaction.guild.get_channel(int(client.config.report_channel))
        embed = discord.Embed(title='Message signalé')
        if message.content:
            embed.description = message.content
        embed.set_author(name=f"Auteur : {message.author.display_name}, ID : {message.author.id}", icon_url=message.author.display_avatar.url)
        embed.timestamp = message.created_at
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label='Aller au message', style=discord.ButtonStyle.url, url=message.jump_url))
        await log_channel.send(embed=embed, view=url_view)