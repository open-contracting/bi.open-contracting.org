# Power BI

Follow these instructions to deploy [Kingfisher Collect](https://kingfisher-collect.readthedocs.io/en/latest/) and [Cardinal](https://cardinal.readthedocs.io/en/latest/) using Docker.

The [`Makefile`](Makefile) makes this easy to setup. You can configure it by changing the settings in the [`env.public`](env.public) file.

You must choose an operating system user with read, write and execute permissions to the "working directory" for the project (`chmod 700`, at least). For simplicity, you can:

- Name the operating system user the same as the database user (`DATABASE_USER` setting)
- Create a home directory for the operating system user, to use as the working directory (`CARDINAL_WORKDIR` setting)
- Make the working directory readable and executable by others (`chmod 755`)
- Change the current directory to the working directory when running the commands below

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

Download the [`Makefile`](Makefile) to the current directory:

```bash
curl -sSLO https://raw.githubusercontent.com/open-contracting/bi.open-contracting.org/refs/heads/main/powerbi/Makefile
```

Download the [`env.public`](env.public), [`cron.sh`](cron.sh) and [`env.private`](env.private) files to the current directory, if they don't exist, and restrict permissions to the `env.private` file (`chmod go-rwx`):

```bash
make setup
```

Lastly, edit the `env.public` and `env.private` files. At minimum, set the `DATABASE_PASSWORD` setting in the `env.private` file to a [strong password](https://www.lastpass.com/features/password-generator).

## Database (PostgreSQL)

These commands connect to the database server set by the `DATABASE_HOST` setting, by default `localhost`, on the port set by the `DATABASE_PORT` setting, by default `5432`.

### Create database and user

This step requires a **maintenance database user** (`MAINTENANCE_DATABASE_USER` setting, by default `postgres`) with the privileges:

- [`CREATEDB`](https://www.postgresql.org/docs/current/sql-createrole.html) database privilege
- `CREATEROLE` database privilege
- [`CONNECT`](https://www.postgresql.org/docs/current/ddl-priv.html) object privilege to the **maintenance database** (`MAINTENANCE_DATABASE_NAME` setting, by default `postgres`)

Run `make -s createdb createuser` to:

- Create the **project database** (`DATABASE_NAME` setting, by default `cardinal`), owned by the **maintenance database user**, if it doesn't exist
- Create the **project database user** (`DATABASE_USER` setting, by default `cardinal`), if it doesn't exist

  It will prompt for the project database user's password. Enter the same password as the `DATABASE_PASSWORD` setting.

This must be run:

- by any operating system user,
- from any directory in which the user can read the `Makefile` and `env.public` files,
- to which the operating system user has read and execute permissions.

The simplest option is to run this command as the `postgres` operating system user, which has the necessary privileges.

This command requires you to authenticate as the **maintenance database user**. Either enter the password when prompted, or, to skip the password prompt:

- Run the command as the `postgres` operating system user, since the default [`pg_hba.conf`](https://www.postgresql.org/docs/current/auth-g-hba-conf.html) file allows local `peer` connections as the `postgres` database user to all databases.
- Create a [`.pgpass`](https://www.postgresql.org/docs/current/libpq-pgpass.html) file in the operating system user's home directory, and set its permissions to owner-readable only (`chmod 400`). For example:

  ```none
  localhost:5432:maintenance-database-name:maintenance-database-user:strong-password
  ```

### Create tables

Run `make -s tables` to:

- Create (or re-create) the `codelist`, `indicator`, `cpc`, `unspsc` and `excluded_supplier` tables, owned by the **project database user**

If you don't need the `excluded_supplier` table or only need one of the `cpc` or `unspsc` tables, you can modify the `tables` target in the `Makefile`, or run the individual targets you need, like:

```none
make -s codelist
make -s indicator
# One of:
make -s cpc
make -s unspsc
# If applicable:
make -s excluded_supplier
```

This must be run:

- by any operating system user,
- from any directory in which the user can read the `Makefile` and `env.public` files,
- to which the operating system user has read and execute permissions.

This command requires you to authenticate as the **project database user**. Either enter the password when prompted, or, to skip the password prompt:

- Set the `DATABASE_USER` setting to the name of the operating system user that will run the [cron job](#cron), since the default [`pg_hba.conf`](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) file allows local `peer` connections as any database user to all databases.
- Create a [`.pgpass`](https://www.postgresql.org/docs/current/libpq-pgpass.html) file in the operating system user's home directory, and set its permissions to owner-readable only (`400`). For example:

  ```none
  localhost:5432:project-database-name:project-database-user:strong-password
  ```

## Docker

Run `make build` to:

- Clone the [`kingfisher-collect`](https://github.com/open-contracting/kingfisher-collect) and [`cardinal-rs`](https://github.com/open-contracting/cardinal-rs) repositories into the current directory, if they don't exist
- Download the [`Dockerfile_cardinal`](Dockerfile_cardinal) and [`Dockerfile_python`](Dockerfile_python) files to the current directory, if they don't exist
- Pull changes for the `kingfisher-collect` and `cardinal-rs` repositories
- Build the `kingfisher-collect` and `cardinal-rs` images

This must be run:

- by any operating system user,
- from any directory in which the user can read the `Makefile`,
- to which the user has read, write and execute permissions.

This command requires you to have write permission to the [Docker daemon's Unix socket](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user), which is owned by the `root` user and `docker` group. Either run the command with `sudo`, or add the operating system user to the `docker` group.

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
- Download [Cardinal's settings file](https://github.com/open-contracting/deploy/tree/main/salt/kingfisher/collect/files/cardinal/) to `cardinal.ini`, owned by the current operating system user

This must be run:

- by the operating system user that will run the [cron job](#cron),
- from the working directory for the project (same as the `CARDINAL_WORKDIR` setting).

## Cron

The [`cron.sh` script](cron.sh) creates a container from the [`kingfisher-collect` image](#docker). This container needs network access to the database server. If the database server is running on the same machine as the cron job, then the simplest option is to:

- Set `listen_addresses = '*'`, either in the [`postgresql.conf`](https://www.postgresql.org/docs/current/config-setting.html) file or in a configuration file under the `conf.d` directory
- Configure the [`pg_hba.conf`](https://www.postgresql.org/docs/current/auth-g-hba-conf.html) file to allow connections from the [IP addresses](https://docs.docker.com/engine/network/#ip-address-and-hostname) allocated by the Docker daemon. For example:

  ```none
  hostssl all all 0.0.0.0/0 scram-sha-256
  hostssl all all ::/0      scram-sha-256
  ```

  This assumes that an external firewall closes the port of the database server to external connections.

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
- from any directory in which the user can read the `Makefile`, `env.public` and `env.private` files, and read and execute the `cron.sh` file.

We recommend also setting the `MAILTO` environment variable in the user's crontab, to be notified of any errors.

## Clean

If desired, you can delete the `kingfisher-collect` and `cardinal-rs` directories, which are downloaded by the `build` target, but aren't needed after building images:

```bash
make clean-build
```

If you need to start over, delete the cron job manually. Then, delete the `cardinal.ini` file and the `data`, `logs` and `scratch` directories:

```bash
make force-clean
```

### Excluded suppliers

If you use the `excluded_supplier` table, you need to schedule a cron job to update the table. For example, for the Dominican Republic, this script can run daily:

```bash
#!/usr/bin/env bash

set -euo pipefail

# https://datosabiertos.dgcp.gob.do/opendata/tablas
curl -sSk https://api.dgcp.gob.do/opendata/proveedores/proveedores_inhabilitados.csv |
    # The first column is the RPE.
    grep -Eo '^[0-9]+,' |
    # Sort numerically and uniquely.
    sort -nu |
    # Prefix the identifier scheme.
    sed -E 's/^(.+),$/DO-RPE-\1/' |
    # Replace the table in a transaction.
    psql -U kingfisher_collect -h localhost -q -c "BEGIN; DELETE FROM excluded_supplier; COPY excluded_supplier (identifier) FROM stdin; END;"
```

## Disk usage

Kingfisher Collect writes:

- data files to the `data/` directory (>20GB). This directory must not be deleted; otherwise, contracting processes are lost, because Kingfisher Collect downloads only new files.
- data to a table whose name matches the Kingfisher Collect spider (for example, `ecuador_sercop_bulk`, ~10GB). This table must not be dropped; otherwise, Kingfisher Collect re-downloads all old files, instead of only new files.
- log files to the `logs/` directory (<10MB each). To control disk usage, set up log rotation on this directory.

The [cron job](#cron) writes:

- contracting processes to a table whose name suffixes `_clean` to the Kingfisher Collect spider (`ecuador_sercop_bulk_clean`, ~10GB). This table is read by Power BI.
- indicator results to a table whose name suffixes `_result` to the Kingfisher Collect spider (`ecuador_sercop_bulk_result`, ~50MB). This table is read by Power BI.
- temporary files (~15GB), that are deleted by the end of the script.

As such, the project requires about 50GB for both permanent and temporary data.

## Reference

This process replicates the configuration in the [`incremental`](https://github.com/open-contracting/deploy/blob/main/salt/kingfisher/collect/incremental.sls) state from the [`deploy`](https://ocdsdeploy.readthedocs.io/en/latest/) repository.
