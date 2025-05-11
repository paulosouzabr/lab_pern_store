#!/bin/bash

# Build the Jenkins agent image
docker build -t jenkins-agent:latest -f ../config/dockerfile .

# Create the Jenkins namespace if it doesn't exist
kubectl create namespace jenkins --dry-run=client -o yaml | kubectl apply -f -

# Apply RBAC configurations
kubectl apply -f ../kubernetes/agent-rbac.yaml

# Create a secret for the Jenkins agent
# Note: Replace 'your-jenkins-secret' with the actual secret from Jenkins
kubectl create secret generic jenkins-agent-secret \
  --from-literal=jenkins-agent-secret='your-jenkins-secret' \
  --namespace jenkins \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy the Jenkins agent
kubectl apply -f ../kubernetes/agent-deployment.yaml

echo "Jenkins agent setup completed!"