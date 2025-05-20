# Umbra-Discord-bot

Release code quality : [![Release code quality](https://github.com/Captn138/Umbra-Discord-bot/actions/workflows/python-app.yml/badge.svg?branch=main&event=release)](https://github.com/Captn138/Umbra-Discord-bot/actions/workflows/python-app.yml) | 
Latest run : [![Latest run](https://github.com/Captn138/Umbra-Discord-bot/actions/workflows/python-app.yml/badge.svg)](https://github.com/Captn138/Umbra-Discord-bot/actions/workflows/python-app.yml)

## License
This project is licensed under the [GNU AGPL v3](LICENSE).
- All modifications of this code must be published under the same license, even for SaaS use cases
- You can comercialize a modification of this code
- You must attribute the source of the code

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
- /here_channel : manage here-allowed channels
- /report_channel : manage the report channel
- /manager : manage the manager role
- /debug : some useful commands to debug

## Requirements

- python3
- venv module
- make
- sqlite3

## Installation

DEPRECATED

1. `sqlite3 <db>.sqlite < schema.sql`
2. `echo token=<token> >> .env` and `echo dbname=<db>.sqlite >> .env`
3. `sqlite3 <db>.sqlite "insert into settings (key, value) values ('guild_id', '<guild_id>')"`
4. `make`

If you do not want to use the Makefile, here are the installation steps :

4. `python3 -m venv venv`
5. `. venv/bin/activate`
6. `pip3 install -r requirements.txt`
7. `python3 app.py`
