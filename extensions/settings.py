import discord
from dbOperations import dbOperations
from typing import List


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.send_message('Action confirmée.', ephemeral=True)
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.send_message('Action refusée.', ephemeral=True)
        self.stop()


class Dropdown_remove_temp_name(discord.ui.Select):
    def __init__(self, db, list: List[str]):
        super().__init__(placeholder='Choisissez une valeur ...', min_values=1, max_values=1, options=list)
        self.db = db

    async def callback(self, interaction: discord.Interaction):
        dbOperations.query_db(self.db, 'delete from voice_channel_names where name == ?', [self.values[0]])
        await interaction.response.send_message('Nom de salon vocal temporaire supprimé', ephemeral=True)


class Dropdown_remove_watched_channel(discord.ui.Select):
    def __init__(self, db, list: List[int]):
        super().__init__(placeholder='Choisissez une valeur ...', min_values=1, max_values=1, options=list)
        self.db = db

    async def callback(self, interaction: discord.Interaction):
        dbOperations.query_db(self.db, 'delete from voice_watch_list where id == ?', [self.values[0]])
        await interaction.response.send_message('Salon retiré de la liste de création de salons', ephemeral=True)


class DropdownView(discord.ui.View):
    def __init__(self, dropdown: discord.ui.Select):
        super().__init__()
        self.add_item(dropdown) 


async def setup(client):
    @client.tree.command(description="Ajouter un salon vocal à la liste de création de salons")
    async def add_watched_channel(interaction: discord.Interaction, channel: discord.VoiceChannel): # TODO multiples ajouts
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            dbOperations.query_db(client.config.db, 'insert into voice_watch_list (id) values ( ? )', [channel.id])
            client.config.voice_watch_list.append(channel.id)
            await interaction.response.send_message(f"`{channel.name}` ajouté à la liste de création de salons", ephemeral=True)

    @client.tree.command(description="Retirer un salon vocal de la liste de création de salons")
    async def remove_watched_channel(interaction: discord.Interaction, channel: discord.VoiceChannel): # TODO dropdown
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            if channel.id in client.config.voice_watch_list:
                dbOperations.query_db(client.config.db, 'delete from voice_watch_list where id = ?', [channel.id])
                client.config.voice_watch_list.remove(channel.id)
                await interaction.response.send_message(f"`{channel.name}` retiré de la liste de création de salons", ephemeral=True)
            else:
                await interaction.response.send_message(f"`{channel.name}` n'était pas dans la liste de création de salons", ephemeral=True)

    @client.tree.command(description="Retirer TOUS les salons vocaux de la liste de création de salons")
    async def purge_watched_channels(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            view = Confirm()
            await interaction.response.send_message('Si vous continuez, tous les salons seront retirés de la liste de création de salons. Continuer ?', ephemeral=True, view=view)
            await view.wait()
            if view.value is not None and view.value:
                dbOperations.query_db(client.config.db, 'delete from voice_watch_list')
                client.config.voice_watch_list = []

    @client.tree.command(description="Lister les salons vocaux de la liste de création de salons")
    async def print_watched_channels(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            if not client.config.voice_watch_list:
                await interaction.response.send_message('La liste de création de salons est vide', ephemeral=True)
            else:
                msg = "Voici la liste de création de salons :\n"
                for id in client.config.voice_watch_list:
                    msg += f"- <#{id}>\n"
                await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Ajouter un nom de salon vocal temporaire")
    async def add_temp_name(interaction: discord.Interaction, name: str):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            dbOperations.query_db(client.config.db, 'insert into voice_channel_names (name) values ( ? )', [name])
            await interaction.response.send_message(f"`{name}` ajouté à la liste des noms de salons vocaux temporaires", ephemeral=True)

    @client.tree.command(description="Retirer un nom de salon vocal temporaire")
    async def remove_temp_name(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            query = dbOperations.query_db(client.config.db, 'select name from voice_channel_names')
            if not query:
                await interaction.response.send_message('La liste des noms de salons vocaux temporaires est vide', ephemeral=True)
            else:
                list = []
                for name in query:
                    list.append(discord.SelectOption(label=name['name']))
                view = DropdownView(Dropdown_remove_temp_name(client.config.db, list))
                await interaction.response.send_message('Choisissez le nom de salon vocal temporaire à supprimer:', ephemeral=True, view=view)

    @client.tree.command(description="Retirer TOUS les noms de salons vocaux temporaires")
    async def purge_temp_names(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            view = Confirm()
            await interaction.response.send_message('Si vous continuez, tous les noms seront retirés de la liste de noms de salons vocaux temporaires. Continuer ?', ephemeral=True, view=view)
            await view.wait()
            if view.value is not None and view.value:
                dbOperations.query_db(client.config.db, 'delete from voice_channel_names')

    @client.tree.command(description="Lister les noms de salons vocaux temporaires")
    async def print_temp_names(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            query = dbOperations.query_db(client.config.db, 'select name from voice_channel_names')
            if not query:
                await interaction.response.send_message('La liste des noms de salons vocaux temporaires est vide', ephemeral=True)
            else:
                msg = "Voici la liste des noms de salons vocaux temporaires :\n"
                for name in query:
                    msg += f"- {name['name']}\n"
                await interaction.response.send_message(msg, ephemeral=True)