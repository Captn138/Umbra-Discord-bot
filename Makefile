# This file is part of Umbra-Discord-Bot, licensed under AGPL-3.0-or-later

ifeq (, $(shell which pyenv))
$(error "No pyenv in $(PATH), consider doing curl https://pyenv.run | bash")
endif

VENV_NAME := umbra
VENV_DIR=$(shell pyenv root)/versions/${VENV_NAME}
PYTHON=${VENV_DIR}/bin/python3
PIP=${VENV_DIR}/bin/pip3

.SILENT:

all:	install run

run:	app.py .env
	echo All set ! Now running the bot ...
	$(PYTHON) app.py

.env:
	$(error ".env file is needed")

install:	python venv requirements.txt
	echo Installing dependencies ...
	$(PIP) install -qqr requirements.txt

venv:
	echo Checking for venv ...
	@if ! pyenv versions --bare | grep -q "^$(VENV_NAME)$$"; then \
		echo Creating virtualenv $(VENV_NAME) ...; \
		pyenv virtualenv $(VENV_NAME); \
	fi

python:
	echo Checking for Python installation ...
	pyenv install -s

clean:
	echo Removing virtual environment ...
	pyenv virtualenv-delete -f $(VENV_NAME)
	echo Removing python cache  ...
	find . -type d -name "*__pycache__" -exec rm -rf {} +