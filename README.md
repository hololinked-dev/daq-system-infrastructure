# DAQ System Infrastructure (Docker)

Project to setup a infrastructure for a networked data acquisition system or IoT based on docker.
Suitable for usage with [`hololinked`](https://github.com/hololinked-dev/hololinked) or any DAQ or IoT platform in general.
There will be a separate version for Kubernetes.

## Components

- **PostgreSQL**: Database server to store data.
- **Keycloak**: Identity and Access Management (IAM) server for authentication and authorization.
- **CloudBeaver**: Web-based database management tool for PostgreSQL.

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
docker-compose up -d
```

Three workspaces will be created in the current directory to persist data:

- `postgres-workspace`: PostgreSQL data
- `dbeaver-workspace`: CloudBeaver data
- `keycloak-workspace`: Keycloak data

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
