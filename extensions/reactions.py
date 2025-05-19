# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


import discord


async def setup(client):
    def build_string(string: str, message: discord.Message):
        string = string.replace('%USER%', message.author.mention)
        return string

    @client.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if payload.user_id == client.user.id:
            return
        channel = client.get_channel(payload.channel_id)
        if channel is None:
            channel = await client.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author == client.user:
            return
        for reaction in message.reactions:
            async for user in reaction.users():
                if reaction.emoji == payload.emoji and user == client.user:
                    return
        for emoji_id, text in client.config.emoji_reacts.items():
            if str(payload.emoji) == emoji_id:
                await message.add_reaction(payload.emoji)
                await message.reply(build_string(text, message))
