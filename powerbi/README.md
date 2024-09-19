# Power BI

Follow these instructions to deploy [Kingfisher Collect](https://kingfisher-collect.readthedocs.io/en/latest/) and [Cardinal](https://cardinal.readthedocs.io/en/latest/) using Docker.

The `Makefile` makes this easy to setup. You can configure it by changing the variables in `config.mk`.

All commands assume that the current directory is the "working directory" for the project. The local user must have read, write and execute permissions to the working directory.

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

Run `make database` as a local user with the [CREATEDB](https://www.postgresql.org/docs/current/sql-createrole.html) privilege (for example, as the `postgres` user):

```bash
make -s database
```

This will:

- Create a PostgreSQL database (the `DATABASE_NAME` configuration, by default `cardinal`), if it doesn't exist
- Create a PostgreSQL user (the `DATABASE_USER` configuration, by default `cardinal`), if it doesn't exist
- Create the `ecuador_sercop_bulk_result` table, owned by the PostgreSQL user, if it doesn't exist
- Create (or re-create) the `codelist`, `indicator` and `cpc` tables, owned by the PostgreSQL user

The PostgreSQL host is set by the `DATABASE_HOST` configuration, by default `localhost`.

This assumes that the local user can authenticate with PostgreSQL without a password. This can be done in a few ways:

1. Configure the [pg_bha.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html) file to allow the local user to login as the PostgreSQL user with the same name. For example, for the `postgres` user:

  ```none
  local all postgres peer
  ```

1. Create a [.pgpass](https://www.postgresql.org/docs/current/libpq-pgpass.html) file in the local user's home directory. For example:

  ```none
  localhost:5432:cardinal:cardinal:strong-password
  ```

## Filesystem

Run `make filesystem` from the working directory (the `CARDINAL_WORKDIR` configuration) for the project, as the local user that will run the cron job:

```bash
make -s filesystem
```

This will:

- Create `data`, `logs` and `scratch` directories, owned by the local user, if they don't exist
- Download Cardinal's settings file to `ecuador_sercop_bulk.ini`, owned by the local user

## Docker

Run `make build` from any directory (that contains the `Makefile`).

This will:

- Clone the `kingfisher-collect` and `cardinal-rs` repositories into the current directory, if they don't exist
- Download the `Dockerfile_cardinal` and `Dockerfile_python` files to the current directory, if they don't exist
- Pull changes to the `kingfisher-collect` and `cardinal-rs` repositories
- Build the `kingfisher-collect` and `cardinal-rs` images

The `kingfisher-collect` image is for running `scrapy` and `manage.py` commands, like:

```bash
docker run --rm --name kingfisher-collect kingfisher-collect scrapy --help
docker run --rm --name kingfisher-collect kingfisher-collect python manage.py --help
```

The `cardinal-rs` image is for running `ocdscardinal` commands, like:

```bash
docker run --rm --name cardinal-rs cardinal-rs --help
```

## Cron

Preview the crontab entry:

```bash
make -s print-crontab
```

Make sure the directory of the `cron.sh` file in the crontab entry is correct (if not, edit the `CARDINAL_WORKDIR` configuration).

Add the crontab entry to the local user's crontab file:

```bash
make -s print-crontab | crontab
```

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
