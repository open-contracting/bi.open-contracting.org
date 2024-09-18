# Power BI

This directory contains files to support deploying [Kingfisher Collect](https://kingfisher-collect.readthedocs.io/en/latest/) and [Cardinal](https://cardinal.readthedocs.io/en/latest/) using Docker. It replicates the configuration in the [incremental](https://github.com/open-contracting/deploy/blob/main/salt/kingfisher/collect/incremental.sls) state from the [deploy](https://ocdsdeploy.readthedocs.io/en/latest/) repository.

The `Makefile` makes this easy to setup. You can configure it by changing the variables in `config.mk`.

To print the commands that a `make` target would execute, use the `-n` (`--dry-run`) option. For example:

```bash
make -n db
```

## PostgreSQL

Run `make db` as a local user with the [CREATEDB](https://www.postgresql.org/docs/current/sql-createrole.html) privilege (for example, as the `postgres` user):

```bash
make -s db
```

This will:

- Create a database (`cardinal`, by default), if it doesn't exist
- Create a user (`cardinal`, by default), if it doesn't exist
- Create the `ecuador_sercop_bulk_result` table, owned by the user, if it doesn't exist
- Create (or re-create) the `codelist`, `indicator` and `cpc` tables, owned by the user

## Docker

Running `make build` builds two images:

- `kingfisher-collect`, for running `scrapy` and `manage.py` commands, like:

  ```bash
  docker run --rm --name kingfisher-collect kingfisher-collect scrapy --help
  docker run --rm --name kingfisher-collect kingfisher-collect python manage.py --help
  ```

- `cardinal`, for running `ocdscardinal` commands, like

  ```bash
  docker run --rm --name cardinal-rs cardinal-rs --help
  ```

## Cron

Add a crontab entry, after updating the path. For example:

```bash
echo "15 0 * * * /path/to/bin/cron.sh" | crontab
```
