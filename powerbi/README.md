# Power BI

To run the SQL commands:

1. Connect to the server as the `incremental` user:

    ```bash
    ssh incremental@ocp23.open-contracting.org
    ```

1. Connect to the `kingfisher_collect` database as the `kingfisher_collect` user:

    ```bash
    psql postgresql://kingfisher_collect@localhost/kingfisher_collect
    ```

## General

### `{spider}` tables

[Kingfisher Collect](https://kingfisher-collect.readthedocs.io/en/latest/) crawls data sources, and inserts OCDS data into SQL tables. The schema is:

```sql
CREATE TABLE {spider} (
    data jsonb
);
CREATE INDEX idx_{spider} ON {spider} USING btree (((data ->> 'date'::text)));
```

### `{spider}_result` tables

[Cardinal](https://cardinal.readthedocs.io/en/latest/) calculates indicators, and inserts results into tables. The schema is:

```sql
CREATE TABLE {spider}_result (
  id SERIAL,                              /* an auto-incrementing ID that has no semantics */
  ocid text,                              /* matches /ocid in the compiled release JSON */
  subject text,                           /* the indicator's scope, one of OCID, Buyer, ProcuringEntity, Tenderer */
  code text,                              /* the indicator's code */
  result numeric,                         /* an individual indicator result */
  buyer_id text,                          /* matches /buyer/id in the JSON */
  procuring_entity_id text,               /* matches /tender/procuringEntity/id in the JSON */
  tenderer_id text,                       /* matches /bids/details[]/tenderers[]/id in the JSON */
  created_at timestamp without time zone, /* the time when this row was added */
  PRIMARY KEY (id)
);
```

- An indicator triggers at most once per entity (`ocid`, `buyer_id`, `procuring_entity_id` or `tenderer_id`). However, we “spread” the non-OCID results across multiple contracting processes. So, the unique key (if we were to add one) would be (`ocid`, `code`, `buyer_id`, `procuring_entity_id`, `tenderer_id`).
- Each row is about only one entity. For example, if a contracting process is flagged (`ocid`) and the same contracting process has both a buyer that is flagged (`buyer_id`) and a tenderer that is flagged (`tenderer_id`), there will be 3 rows, not 1. For example:

  | ocid | subject | code | buyer_id | tenderer_id |
  | - | - | - | - | - |
  | ocds-213czf-1 | OCID | NF024 | | |
  | ocds-213czf-1 | Buyer | NF038 | 1 | |
  | ocds-213czf-1 | Tenderer | NF025 | | 3 |

To manually insert results during development, run, for example:

```bash
psql postgresql://kingfisher_collect@localhost/kingfisher_collect -c \
"\copy dominican_republic_api_result (ocid, subject, code, result, buyer_id, procuring_entity_id, tenderer_id, created_at) FROM stdin DELIMITER ',' CSV HEADER;" < /tmp/results.csv
```

### `indicator` table

*Purpose:* Lookup categories, titles and descriptions of [Cardinal indicator](https://cardinal.readthedocs.io/en/latest/cli/indicators/index.html#list) codes.

*Update frequency:* As needed, when new indicators are implemented.

*Install:*

```sql
CREATE TABLE indicator (
  id SERIAL,
  code text,
  category text,
  title text,
  description text,
  category_es text,
  title_es text,
  description_es text,
  PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ON indicator (code);
```

```console
$ psql postgresql://kingfisher_collect@localhost/kingfisher_collect -c \
"\copy indicator (code,category,title,description,category_es,title_es,description_es) FROM stdin DELIMITER ',' CSV HEADER;"
code,category,title,description,category_es,title_es,description_es
R023,Collusion detection,Fixed-multiple bid prices,The percentage difference between two tenderers' bid prices is the same in different contracting processes,Detección de colusión,Diferencia similar entre precios de oferta,La diferencia porcentual entre los precios de oferta de dos oferentes es la misma en distintos procesos de contratación
R024,Collusion detection,Price close to winning bid,The percentage difference between the winning bid and the second-lowest valid bid is a low outlier,Detección de colusión,Precio cercano a la oferta ganadora,La diferencia porcentual entre la oferta ganadora y la segunda oferta válida más baja es un valor atípico bajo
R025,Collusion detection,Excessive unsuccessful bids,The ratio of winning bids to submitted bids for a top tenderer is a low outlier,Detección de colusión,Número excesivo de ofertas no exitosas,La relación entre las ofertas ganadoras y las presentadas por un oferente es un valor atípico bajo
R035,Risks to suppliers,All except winning bid disqualified,Bids are disqualified if not submitted by the single tenderer of the winning bid,Riesgos de adjudicación,Todas las ofertas son descalificadas excepto la ganadora,Las ofertas presentadas son descalificadas excepto la  ganadora
R036,Risks to suppliers,Lowest bid disqualified,"The lowest submitted bid is disqualified, while the award criterion is price only",Riesgos de adjudicación,Oferta más baja descalificada,La oferta más baja es descalificada cuando el criterio de adjudicación es solo precio
R038,Risks to suppliers,Excessive disqualified bids,"The ratio of disqualified bids to submitted bids is a high outlier per buyer, procuring entity or tenderer",Riesgos de adjudicación,Alto número de ofertas descalificadas,La relación de ofertas descalificadas y las presentadas es un valor atípico alto para un comprador o un oferente
R028,Collusion detection,Identical bid prices,Two bids submitted by different tenderers have the same price,Detección de colusión,Precios de oferta idénticos,Dos ofertas presentadas por diferentes oferentes tienen el mismo precio
R030,Risks to suppliers,Late bid won,The winning bid was received after the submission deadline,Riesgos de adjudicación,Oferta tardía gana,La oferta ganadora fue recibida después de la fecha límite de presentación
R048,Risks to suppliers,Heterogeneous supplier,The variety of items supplied by a tenderer is a high outlier,Riesgos de adjudicación,Proveedor multipropósito,La variedad de artículos suministrados por un oferente es un valor atípico alto
R058,Collusion detection,Heavily discounted bid,The percentage difference between the winning bid and the second-lowest valid bid is a high outlier,Detección de colusión,Oferta con precio muy bajo,La diferencia porcentual entre la oferta ganadora y la segunda oferta válida más baja es un valor atípico alto
\.
```

### `codelist` table

*Purpose:* Lookup translations of English codes that occur in the OCDS data.

*Update frequency:* As needed, when new codes need translations.

*Install:*

```sql
CREATE TABLE codelist (
  id SERIAL,
  codelist text,
  code text,
  code_es text,
  PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ON codelist (codelist, code);
```

```console
$ psql postgresql://kingfisher_collect@localhost/kingfisher_collect -c \
"\copy codelist (codelist,code,code_es) FROM stdin DELIMITER ',' CSV HEADER;"
codelist,code,code_es
method,open,abierto
method,selective,selectivo
method,limited,limitado
method,direct,directo
tenderStatus,pending,pendiente
tenderStatus,active,activo
tenderStatus,cancelled,cancelado
tenderStatus,unsuccessful,sin éxito
bidStatus,pending,pendiente
bidStatus,valid,calificada
bidStatus,disqualified,descalificada
bidStatus,InTreatment,pendiente
bidStatus,Qualified,calificada
bidStatus,Disqualified,descalificada
partyRole,bidder,oferente
partyRole,supplier,proveedor
\.
```

## Dominican Republic (DO)

### `unspsc` table

*Purpose:* Lookup descriptions of [United Nations Standard Products and Services Code (UNSPSC)](https://www.unspsc.org) codes.

*Source:* OCP has parts of UNPSC in [English](https://docs.google.com/spreadsheets/d/1_aVRybL5hF9o1uYKD5NcATQQGFyc9eGGcja3oaJo4EM/edit#gid=527001288) and [Spanish](https://docs.google.com/spreadsheets/d/1r0qC1hPMw4XBBx7CUP1xnZeLD0CgOe_yAocLomOeVXQ/edit#gid=1593824065). English and Spanish labels were manually combined for 2-digit codes.

*Update frequency:* Every few years.

*Install:* Upload the `unspsc.csv` file from this repository to `/tmp/unspsc.csv`.

```sql
CREATE TABLE unspsc (
  id SERIAL,
  code integer,
  description text,
  description_es text,
  PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ON unspsc (code);
```

```bash
psql postgresql://kingfisher_collect@localhost/kingfisher_collect -c \
"\copy unspsc (code, description, description_es) FROM stdin DELIMITER ',' CSV HEADER;" < /tmp/unspsc.csv
```

### `excluded_supplier` table

*Purpose:* Display the "Proportion of contracting processes for buyer with debarred suppliers" chart.

*Source:* The Dominican Republic publishes [debarred suppliers](https://datosabiertos.dgcp.gob.do/opendata/tablas) (*proveedores inhabilitados*) in CSV format.

*Update frequency:* Monthly.

*Install:*

```sql
CREATE TABLE excluded_supplier (
  id SERIAL,
  identifier text,
  PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ON excluded_supplier (identifier);
```

```bash
curl -sS https://api.dgcp.gob.do/opendata/proveedores/proveedores_inhabilitados.csv | grep -Eo '^[0-9]+,' | sed -E 's/^(.+),$/DO-RPE-\1/' | sort -u > /tmp/excluded_supplier.csv
```

```bash
psql postgresql://kingfisher_collect@localhost/kingfisher_collect -c \
"\copy excluded_supplier (identifier) FROM stdin DELIMITER ',' CSV HEADER;" < /tmp/excluded_supplier.csv
```

## Ecuador (EC)

### `cpc` table

*Purpose:* Purpose: Lookup descriptions of [Central Product Classification (CPC)](https://unstats.un.org/unsd/classifications/Econ/CPC.cshtml) codes.

*Source:* [Ecuador](https://aplicaciones2.ecuadorencifras.gob.ec/SIN/metodologias/CPC%202.0.pdf) (2012-06) publishes CPC Ver. 2 with different Spanish labels than [UNSD](https://unstats.un.org/unsd/classifications/Econ/CPC.cshtml). (CPC 2.1 contains new codes, in English only). English labels from UNSD and Spanish labels from Ecuador were manually combined for 1, 2 and 3-digit codes.

*Update frequency:* Every few years.

*Install:* Upload the `cpc.csv` file from this repository to `/tmp/cpc.csv`.

```sql
CREATE TABLE cpc (
  id SERIAL,
  code text,
  description text,
  description_es text,
  PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ON cpc (code);
```

```bash
psql postgresql://kingfisher_collect@localhost/kingfisher_collect -c \
"\copy cpc (code, description, description_es) FROM stdin DELIMITER ',' CSV HEADER;" < /tmp/cpc.csv
```
