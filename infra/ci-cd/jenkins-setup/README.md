# Add Jenkins Helm repository
helm repo add jenkins https://charts.jenkins.io
helm repo update

# Create namespace
kubectl create namespace jenkins

# Install Jenkins
helm install jenkins jenkins/jenkins -f infra/ci-cd/jenkins-values.yaml -n jenkins

# Wait for Jenkins to be ready
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/component=jenkins-controller -n jenkins

# Get admin password
kubectl exec --namespace jenkins -it svc/jenkins -c jenkins -- /bin/cat /run/secrets/additional/chart-admin-password