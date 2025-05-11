# Jenkins Agent Setup

This repository contains the necessary configurations to set up a Jenkins agent in a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster running
- kubectl configured
- Docker installed
- Jenkins master running in the cluster

## Setup Instructions

1. Configure Jenkins Master:
   - Go to "Manage Jenkins" > "Manage Nodes and Clouds"
   - Add a new permanent agent
   - Note down the agent secret

2. Update Configurations:
   - Replace 'your-jenkins-secret' in the setup script with the actual agent secret
   - Update the JENKINS_URL in agent-deployment.yaml if needed

3. Run the Setup:
```bash
cd scripts
chmod +x setup-agent.sh
./setup-agent.sh
```

4. Verify the Setup:
```bash
kubectl get pods -n jenkins
```

## Troubleshooting

- Check agent logs:
```bash
kubectl logs -n jenkins -l app=jenkins-agent
```

- Check agent connection status in Jenkins UI

## Maintenance

- To update the agent:
```bash
kubectl rollout restart deployment/jenkins-agent -n jenkins
```