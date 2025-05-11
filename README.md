# PERN Store - Kubernetes Learning Project

A full-stack e-commerce application built with the PERN stack (PostgreSQL, Express, React, Node.js) designed to help developers learn Kubernetes deployment concepts.

-> This project was based in [PERN STORE - By Joseph Odunsi](https://github.com/dhatGuy/PERN-Store) - Thank you

## Project Structure

```bash
├── app/
│   ├── backend/            # Node.js/Express backend
│   │   └── server/         # Server implementation
│   └── frontend/           # React frontend application
├── infra/
│   ├── ci-cd/              # CI/CD configurations
│   ├── containers/         # Docker compose files
│   └── scripts/            # Deployment scripts
```

## Features

- Complete e-commerce functionality
- User authentication and authorization
- Shopping cart management
- Product reviews
- Order processing
- Responsive design

## Tech Stack

- **Frontend**: React, Windmill UI, TailwindCSS
- **Backend**: Node.js, Express
- **Database**: PostgreSQL
- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: Jenkins

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (Minikube for local development)

### Local Development

1. Clone the repository:
```sh
git clone https://github.com/paulosouzabr/pern-store.git
```

2. Start the development environment using Docker Compose:
```sh
cd infra/containers/docker-compose
docker-compose up --build
```

3. Access the applications:
- Frontend: http://localhost:3000
- Backend: http://localhost:9000
- PgAdmin: http://localhost:16543

### Kubernetes Deployment

1. Deploy using the provided Python script:
```sh
cd infra/scripts/python/deploy_k8s_minikube_cluster
python deploy_k8s_cluster_macos.py
```

This script will:
- Install required dependencies
- Start Minikube cluster
- Enable necessary addons
- Configure MetalLB
- Deploy the application

## Project Structure for Kubernetes

The project includes examples of various Kubernetes resources:
- Deployments
- Services
- Ingress configurations
- ConfigMaps
- Secrets
- Persistent Volumes
- StatefulSets (for PostgreSQL)

## Environment Configuration

Copy the example environment files and configure them:
```sh
cp app/backend/server/.env.example app/backend/server/.env
cp app/frontend/.env.example app/frontend/.env
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the Apache License.
