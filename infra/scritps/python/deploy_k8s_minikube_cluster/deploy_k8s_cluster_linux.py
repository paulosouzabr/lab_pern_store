import subprocess
import yaml
import time
import os

profile_name = "store"  # Change this to your desired profile name
nodes = 3
cpu = 4
memory = 4096
cni = "calico"
driver = "kvm2"
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

    # First ensure essential packages are installed
    print("Installing essential packages...")
    try:
        run_command("sudo apt-get update -qq")
        run_command("sudo apt-get install -y -qq apt-transport-https ca-certificates curl git python3-pip")
    except Exception as e:
        print(f"Warning: Could not install essential packages: {e}")
        print("Continuing anyway...")
    
    # Install QEMU if not already installed
    print("Checking if KVM2 (libvirt + qemu-kvm) is installed...\n")
    try:
        output = run_command("dpkg -l | grep -E 'libvirt-daemon-system|qemu-kvm'", check_exit_code=False)
        if "libvirt-daemon-system" in output and "qemu-kvm" in output:
            print("KVM2 dependencies appear to be installed.")
        else:
            print("KVM2 dependencies not fully installed. Installing...\n")
            try:
                run_command("sudo apt-get update -qq")
                run_command(
                    "sudo apt-get install -y -qq qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager"
                )
            except Exception as e:
                print(f"Warning: Could not install KVM2 dependencies: {e}")
    except Exception as e:
        print(f"Warning during KVM2 check: {e}")
        print("Attempting to install KVM2 dependencies anyway...")
        try:
            run_command("sudo apt-get install -y -qq qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager")
        except Exception as e:
            print(f"Warning: Could not install KVM2 dependencies: {e}")

    print("Adding current user to 'libvirt' and 'kvm' groups (may require reboot)...")
    try:
        run_command("sudo usermod -aG libvirt $(whoami)")
        run_command("sudo usermod -aG kvm $(whoami)")
    except Exception as e:
        print(f"Warning: Failed to add user to groups: {e}")
    
    # Check for KVM support
    print("Checking for KVM support...")
    kvm_available = False
    try:
        output = run_command("ls -la /dev/kvm", check_exit_code=False)
        if "/dev/kvm" in output:
            kvm_available = True
            print("KVM is available. Adding current user to kvm group...")
            try:
                run_command("sudo usermod -aG kvm $USER", check_exit_code=False)
            except Exception as e:
                print(f"Warning: Could not add user to kvm group: {e}")
    except Exception:
        pass
    
    if not kvm_available:
        print("KVM not available. This may affect performance.")
        print("Make sure virtualization is enabled in BIOS if supported.")
    
    try:
        output = run_command("getent group libvirt", check_exit_code=False)
        if "libvirt" in output:
            print("Adding current user to libvirt group...")
            try:
                run_command("sudo usermod -aG libvirt $USER", check_exit_code=False)
            except Exception as e:
                print(f"Warning: Could not add user to libvirt group: {e}")
        else:
            print("libvirt group does not exist, this is normal if libvirt is not installed.")
    except Exception:
        print("Could not check for libvirt group. Continuing...")
    
    # Install kubectl
    print("\nChecking if kubectl is installed...\n")
    kubectl_installed = False
    try:
        output = run_command("which kubectl", check_exit_code=False)
        if "/kubectl" in output:
            kubectl_installed = True
            print("kubectl is already installed.")
    except Exception:
        pass
    
    if not kubectl_installed:
        print("\nKubectl not found. Installing kubectl...\n")
        kubectl_installed = False

        try:
            run_command('curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
                        chmod +x kubectl && \
                        sudo mv kubectl /usr/local/bin/ && \
                        kubectl version --client --output=yaml')
            kubectl_installed = True
        except Exception as e:
            print(f"Warning: Could not install kubectl via direct download: {e}")
        
        if not kubectl_installed:
            print("Failed to install kubectl using any method. Please install manually.")
            print("Continuing with script execution...")
    
    # Install minikube
    print("\nChecking if minikube is installed...\n")
    minikube_installed = False
    try:
        output = run_command("which minikube", check_exit_code=False)
        if "/minikube" in output:
            minikube_installed = True
            print("minikube is already installed.")
    except Exception:
        pass
    
    if not minikube_installed:
        print("\nMinikube not found. Installing minikube...\n")
        try:
            print("Trying to install minikube via direct download...")
            try:
                run_command("wget -q https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 -O minikube")
            except Exception:
                print("wget failed, trying curl...")
                run_command("curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64")
            
            run_command("chmod +x minikube")
            run_command("sudo mv minikube /usr/local/bin/")
            print("minikube installed successfully.")
        except Exception as e:
            print(f"Warning: Could not install minikube: {e}")
            print("Please install minikube manually.")
            print("Continuing with script execution...")

def start_minikube():
    print(f"Starting Minikube with {nodes} nodes...\n")
    run_command(f"minikube start -n={nodes} --cni={cni} --driver={driver} --cpus={cpu} --memory={memory} --disk-size={disk_size} -p {profile_name}")
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
        run_command(f"minikube addons enable {addon} -p {profile_name}")

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
        # deploy_first_deployment()  # Uncomment if you want to deploy the sample application
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()