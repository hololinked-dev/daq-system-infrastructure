# DAQ System Infrastructure (Docker)

Project to setup a infrastructure for a networked data acquisition system or IoT based on docker.
Suitable for usage with [`hololinked`](https://github.com/hololinked-dev/hololinked) or any DAQ or IoT platform in general.
There will be a separate version for Kubernetes.

## Components

- **Keycloak**: Identity and Access Management (IAM) server for authentication and authorization.
- **PostgreSQL**: Database server to store data. Mandatory for keycloak.
- **CloudBeaver**: Web-based database management tool for PostgreSQL.
- **MongoDB** (optional): NoSQL database. Either of MongoDB or PostgreSQL can be used with `hololinked`.

## Prerequisites

- Docker Engine

## Installation

Export a dotenv file with the following variables:

```
POSTGRES_ADMIN=postgres
POSTGRES_ADMIN_PASSWORD=mysecretpassword
CLOUDBEAVER_ADMIN=admin
CLOUDBEAVER_ADMIN_PASSWORD=mysecretpassword2
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=mysecretpassword3
```

Then:

```bash
docker-compose up -d postgres dbeaver keycloak
```

Or, if you wish to use all services including MongoDB:

```bash
docker-compose up -d
```

Four workspaces will be created in the current directory to persist data:

- `data/postgres`: PostgreSQL data
- `data/dbeaver`: CloudBeaver data
- `data/keycloak`: Keycloak data
- `data/mongo`: MongoDB data (if using MongoDB)

#### Variables

- **Postgres**:

| Name                          | Description                                                                                                                       | Default Value              |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| `POSTGRES_ADMIN`              | PostgreSQL admin username                                                                                                         | `postgres`                 |
| `POSTGRES_ADMIN_PASSWORD`     | PostgreSQL admin password                                                                                                         | `postgrespassword`         |
| `POSTGRES_MULTIPLE_DATABASES` | Comma-separated list of databases to create. Please ensure that the default databases are also created if you intend to use them. | `keycloak, hololinked`     |
| `POSTGRES_NONADMIN_PASSWORD`  | General password for non-admin users (`keycloak`, `hololinked`)                                                                   | `postgresnonadminpassword` |

- **CloudBeaver**:

| Name                         | Description                                                                                                            | Default Value   |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------- |
| `CLOUDBEAVER_ADMIN`          | CloudBeaver admin username                                                                                             | `admin`         |
| `CLOUDBEAVER_ADMIN_PASSWORD` | CloudBeaver admin password, generally requires a strong password otherwise you will be reprompted to create once again | `adminpassword` |

- **Keycloak**:

| Name                      | Description             | Default Value   |
| ------------------------- | ----------------------- | --------------- |
| `KEYCLOAK_ADMIN`          | Keycloak admin username | `admin`         |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin password | `adminpassword` |

- **MongoDB**:

If you wish to use mongoDB with `hololinked`,

`docker compose -f compose-mongo.yml up -d`

with the following environment variables:

| Name                          | Description                  | Default Value   |
| ----------------------------- | ---------------------------- | --------------- |
| `MONGO_ADMIN`                 | MongoDB admin username       | `mongoadmin`    |
| `MONGO_ADMIN_PASSWORD`        | MongoDB admin password       | `mongopassword` |
| `MONGOEXPRESS_ADMIN`          | Mongo Express admin username | `admin`         |
| `MONGOEXPRESS_ADMIN_PASSWORD` | Mongo Express admin password | `adminpassword` |

### Database Migrations

To apply database migrations for `hololinked`, you can use the following command:

```bash
alembic -c postgresql://<POSTGRES_ADMIN>:<POSTGRES_ADMIN_PASSWORD>@localhost:5432/hololinked upgrade head
```

A list of migration versions and their compatibility with the current version can be found in the `alembic/versions` directory of the `hololinked` repository.
