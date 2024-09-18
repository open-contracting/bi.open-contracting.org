# Power BI

This directory contains files to support deploying [Kingfisher Collect](https://kingfisher-collect.readthedocs.io/en/latest/) and [Cardinal](https://cardinal.readthedocs.io/en/latest/) using Docker.

The `Makefile` makes this easy to setup. You can configure it by changing the variables in `config.mk`.

To print the commands that a `make` target would execute, use the `-n` (`--dry-run`) option. For example:

```bash
make -n database
```

To run all targets (setup the database and filesystem, build the images, and install the crontab), run:

```bash
make -s
make -s print-crontab | crontab
```

## PostgreSQL

Run `make database` as a local user with the [CREATEDB](https://www.postgresql.org/docs/current/sql-createrole.html) privilege (for example, as the `postgres` user):

```bash
make -s database
```

This will:

- Create a database (`cardinal`, by default), if it doesn't exist
- Create a user (`cardinal`, by default), if it doesn't exist
- Create the `ecuador_sercop_bulk_result` table, owned by the user, if it doesn't exist
- Create (or re-create) the `codelist`, `indicator` and `cpc` tables, owned by the user

## Filesystem

Run `make filesystem` from the working directory for the project.

```bash
make -s filesystem
```

This will:

- Create `data`, `logs` and `scratch` directories
- Download Cardinal's settings file to `ecuador_sercop_bulk.ini`

## Docker

Run `make build` to build two images:

- `kingfisher-collect`, for running `scrapy` and `manage.py` commands, like:

  ```bash
  docker run --rm --name kingfisher-collect kingfisher-collect scrapy --help
  docker run --rm --name kingfisher-collect kingfisher-collect python manage.py --help
  ```

- `cardinal`, for running `ocdscardinal` commands, like

  ```bash
  docker run --rm --name cardinal-rs cardinal-rs --help
  ```

This clones the `kingfisher-collect` and `cardinal-rs` repositories into the current directory.

## Cron

Preview the crontab entry:

```bash
make -s print-crontab
```

Add the crontab entry:

```bash
make -s print-crontab | crontab
```

## Reference

This process replicates the configuration in the [incremental](https://github.com/open-contracting/deploy/blob/main/salt/kingfisher/collect/incremental.sls) state from the [deploy](https://ocdsdeploy.readthedocs.io/en/latest/) repository.
