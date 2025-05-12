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
    @client.tree.command(description="Gérer les salons de la liste de création de salons")
    @discord.app_commands.describe(channel="Salon vocal requis si operation = add")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="add", value="add"),
        discord.app_commands.Choice(name="remove", value="remove"),
        discord.app_commands.Choice(name="purge", value="purge"),
        discord.app_commands.Choice(name="print", value="print")
    ])
    async def watched_channel(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: discord.VoiceChannel = None):
        if not client.check_user_has_rights(interaction.user):
            return
        match operation.value:
            case "add":
                if not channel:
                    await interaction.response.send_message(':exclamation: Un salon vocal est requis', ephemeral=True)
                elif channel.id in client.config.voice_watch_list:
                    await interaction.response.send_message(f":warning: `{channel.name}` appartient déjà à la liste de création de salons", ephemeral=True)
                else:
                    dbOperations.query_db(client.config.db, 'insert into voice_watch_list (id) values ( ? )', [channel.id])
                    client.config.voice_watch_list.append(channel.id)
                    await interaction.response.send_message(f":white_check_mark: `{channel.name}` ajouté à la liste de création de salons", ephemeral=True)
            case "remove":
                query = dbOperations.query_db(client.config.db, 'select id from voice_watch_list')
                if not client.config.voice_watch_list:
                    await interaction.response.send_message(':warning: La liste de création de salons est vide', ephemeral=True)
                else:
                    list = []
                    for id in client.config.voice_watch_list:
                        list.append(discord.SelectOption(label=interaction.guild.get_channel(id).name, value=id))
                    view = DropdownView(Dropdown_remove_watched_channel(client.config.db, client.config.voice_watch_list, list))
                    await interaction.response.send_message('Choisissez salon à supprimer de la liste de création de salons :', ephemeral=True, view=view)
            case "purge":
                view = Confirm()
                await interaction.response.send_message(':exclamation: Si vous continuez, tous les salons seront retirés de la liste de création de salons. Continuer ?', ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    dbOperations.query_db(client.config.db, 'delete from voice_watch_list')
                    client.config.voice_watch_list = []
            case "print":
                if not client.config.voice_watch_list:
                    await interaction.response.send_message(':warning: La liste de création de salons est vide', ephemeral=True)
                else:
                    msg = "Voici la liste de création de salons :\n"
                    for id in client.config.voice_watch_list:
                        msg += f"- <#{id}>\n"
                    await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Gérer les salons vocaux temporaires")
    @discord.app_commands.describe(name="Nom requis si operation = add")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="add", value="add"),
        discord.app_commands.Choice(name="remove", value="remove"),
        discord.app_commands.Choice(name="purge", value="purge"),
        discord.app_commands.Choice(name="print", value="print")
    ])
    async def temp_name(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], name: str = None):
        if not client.check_user_has_rights(interaction.user):
            return
        match operation.value:
            case "add":
                if not name:
                    await interaction.response.send_message(':exclamation: Un nom est requis', ephemeral=True)
                else:
                    dbOperations.query_db(client.config.db, 'insert into voice_channel_names (name) values ( ? )', [name])
                    await interaction.response.send_message(f":white_check_mark: `{name}` ajouté à la liste des noms de salons vocaux temporaires", ephemeral=True)
            case "remove":
                query = dbOperations.query_db(client.config.db, 'select name from voice_channel_names')
                if not query:
                    await interaction.response.send_message(':warning: La liste des noms de salons vocaux temporaires est vide', ephemeral=True)
                else:
                    list = []
                    for elem in query:
                        list.append(discord.SelectOption(label=elem['name']))
                    view = DropdownView(Dropdown_remove_temp_name(client.config.db, list))
                    await interaction.response.send_message('Choisissez le nom de salon vocal temporaire à supprimer :', ephemeral=True, view=view)
            case "purge":
                view = Confirm()
                await interaction.response.send_message(':exclamation: Si vous continuez, tous les noms seront retirés de la liste de noms de salons vocaux temporaires. Continuer ?', ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    dbOperations.query_db(client.config.db, 'delete from voice_channel_names')
            case "print":
                query = dbOperations.query_db(client.config.db, 'select name from voice_channel_names')
                if not query:
                    await interaction.response.send_message(':warning: La liste des noms de salons vocaux temporaires est vide', ephemeral=True)
                else:
                    msg = "Voici la liste des noms de salons vocaux temporaires :\n"
                    for elem in query:
                        msg += f"- {elem['name']}\n"
                    await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Gérer les salons de la liste des salons here")
    @discord.app_commands.describe(channel="Salon requis si operation = add")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="add", value="add"),
        discord.app_commands.Choice(name="remove", value="remove"),
        discord.app_commands.Choice(name="purge", value="purge"),
        discord.app_commands.Choice(name="print", value="print")
    ])
    async def here_channel(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: discord.TextChannel = None):
        if not client.check_user_has_rights(interaction.user):
            return
        match operation.value:
            case "add":
                if not channel:
                    await interaction.response.send_message(':exclamation: Un salon est requis', ephemeral=True)
                elif channel.id in client.config.here_allowed_channels:
                    await interaction.response.send_message(f":warning: `{channel.name}` appartient déjà à la liste des salons here", ephemeral=True)
                else:
                    dbOperations.query_db(client.config.db, 'insert into here_allowed_channels (id) values ( ? )', [channel.id])
                    client.config.here_allowed_channels.append(channel.id)
                    await interaction.response.send_message(f":white_check_mark: `{channel.name}` ajouté à la liste des salons here", ephemeral=True)
            case "remove":
                if not client.config.here_allowed_channels:
                    await interaction.response.send_message(':warning: La liste des salons here est vide', ephemeral=True)
                else:
                    list = []
                    for id in client.config.here_allowed_channels:
                        list.append(discord.SelectOption(label=interaction.guild.get_channel(id).name, value=id))
                    view = DropdownView(Dropdown_remove_here_channel(client.config.db, client.config.here_allowed_channels, list))
                    await interaction.response.send_message('Choisissez salon à supprimer de la liste des salons here :', ephemeral=True, view=view)
            case "purge":
                view = Confirm()
                await interaction.response.send_message(':exclamation: Si vous continuez, tous les salons seront retirés de la liste des salons here. Continuer ?', ephemeral=True, view=view)
                await view.wait()
                if view.value is not None and view.value:
                    dbOperations.query_db(client.config.db, 'delete from here_allowed_channels')
                    client.config.here_allowed_channels = []
            case "print":
                if not client.config.here_allowed_channels:
                    await interaction.response.send_message(':warning: La liste des salons here est vide', ephemeral=True)
                else:
                    msg = "Voici la liste des salons here :\n"
                    for id in client.config.here_allowed_channels:
                        msg += f"- <#{id}>\n"
                    await interaction.response.send_message(msg, ephemeral=True)

    @client.tree.command(description="Gérer le rôle de manager")
    @discord.app_commands.describe(role="Rôle requis si operation = set")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="get", value="get"),
        discord.app_commands.Choice(name="set", value="set"),
        discord.app_commands.Choice(name="unset", value="unset")
    ])
    async def manager(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], role: discord.Role = None):
        if not client.check_user_has_rights(interaction.user):
            return
        match operation.value:
            case "get":
                if not hasattr(client.config, 'manager_id'):
                    await interaction.response.send_message(":warning: Le rôle de manager n'est pas défini", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Le rôle de manager est : {interaction.guild.get_role(int(client.config.manager_id)).mention}", ephemeral=True)
            case "set":
                if not role:
                    await interaction.response.send_message(':exclamation: Un rôle est requis', ephemeral=True)
                else:
                    client.config.manager_id = str(role.id)
                    dbOperations.query_db(client.config.db, "delete from settings where key == 'manager_id'")
                    dbOperations.query_db(client.config.db, "insert into settings (key, value) values ('manager_id', ? )", [role.id])
                    await interaction.response.send_message(f":white_check_mark: {role.mention} est le nouveau rôle de manager", ephemeral=True)
            case "unset":
                if not hasattr(client.config, 'manager_id'):
                    await interaction.response.send_message(":warning: Le rôle de manager n'est pas défini", ephemeral=True)
                else:
                    dbOperations.query_db(client.config.db, "delete from settings where key == 'manager_id'")
                    del client.config.manager_id
                    await interaction.response.send_message(f":white_check_mark: Le rôle de manager à été désattribué", ephemeral=True)

    @client.tree.command(description="Gérer le salon de report")
    @discord.app_commands.describe(channel="Salon requis si operation = set")
    @discord.app_commands.choices(operation=[
        discord.app_commands.Choice(name="get", value="get"),
        discord.app_commands.Choice(name="set", value="set"),
        discord.app_commands.Choice(name="unset", value="unset")
    ])
    async def report_channel(interaction: discord.Interaction, operation: discord.app_commands.Choice[str], channel: discord.TextChannel = None):
        if not client.check_user_has_rights(interaction.user):
            return
        match operation.value:
            case "get":
                if not hasattr(client.config, 'report_channel'):
                    await interaction.response.send_message(":warning: Le salon de report n'est pas défini", ephemeral=True)
                else:
                    await interaction.response.send_message(f"Le salon de report est : {interaction.guild.get_channel(int(client.config.report_channel)).mention}", ephemeral=True)
            case "set":
                if not channel:
                    await interaction.response.send_message(':exclamation: Un salon est requis', ephemeral=True)
                else:
                    client.config.report_channel = str(channel.id)
                    dbOperations.query_db(client.config.db, "delete from settings where key == 'report_channel'")
                    dbOperations.query_db(client.config.db, "insert into settings (key, value) values ('report_channel', ? )", [channel.id])
                    await interaction.response.send_message(f":white_check_mark: {channel.mention} est le nouveau salon de report", ephemeral=True)
            case "unset":
                if not hasattr(client.config, 'report_channel'):
                    await interaction.response.send_message(":warning: Le salon de report n'est pas défini", ephemeral=True)
                else:
                    dbOperations.query_db(client.config.db, "delete from settings where key == 'report_channel'")
                    del client.config.report_channel
                    await interaction.response.send_message(f":white_check_mark: Le salon de report à été désattribué", ephemeral=True)