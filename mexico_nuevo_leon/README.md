# Mexico Nuevo León

[`manage.py`](manage.py) reads collections from a MongoDB database (and, for public OCDS data, from CKAN) and writes them to a PostgreSQL database, for consumption by the business intelligence tool.

## Install

The requirements files are in the repository's root directory. Run the commands below from there.

The production requirements pin `psycopg[c]`, which is compiled against the system `libpq`. Installing them therefore requires a build toolchain and the PostgreSQL client headers (for example, `build-essential` and `libpq-dev` on Debian/Ubuntu, or `build-base` and `libpq-dev` on Alpine):

```bash
pip install -r requirements.txt
```

If you don't have a build toolchain, install the pre-built binary of psycopg against the shared requirements instead, which don't pin psycopg:

```bash
pip install "psycopg[binary]" -r requirements_base.txt
```

For local development, use the development requirements, which pin `psycopg[binary]` (no build toolchain needed):

```bash
pip install -r requirements_dev.txt
```

## Usage

```bash
python mexico_nuevo_leon/manage.py --help
```
