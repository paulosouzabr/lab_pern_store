import subprocess
import yaml
import time
import os

profile_name = "store" # Change this to your desired profile name"
nodes = 3
cpu = 4
memory = 8192
cni = "calico"
driver = "qemu"
disk_size = "50g"

def run_command(command, check_exit_code=True):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output_lines = []

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            output_lines.append(output.strip())

    stderr = process.stderr.read()
    if stderr:
        for line in stderr.splitlines():
            print(line.strip())
            output_lines.append(line.strip())

        if check_exit_code and not any(msg in stderr.lower() for msg in ["level=info", "level=warning"]):
            raise Exception(stderr)

    rc = process.poll()
    if check_exit_code and rc != 0:
        raise Exception(f"Command failed with return code {rc}")

    return '\n'.join(output_lines)


def pre_flight():
    try:
        print(f"Checking if qemu is installed...\n")
        run_command("brew list |grep qemu")
    except Exception:
        print(f"Qemu not found. Installing Qemu...\n")
        run_command("brew install qemu")

    try:
        print(f"Checking if socket_vmnet is installed...\n")
        run_command("brew list |grep socket_vmnet")
    except Exception:
        print(f"socket_vmnet not found. Installing socket_vmnet...\n")
        run_command("brew install socket_vmnet")

    try:
        print(f"\nChecking if minikube is installed...\n")
        run_command("minikube version")
    except Exception:
        print(f"\nMinikube not found. Installing minikube...\n")
        run_command("brew install minikube")

def start_minikube():
    print(f"Starting Minikube with 3 nodes...\n")
    run_command(f"minikube start -n={nodes} --cni={cni} --driver={driver} --cpus={cpu} --memory={memory} --disk-size={disk_size} -p {profile_name} ")
    run_command(f"minikube status -p {profile_name}")
    print(f"The k8s cluster is ready to configure the addons...\n")

def enable_addons():
    addons = [
        "volumesnapshots",
        "csi-hostpath-driver",
        "default-storageclass",
        "ingress",
        "ingress-dns",
        "metallb",
        "metrics-server",
        "storage-provisioner",
        "registry"
    ]
    for addon in addons:
        print(f"Enabling addon: {addon}...")
        run_command(f"minikube addons enable {addon} -p {profile_name} ")

def configure_metallb():
    print("Configuring MetalLB...")
    minikube_ip = run_command(f"minikube ip -p {profile_name}").strip()
    ip_parts = minikube_ip.split('.')
    subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
    ip_range = f"{subnet}.100-{subnet}.200"

    yamls_folder = r'./yamls'
    if not os.path.exists(yamls_folder):
        os.makedirs(yamls_folder)

    metallb_config = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "namespace": "metallb-system",
            "name": "config"
        },
        "data": {
            "config": yaml.dump({
                "address-pools": [
                    {
                        "name": "default",
                        "protocol": "layer2",
                        "addresses": [ip_range]
                    }
                ]
            }, default_flow_style=False)
        }
      }

    config_yaml = yaml.dump(metallb_config, default_flow_style=False)
    with open(f'./yamls/{profile_name}-metallb-config.yaml', "w") as f:
        f.write(config_yaml)

    run_command(f"kubectl --context={profile_name} apply -f ./yamls/{profile_name}-metallb-config.yaml")

def deploy_first_deployment():
    minikube_ip = run_command(f"minikube ip -p {profile_name}").strip()

    print("Deploying first-deployment application...")

    yamls_folder = r'./yamls'
    if not os.path.exists(yamls_folder):
        os.makedirs(yamls_folder)

    first_deployment_deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "first-deployment",
            "namespace": "default"
        },
        "spec": {
            "replicas": 4,
            "selector": {
                "matchLabels": {
                    "app": "first-deployment"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "first-deployment"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "first-deployment",
                            "image": "nginx",
                            "ports": [
                                {
                                    "containerPort": 80
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }

    first_deployment_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "first-deployment",
            "namespace": "default"
        },
        "spec": {
            "selector": {
                "app": "first-deployment"
            },
            "ports": [
                {
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 80
                }
            ],
            "type": "ClusterIP"
        }
    }

    first_deployment_ingress = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "first-deployment-ingress",
            "namespace": "default",
            "annotations": {
                "nginx.ingress.kubernetes.io/rewrite-target": "/"
            }
        },
        "spec": {
            "rules": [
                {
                    "host": f"first.{minikube_ip}.nip.io",
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "first-deployment",
                                        "port": {
                                            "number": 80
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    resources = [first_deployment_deployment, first_deployment_service]
    ingress_deploy = [first_deployment_ingress]

    for resource in resources:
        config_yaml = yaml.dump(resource)
        resource_name = resource['metadata']['name']
        with open(f"./yamls/{profile_name}-{resource_name}.yaml", "w") as f:
            f.write(config_yaml)
        try:
            run_command(f"kubectl --context={profile_name} apply -f ./yamls/{profile_name}-{resource_name}.yaml")
            time.sleep(5)
        except Exception as e:
            print(f"An error occurred while applying {resource_name}: {e}")

    for ingress in ingress_deploy:
        config_yaml = yaml.dump(ingress)
        resource_name = ingress['metadata']['name']
        with open(f"./yamls/{profile_name}-{resource_name}.yaml", "w") as f:
            f.write(config_yaml)
        try:
            run_command(f"kubectl --context={profile_name} apply -f ./yamls/{profile_name}-{resource_name}.yaml")
        except Exception as e:
            print(f"An error occurred while applying ingress {resource_name}: {e}")

def main():
    try:
        pre_flight()
        start_minikube()
        enable_addons()
        configure_metallb()
        #deploy_first_deployment()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
