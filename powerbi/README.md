# Power BI

Follow these instructions to deploy [Kingfisher Collect](https://kingfisher-collect.readthedocs.io/en/latest/) and [Cardinal](https://cardinal.readthedocs.io/en/latest/) using Docker.

The [Makefile](Makefile) makes this easy to setup. You can configure it by changing the settings in the [config.mk](config.mk) file.

All commands assume that the current directory is the "working directory" for the project.

You must choose an operating system user with read, write and execute permissions to the working directory (`chmod 700`, at least). For simplicity, you p:

- Name the operating system user the same as the database user (`DATABASE_USER` setting)
- Create a home directory for the operating system user, to use as the working directory (`CARDINAL_WORKDIR` setting)
- Make the working directory readable and executable by others (`chmod 755`)

## Tips

To print the commands that a `make` target would execute, use the `-n` (`--dry-run`) option. For example:

```bash
make -n database
```

To run all targets (setup the database, setup the filesystem, build the images, and install the crontab), run:

```bash
make -s
make -s print-crontab | crontab
```

## Setup

Download the `Makefile` to the current directory:

```bash
curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/Makefile
```

Download the `config.mk` and `cron.sh` files to the current directory, if they don't exist:

```bash
make setup
```

Lastly, edit the `config.mk` file, as needed.

## Database

These commands connect to the PostgreSQL host set by the `DATABASE_HOST` setting, by default `localhost`.

### Create database and user

This step requires a PostgreSQL **maintenance database user** (the `MAINTENANCE_DATABASE_USER` setting, by default the name of the current operating system user) with the privileges:

- [`CREATEDB`](https://www.postgresql.org/docs/current/sql-createrole.html) database privilege
- `CREATEROLE` database privilege
- [`CONNECT`](https://www.postgresql.org/docs/current/ddl-priv.html) object privilege to the **maintenance database** (the `MAINTENANCE_DATABASE_NAME` setting, by default `postgres`)

Run `make -s createdb createuser` to:

- Create the **project database** (the `DATABASE_NAME` setting, by default `cardinal`), owned by the **maintenance database user**, if it doesn't exist
- Create the **project database user** (the `DATABASE_USER` setting, by default `cardinal`), if it doesn't exist

This must be run:

- by any operating system user,
- that can authenticate as the **maintenance database user** without a password,
- from any directory containing the `Makefile` and `config.mk` files,
- to which the operating system user has read and execute permissions.

The simplest option is to run this command as the `postgres` operating system user, since the default [pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) file allows local `peer` connections as the `postgres` database user to all databases.

Otherwise, you can, for example, create a [.pgpass](https://www.postgresql.org/docs/current/libpq-pgpass.html) file in the operating system user's home directory, and set its permissions to owner-readable only (`chmod 400`). For example:

```none
localhost:5432:maintenance-database-name:maintenance-database-user:strong-password
```

### Create tables

Run `make -s tables` to:

- Create the `ecuador_sercop_bulk_result` table, owned by the **project database user**, if it doesn't exist
- Create (or re-create) the `codelist`, `indicator` and `cpc` tables, owned by the **project database user**

This must be run:

- by any operating system user,
- that can authenticate as the **project database user** without a password,
- from any directory containing the `Makefile` and `config.mk` files,
- to which the operating system user has read and execute permissions.

The simplest option is to set the `DATABASE_USER` setting to the name of the operating system user that will run the [cron job](#cron), since the default [pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) file allows local `peer` connections as any database user to all databases.

Otherwise, you can, for example, create a [.pgpass](https://www.postgresql.org/docs/current/libpq-pgpass.html) file in the operating system user's home directory, and set its permissions to owner-readable only (`400`). For example:

```none
localhost:5432:project-database-name:project-database-user:strong-password
```

## Docker

Run `make build` to:

- Clone the `kingfisher-collect` and `cardinal-rs` repositories into the current directory, if they don't exist
- Download the `Dockerfile_cardinal` and `Dockerfile_python` files to the current directory, if they don't exist
- Pull changes for the `kingfisher-collect` and `cardinal-rs` repositories
- Build the `kingfisher-collect` and `cardinal-rs` images

This must be run:

- by any operating system user,
- from any directory containing the `Makefile`,
- to which the user has read, write and execute permissions.

The `kingfisher-collect` image is for running `scrapy` and `manage.py` commands, like:

```bash
docker run --rm --name kingfisher-collect kingfisher-collect scrapy --help
docker run --rm --name kingfisher-collect kingfisher-collect python manage.py --help
```

The `cardinal-rs` image is for running `ocdscardinal` commands, like:

```bash
docker run --rm --name cardinal-rs cardinal-rs --help
```

## Filesystem

Run `make -s filesystem` to:

- Create `data`, `logs` and `scratch` directories, owned by the current operating system user, if they don't exist
- Download Cardinal's settings file to `ecuador_sercop_bulk.ini`, owned by the current operating system user

This must be run:

- by the operating system user that will run the [cron job](#cron),
- from the working directory for the project (same as the `CARDINAL_WORKDIR` setting).

## Cron

Preview the crontab entry, to make sure the directory of the `cron.sh` script is correct (if not, edit the `CARDINAL_WORKDIR` setting):

```bash
make -s print-crontab
```

Add the crontab entry to the operating system user's crontab file:

```bash
make -s print-crontab | crontab
```

This must be run:

- by the operating system user that will run the cron job,
- from any directory containing the `Makefile` and `config.mk` files.

## Clean

If desired, you can delete the `kingfisher-collect` and `cardinal-rs` directories, which are downloaded by the `build` target, but aren't needed after building images:

```bash
make clean-build
```

If you need to start over, delete the cron job manually. Then, delete the `ecuador_sercop_bulk.ini` file and the `data`, `logs` and `scratch` directories:

```bash
make force-clean
```

## Reference

This process replicates the configuration in the [incremental](https://github.com/open-contracting/deploy/blob/main/salt/kingfisher/collect/incremental.sls) state from the [deploy](https://ocdsdeploy.readthedocs.io/en/latest/) repository.
