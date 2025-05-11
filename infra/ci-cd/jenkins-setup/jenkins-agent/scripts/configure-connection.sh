#!/bin/bash

# Set variables
JENKINS_URL="http://jenkins.jenkins.svc.cluster.local:8080"
JENKINS_USER="admin"
JENKINS_PASS="admin123"  # Change this to your Jenkins admin password

# Wait for Jenkins to be ready
until $(curl --output /dev/null --silent --head --fail ${JENKINS_URL}); do
    printf '.'
    sleep 5
done

# Get Jenkins crumb for authentication
CRUMB=$(curl -s --user "${JENKINS_USER}:${JENKINS_PASS}" \
    "${JENKINS_URL}/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)")

# Configure the Kubernetes cloud in Jenkins
curl -X POST "${JENKINS_URL}/configureClouds" \
    --user "${JENKINS_USER}:${JENKINS_PASS}" \
    -H "${CRUMB}" \
    -H "Content-Type:application/xml" \
    --data-binary "@../config/jenkins-agent.yaml"

# Verify the agent connection
echo "Waiting for agent to connect..."
kubectl wait --for=condition=Ready pod -l app=jenkins-agent -n jenkins --timeout=300s

echo "Jenkins agent configuration completed!"
echo "Please check the Jenkins UI to verify the agent connection."