# DAQ System Infrastructure

Project to setup a infrastructure for a networked data acquisition system or IoT.

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