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
	curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/env.public

cron.sh:
	curl -sSLO https://github.com/open-contracting/bi.open-contracting.org/raw/refs/heads/main/powerbi/cron.sh

env.private:
	curl -sSLO https://github.com/open-contracting/bi.open-contracting.org/raw/refs/heads/main/powerbi/env.private

.PHONY: setup
setup: env.public cron.sh env.private
	chmod go-rwx env.private

kingfisher-collect:
	git clone https://github.com/open-contracting/kingfisher-collect.git

cardinal-rs:
	git clone https://github.com/open-contracting/cardinal-rs.git

Dockerfile_cardinal:
	curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/Dockerfile_cardinal

Dockerfile_python:
	curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/Dockerfile_python

.PHONY: pull-kingfisher-collect
pull-kingfisher-collect: kingfisher-collect
	git -C kingfisher-collect pull --rebase

.PHONY: pull-cardinal-rs
pull-cardinal-rs: cardinal-rs
	git -C cardinal-rs pull --rebase

.PHONY: build-python
build-python: pull-kingfisher-collect pull-cardinal-rs Dockerfile_python
	docker build --file Dockerfile_python --tag kingfisher-collect .

.PHONY: build-cardinal
build-cardinal: pull-cardinal-rs Dockerfile_cardinal
	docker build --file Dockerfile_cardinal --tag cardinal-rs .

.PHONY: build
build: build-python build-cardinal

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

.PHONY: codelist
codelist:
	curl -sSL https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/data/codelist.csv | \
		psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS codelist' \
		-c 'CREATE TABLE codelist (id serial PRIMARY KEY, codelist text, code text, code_es text, UNIQUE (codelist, code))' \
		-c '\copy codelist (codelist, code, code_es) from stdin csv header'

.PHONY: cpc
cpc:
	curl -sSL https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/data/cpc.csv | \
		psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS cpc' \
		-c 'CREATE TABLE cpc (id serial PRIMARY KEY, code text UNIQUE, description text, description_es text)' \
		-c '\copy cpc (code, description, description_es) from stdin csv header'

.PHONY: excluded_supplier
excluded_supplier:
	psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS excluded_supplier' \
		-c "CREATE TABLE excluded_supplier (id serial PRIMARY KEY, identifier text UNIQUE)"


.PHONY: indicator
indicator:
	curl -sSL https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/data/indicator.csv | \
		psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS indicator' \
		-c 'CREATE TABLE indicator (id serial PRIMARY KEY, code text UNIQUE, category text, title text, description text, category_es text, title_es text, description_es text)' \
		-c '\copy indicator (code, category, title, description, category_es, title_es, description_es) from stdin csv header'

.PHONY: unspsc
unspsc:
	curl -sSL https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/data/unspsc.csv | \
		psql "$(DATABASE_URL)" -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS unspsc' \
		-c 'CREATE TABLE unspsc (id serial PRIMARY KEY, code integer UNIQUE, description text, description_es text)' \
		-c '\copy unspsc (code, description, description_es) from stdin csv header'

.PHONY: tables
tables: codelist cpc excluded_supplier indicator unspsc

data:
	mkdir -p data

logs:
	mkdir -p logs

scratch:
	mkdir -p scratch

cardinal.ini:
	curl -sSL -o cardinal.ini https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/cardinal/$(KINGFISHER_COLLECT_SPIDER).ini

filesystem: data logs scratch cardinal.ini

.PHONY: print-crontab
print-crontab: cron.sh
	printf "15 0 * * * $(CARDINAL_WORKDIR)/cron.sh\n"

.PHONY: clean-build
clean-build:
	rm -rf kingfisher-collect
	rm -rf cardinal-rs

.PHONY: force-clean
force-clean: clean-build
	rm -f cardinal.ini
	rm -rf data
	rm -rf logs
	rm -rf scratch

.PHONY: all
all: build database filesystem
