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
        await interaction.response.send_message(':white_check_mark: Action confirmée.', ephemeral=True)
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.send_message(':exclamation: Action refusée.', ephemeral=True)
        self.stop()


class Dropdown_remove_here_channel(discord.ui.Select):
    def __init__(self, db, configList : List[int], list: List[discord.SelectOption]):
        super().__init__(placeholder='Choisissez une valeur ...', min_values=1, max_values=1, options=list)
        self.db = db
        self.configList = configList

    async def callback(self, interaction: discord.Interaction):
        dbOperations.query_db(self.db, 'delete from here_allowed_channels where id == ?', [self.values[0]])
        self.configList.remove(int(self.values[0]))
        await interaction.response.send_message(':white_check_mark: Salon retiré de la liste des salons here', ephemeral=True)


class Dropdown_remove_temp_name(discord.ui.Select):
    def __init__(self, db, list: List[discord.SelectOption]):
        super().__init__(placeholder='Choisissez une valeur ...', min_values=1, max_values=1, options=list)
        self.db = db

    async def callback(self, interaction: discord.Interaction):
        dbOperations.query_db(self.db, 'delete from voice_channel_names where name == ?', [self.values[0]])
        await interaction.response.send_message(':white_check_mark: Nom de salon vocal temporaire supprimé', ephemeral=True)


class Dropdown_remove_watched_channel(discord.ui.Select):
    def __init__(self, db, configList : List[int], list: List[discord.SelectOption]):
        super().__init__(placeholder='Choisissez une valeur ...', min_values=1, max_values=1, options=list)
        self.db = db
        self.configList = configList

    async def callback(self, interaction: discord.Interaction):
        dbOperations.query_db(self.db, 'delete from voice_watch_list where id == ?', [self.values[0]])
        self.configList.remove(int(self.values[0]))
        await interaction.response.send_message(':white_check_mark: Salon retiré de la liste de création de salons', ephemeral=True)


class DropdownView(discord.ui.View):
    def __init__(self, dropdown: discord.ui.Select):
        super().__init__()
        self.add_item(dropdown) 


async def setup(client):
    @client.tree.command(description="Ajouter un salon vocal à la liste de création de salons")
    async def add_watched_channel(interaction: discord.Interaction, channel: discord.VoiceChannel):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            if channel.id in client.config.voice_watch_list:
                await interaction.response.send_message(f":warning: `{channel.name}` appartient déjà à la liste de création de salons", ephemeral=True)
            else:
                dbOperations.query_db(client.config.db, 'insert into voice_watch_list (id) values ( ? )', [channel.id])
                client.config.voice_watch_list.append(channel.id)
                await interaction.response.send_message(f":white_check_mark: `{channel.name}` ajouté à la liste de création de salons", ephemeral=True)

    @client.tree.command(description="Retirer un salon vocal de la liste de création de salons")
    async def remove_watched_channel(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            query = dbOperations.query_db(client.config.db, 'select id from voice_watch_list')
            if not client.config.voice_watch_list:
                await interaction.response.send_message(':warning: La liste de création de salons est vide', ephemeral=True)
            else:
                list = []
                for id in client.config.voice_watch_list:
                    list.append(discord.SelectOption(label=interaction.guild.get_channel(id).name, value=id))
                view = DropdownView(Dropdown_remove_watched_channel(client.config.db, client.config.voice_watch_list, list))
                await interaction.response.send_message('Choisissez salon à supprimer de la liste de création de salons :', ephemeral=True, view=view)

    @client.tree.command(description="Retirer TOUS les salons vocaux de la liste de création de salons")
    async def purge_watched_channels(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            view = Confirm()
            await interaction.response.send_message(':exclamation: Si vous continuez, tous les salons seront retirés de la liste de création de salons. Continuer ?', ephemeral=True, view=view)
            await view.wait()
            if view.value is not None and view.value:
                dbOperations.query_db(client.config.db, 'delete from voice_watch_list')
                client.config.voice_watch_list = []

    @client.tree.command(description="Lister les salons vocaux de la liste de création de salons")
    async def print_watched_channels(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            if not client.config.voice_watch_list:
                await interaction.response.send_message(':warning: La liste de création de salons est vide', ephemeral=True)
            else:
                msg = "Voici la liste de création de salons :\n"
                for id in client.config.voice_watch_list:
                    msg += f"- <#{id}>\n"
                await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Ajouter un nom de salon vocal temporaire")
    async def add_temp_name(interaction: discord.Interaction, name: str):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            dbOperations.query_db(client.config.db, 'insert into voice_channel_names (name) values ( ? )', [name])
            await interaction.response.send_message(f":white_check_mark: `{name}` ajouté à la liste des noms de salons vocaux temporaires", ephemeral=True)

    @client.tree.command(description="Retirer un nom de salon vocal temporaire")
    async def remove_temp_name(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            query = dbOperations.query_db(client.config.db, 'select name from voice_channel_names')
            if not query:
                await interaction.response.send_message(':warning: La liste des noms de salons vocaux temporaires est vide', ephemeral=True)
            else:
                list = []
                for elem in query:
                    list.append(discord.SelectOption(label=elem['name']))
                view = DropdownView(Dropdown_remove_temp_name(client.config.db, list))
                await interaction.response.send_message('Choisissez le nom de salon vocal temporaire à supprimer :', ephemeral=True, view=view)

    @client.tree.command(description="Retirer TOUS les noms de salons vocaux temporaires")
    async def purge_temp_names(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            view = Confirm()
            await interaction.response.send_message(':exclamation: Si vous continuez, tous les noms seront retirés de la liste de noms de salons vocaux temporaires. Continuer ?', ephemeral=True, view=view)
            await view.wait()
            if view.value is not None and view.value:
                dbOperations.query_db(client.config.db, 'delete from voice_channel_names')

    @client.tree.command(description="Lister les noms de salons vocaux temporaires")
    async def print_temp_names(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            query = dbOperations.query_db(client.config.db, 'select name from voice_channel_names')
            if not query:
                await interaction.response.send_message(':warning: La liste des noms de salons vocaux temporaires est vide', ephemeral=True)
            else:
                msg = "Voici la liste des noms de salons vocaux temporaires :\n"
                for elem in query:
                    msg += f"- {elem['name']}\n"
                await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Ajouter un salon à la liste des salons here")
    async def add_here_channel(interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            if channel.id in client.config.here_allowed_channels:
                await interaction.response.send_message(f":warning: `{channel.name}` appartient déjà à la liste des salons here", ephemeral=True)
            else:
                dbOperations.query_db(client.config.db, 'insert into here_allowed_channels (id) values ( ? )', [channel.id])
                client.config.here_allowed_channels.append(channel.id)
                await interaction.response.send_message(f":white_check_mark: `{channel.name}` ajouté à la liste des salons here", ephemeral=True)

    @client.tree.command(description="Retirer un salon de la liste des salons here")
    async def remove_here_channel(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            if not client.config.here_allowed_channels:
                await interaction.response.send_message(':warning: La liste des salons here est vide', ephemeral=True)
            else:
                list = []
                for id in client.config.here_allowed_channels:
                    list.append(discord.SelectOption(label=interaction.guild.get_channel(id).name, value=id))
                view = DropdownView(Dropdown_remove_here_channel(client.config.db, client.config.here_allowed_channels, list))
                await interaction.response.send_message('Choisissez salon à supprimer de la liste des salons here :', ephemeral=True, view=view)

    @client.tree.command(description="Retirer TOUS les salons de la liste des salons here")
    async def purge_here_channels(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            view = Confirm()
            await interaction.response.send_message(':exclamation: Si vous continuez, tous les salons seront retirés de la liste des salons here. Continuer ?', ephemeral=True, view=view)
            await view.wait()
            if view.value is not None and view.value:
                dbOperations.query_db(client.config.db, 'delete from here_allowed_channels')
                client.config.here_allowed_channels = []

    @client.tree.command(description="Lister les salons de la liste des salons here")
    async def print_here_channels(interaction: discord.Interaction):
        if client.check_user_has_rights(interaction.user, int(client.config.manager_id)):
            if not client.config.here_allowed_channels:
                await interaction.response.send_message(':warning: La liste des salons here est vide', ephemeral=True)
            else:
                msg = "Voici la liste des salons here :\n"
                for id in client.config.here_allowed_channels:
                    msg += f"- <#{id}>\n"
                await interaction.response.send_message(msg, ephemeral=True)
