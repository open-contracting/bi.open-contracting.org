# Power BI

This directory contains files to support deploying [Kingfisher Collect](https://kingfisher-collect.readthedocs.io/en/latest/) and [Cardinal](https://cardinal.readthedocs.io/en/latest/) using Docker. It replicates the configuration in the [incremental](https://github.com/open-contracting/deploy/blob/main/salt/kingfisher/collect/incremental.sls) state from the [deploy](https://ocdsdeploy.readthedocs.io/en/latest/) repository.

Running `make` builds two images:

- `kingfisher-collect`, for running `scrapy` and `manage.py` commands, like:

  ```bash
  docker run --rm --name kingfisher-collect kingfisher-collect scrapy --help
  docker run --rm --name kingfisher-collect kingfisher-collect python manage.py --help
  ```

- `cardinal`, for running `ocdscardinal` commands, like

  ```bash
  docker run --rm --name cardinal-rs cardinal-rs --help
  ```
