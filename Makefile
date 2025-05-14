# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

.SILENT:

all:	install run

run:	app.py .env
	echo All set ! Now running the bot ...
	. venv/bin/activate && python3 app.py

install:	venv requirements.txt
	echo Installing dependencies ...
	. venv/bin/activate && pip install -qqr requirements.txt

venv:
	echo Creating virtual env ...
	python3 -m venv venv

.env:
	echo .env file is needed > /dev/stderr
	exit 1