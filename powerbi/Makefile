# See https://clarkgrubb.com/makefile-style-guide#prologue
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

# See https://clarkgrubb.com/makefile-style-guide#phony-target-arg
FORCE:

kingfisher-collect:
	git clone https://github.com/open-contracting/kingfisher-collect.git

cardinal-rs:
	git clone https://github.com/open-contracting/cardinal-rs.git

.PHONY: pull-python
pull-python: kingfisher-collect cardinal-rs
	git -C kingfisher-collect pull --rebase

.PHONY: pull-cardinal
pull-cardinal: cardinal-rs
	git -C cardinal-rs pull --rebase

.PHONY: build-python
python: pull-python
	docker build --file Dockerfile_python --tag kingfisher-collect .

.PHONY: build-cardinal
cardinal: pull-cardinal
	docker build --file Dockerfile_cardinal --tag cardinal-rs .

.PHONY: all
all: build-python build-cardinal
