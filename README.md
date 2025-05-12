# Umbra-Discord-bot

## Features

### General

- /hello : simple command allowing to check the bot health
- /feedback : allow the user to send a feedback
- /here : mentions @here with your custom message, mentions the user that lanched the command as well as its voice channel if he is in one

### Voice

- /watched_channel : manage watched channels for automatic voice cahnnels
- /temp_name : manage names for automatic voice channels

### Moderation

- you can report a user by right clicking its profile > Apps > Signaler un utilisateur
- you can report a message by right clicking it > Apps > Signaler un message
- /clear : removes X messages, 1 by default
- /here_channel : manager here-allowed channels
- /report_channel : manage the report channel
- /manager : manage the manager role
- /debug : some useful commands to debug

## Requirements

- python3
- venv module
- make
- sqlite3

## Installation

1. `sqlite3 <db>.sqlite < schema.sql`
2. `echo token=<token> >> .env` and `echo dbname=<db>.sqlite >> .env`
3. `sqlite3 <db>.sqlite "insert into settings (key, value) values ('report_channel', '<report_channel_id>'), ('guild_id', '<guild_id>'), ('manager_id', '<manager_role_id>')"`
4. `make`
