# PetStore API

A simple Flask-based API service for the PetStore sandbox environment.

## Endpoints

### Health Check

GET /health

### Catalog

GET /catalog

Retrieves product data from the catalog-service.

## Local Development

Build:

```bash
docker build -t petstore-api .
