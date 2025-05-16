# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


import discord


async def setup(client):
    @client.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if payload.user_id == client.user.id: # ne trigger pas sur ses propres réactions
            return
        channel = client.get_channel(payload.channel_id) # get channel
        if channel is None:
            channel = await self.fetch_channel(payload.channel_id)
        try:
            message = await channel.fetch_message(payload.message_id) # get message
        except Exception:
            return
        if message.author == client.user:
            return
        for reaction in message.reactions: # parse emotes
            async for user in reaction.users(): # for user for emote
                if reaction.emoji == payload.emoji and user == client.user: # ne trigger pas si le bot a déjà emoté
                    return
        for id, msg in client.config.emoji_reacts.items():
            print(payload.emoji.id, int(id))
            if payload.emoji.id == int(id):
                await message.add_reaction(payload.emoji)
                await message.reply(msg)