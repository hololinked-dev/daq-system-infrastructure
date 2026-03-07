# DAQ System Infrastructure (Docker)

Project to setup a infrastructure for a networked data acquisition system or IoT based on docker. Tailored for usage with [`hololinked`](https://github.com/hololinked-dev/hololinked).

> There will be a separate version for Kubernetes, little late in the future, consider contributing if you need earlier.

The approach would be to use a python CLI to read configuration files (TOML) and then use `docker compose` to start the services.
The CLI's main job is to create environment variable files (dotenv).

## Components

- **Keycloak**: Identity and Access Management (IAM) server for authentication and authorization.
- **PostgreSQL**: Database server to store data. Mandatory for keycloak.
- **CloudBeaver**: Web-based database management tool for SQL-like or select databases.
- **Mosquitto**: MQTT broker.
- **MongoDB** (optional): NoSQL database. Either of MongoDB or PostgreSQL can be used with `hololinked`.
- **MongoExpress**: Mongo Database viewer and management tool.

# Documentation

Please visit [https://docs.hololinked.dev/daq-system-infrastructure](https://docs.hololinked.dev/daq-system-infrastructure).
