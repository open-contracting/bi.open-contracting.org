# See https://clarkgrubb.com/makefile-style-guide#prologue
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

# See https://clarkgrubb.com/makefile-style-guide#phony-target-arg
FORCE:

include env.public

DATABASE_URL=postgresql://$(DATABASE_USER)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)
MAINTENANCE_DATABASE_URL=postgresql://$(MAINTENANCE_DATABASE_USER)@$(DATABASE_HOST):$(DATABASE_PORT)/$(MAINTENANCE_DATABASE_NAME)

env.public:
	curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/default/env.public

cron.sh:
	curl -sSLO https://github.com/open-contracting/bi.open-contracting.org/raw/refs/heads/main/powerbi/default/cron.sh

env.private:
	curl -sSLO https://github.com/open-contracting/bi.open-contracting.org/raw/refs/heads/main/powerbi/default/env.private

.PHONY: setup
setup: env.public cron.sh env.private
	chmod go-rwx env.private

kingfisher-collect:
	git clone https://github.com/open-contracting/kingfisher-collect.git

Dockerfile_python:
	curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/default/Dockerfile_python

.PHONY: pull-kingfisher-collect
pull-kingfisher-collect: kingfisher-collect
	git -C kingfisher-collect pull --rebase

.PHONY: build-python
build-python: pull-kingfisher-collect Dockerfile_python
	docker build --file Dockerfile_python --tag kingfisher-collect .

.PHONY: build
build: build-python

.PHONY: createdb
createdb:
	psql $(MAINTENANCE_DATABASE_URL) \
		<<<"SELECT 'CREATE DATABASE $(DATABASE_NAME)' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$(DATABASE_NAME)')\gexec"

.PHONY: createuser
createuser:
	psql $(MAINTENANCE_DATABASE_URL) \
		-c "SELECT 1/(SELECT COUNT(*) FROM pg_catalog.pg_roles WHERE rolname = '$(DATABASE_USER)')" &>/dev/null \
		&& echo "role '$(DATABASE_USER)' already exists" \
		|| createuser $(DATABASE_USER) -P

data:
	mkdir -p data

logs:
	mkdir -p logs

filesystem: data logs

.PHONY: print-crontab
print-crontab: cron.sh
	printf "15 0 * * * $(OCDS_POWERBI_WORKDIR)/cron.sh\n"

.PHONY: clean-build
clean-build:
	rm -rf kingfisher-collect

.PHONY: force-clean
force-clean: clean-build
	rm -rf data
	rm -rf logs

.PHONY: all
all: build database filesystem
