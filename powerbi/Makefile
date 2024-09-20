# See https://clarkgrubb.com/makefile-style-guide#prologue
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

# See https://clarkgrubb.com/makefile-style-guide#phony-target-arg
FORCE:

include config.mk

config.mk:
	curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/config.mk

cron.sh:
	curl -sSLO https://github.com/open-contracting/bi.open-contracting.org/raw/refs/heads/main/powerbi/cron.sh

.PHONY: setup
setup: config.mk cron.sh

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
	psql $(MAINTENANCE_DATABASE_NAME) -U $(MAINTENANCE_DATABASE_USER) -h $(DATABASE_HOST) \
		<<<"SELECT 'CREATE DATABASE $(DATABASE_NAME)' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$(DATABASE_NAME)')\gexec"

.PHONY: createuser
createuser:
	psql $(MAINTENANCE_DATABASE_NAME) -U $(MAINTENANCE_DATABASE_USER) -h $(DATABASE_HOST) \
		<<<"SELECT 'CREATE USER $(DATABASE_USER)' WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$(DATABASE_USER)')\gexec"

.PHONY: codelist
codelist:
	curl -sSL https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/data/codelist.csv | \
		psql $(DATABASE_NAME) -U $(DATABASE_USER) -h $(DATABASE_HOST) -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS codelist' \
		-c 'CREATE TABLE codelist (id serial PRIMARY KEY, codelist text, code text, code_es text, UNIQUE (codelist, code))' \
		-c '\copy codelist (codelist, code, code_es) from stdin csv header'

.PHONY: cpc
cpc:
	curl -sSL https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/data/cpc.csv | \
		psql $(DATABASE_NAME) -U $(DATABASE_USER) -h $(DATABASE_HOST) -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS cpc' \
		-c 'CREATE TABLE cpc (id serial PRIMARY KEY, code text UNIQUE, description text, description_es text)' \
		-c '\copy cpc (code, description, description_es) from stdin csv header'

.PHONY: indicator
indicator:
	curl -sSL https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/data/indicator.csv | \
		psql $(DATABASE_NAME) -U $(DATABASE_USER) -h $(DATABASE_HOST) -v ON_ERROR_STOP=1 \
		-c 'DROP TABLE IF EXISTS indicator' \
		-c 'CREATE TABLE indicator (id serial PRIMARY KEY, code text UNIQUE, category text, title text, description text, category_es text, title_es text, description_es text)' \
		-c '\copy indicator (code, category, title, description, category_es, title_es, description_es) from stdin csv header'

.PHONY: ecuador_sercop_bulk_result
ecuador_sercop_bulk_result:
	psql $(DATABASE_NAME) -U $(DATABASE_USER) -h $(DATABASE_HOST) \
		-c 'CREATE TABLE IF NOT EXISTS ecuador_sercop_bulk_result (id serial PRIMARY KEY, ocid text, subject text, code text, result numeric, buyer_id text, procuring_entity_id text, tenderer_id text, created_at timestamp without time zone)'

.PHONY: tables
tables: codelist cpc indicator ecuador_sercop_bulk_result

data:
	mkdir -p data

logs:
	mkdir -p logs

scratch:
	mkdir -p scratch

ecuador_sercop_bulk.ini:
	curl -sSLO https://raw.githubusercontent.com/open-contracting/deploy/main/salt/kingfisher/collect/files/cardinal/ecuador_sercop_bulk.ini

filesystem: data logs scratch ecuador_sercop_bulk.ini

.PHONY: print-crontab
print-crontab: cron.sh
	printf "15 0 * * * CARDINAL_DBNAME=$(DATABASE_NAME) CARDINAL_DBUSER=$(DATABASE_USER) CARDINAL_DBHOST=$(DATABASE_HOST) CARDINAL_DBHOST_DOCKER=$(DATABASE_HOST_DOCKER) $(CARDINAL_WORKDIR)/cron.sh"

.PHONY: clean-build
clean-build:
	rm -rf kingfisher-collect
	rm -rf cardinal-rs

.PHONY: force-clean
force-clean: clean-build
	rm -f ecuador_sercop_bulk.ini
	rm -rf data
	rm -rf logs
	rm -rf scratch

.PHONY: all
all: build database filesystem
