-- This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later
CREATE TABLE settings(key text, value text);
CREATE TABLE voice_channel_names(name text);
CREATE TABLE voice_watch_list(id text);
CREATE TABLE here_allowed_channels(id text);
CREATE TABLE infractions(user text, type text, time text, author text, desc text, until text);
CREATE TABLE notes(user text, time text, author text, note text);
