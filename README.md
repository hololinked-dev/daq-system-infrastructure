# DAQ System Infrastructure (Docker)

Project to setup a infrastructure for a networked data acquisition system or IoT based on docker.
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

#### Variables

- **Postgres**:

| Name                        | Description                                         | Default Value    |
| --------------------------- | --------------------------------------------------- | ---------------- |
| POSTGRES_ADMIN              | PostgreSQL admin username                           | postgres         |
| POSTGRES_ADMIN_PASSWORD     | PostgreSQL admin password                           | postgrespassword |
| POSTGRES_MULTIPLE_DATABASES | Comma-separated list of databases to create         |                  |
| POSTGRES_NONADMIN_PASSWORD  | Password for non-admin users (keycloak, hololinked) | nonadminpassword |

- **CloudBeaver**:

| Name                       | Description                | Default Value |
| -------------------------- | -------------------------- | ------------- |
| CLOUDBEAVER_ADMIN          | CloudBeaver admin username | admin         |
| CLOUDBEAVER_ADMIN_PASSWORD | CloudBeaver admin password | adminpassword |

- **Keycloak**:

| Name                    | Description             | Default Value |
| ----------------------- | ----------------------- | ------------- |
| KEYCLOAK_ADMIN          | Keycloak admin username | admin         |
| KEYCLOAK_ADMIN_PASSWORD | Keycloak admin password | adminpassword |
