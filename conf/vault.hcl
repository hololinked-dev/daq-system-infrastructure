ui            = true
log_level     = "warn"
disable_mlock = false  # requires IPC_LOCK capability — set on the container

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1  # TLS is terminated by Traefik upstream
}

storage "file" {
  path = "/vault/data"
}