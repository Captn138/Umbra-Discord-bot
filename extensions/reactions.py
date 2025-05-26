"""
extensions/reactions.py (Umbra-Discord-Bot)
:license: AGPL-3.0,see LICENSE for details

This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later.

Reaction messages module for the Discord application. 
"""

import discord


if __name__ == "__main__":
    raise RuntimeError("Ce module n'est pas destiné à être exécuté directement.")


async def setup(client):
    """
    Function run when module loaded as an extension.
    """
    def build_string(string: str, message: discord.Message):
        """
        Builds the return string using the original message to replace some variables.
        
        Parameters
        ----------
        string : str
            The original string to replace
        message : discord.Message
            The message on which the reaction has been added
        
        Returns
        -------
        str
            The replaced string
        """
        string = string.replace("%USER%", message.author.mention)
        return string

    @client.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        """
        Function run when a reaction is added on a message, overridden from discord.Client.
        If the message reacted to is not from the application, the reaction is not from the application and the application has not yes reacted to the message,
        then if the reaction is a valid one, sends a message using build_string().
        """
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
