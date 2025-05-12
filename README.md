# Umbra-Discord-bot

## Features

### General

- /hello : simple command allowing to check the bot health
- /feedback : allow the user to send a feedback

### Voice

- /add_watched_channel, /remove_watched_channel, /purge_watched_channels, /print_watched_channels : manage watched channels for automatic voice cahnnels
- /add_temp_name, /remove_temp_name, /purge_temp_names, /print_temp_names : manage names for automatic voice channels

### Moderation

- you can report a user by right clicking its profile > Apps > Signaler un utilisateur
- you can report a message by right clicking it > Apps > Signaler un message
- /clear : removes X messages, 1 by default

## Requirements

- python3 >= 3.10
- venv module
- make
- sqlite3

## Installation

1. `sqlite3 <db>.sqlite < schema.sql`
2. `echo token=<token> >> .env` and `echo dbname=<db>.sqlite >> .env`
3. `sqlite3 <db>.sqlite "insert into settings (key, value) values ('report_channel', '<report_channel_id>'), ('guild_id', '<guild_id>'), ('manager_id', '<manager_role_id>')"`
4. `make`