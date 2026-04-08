"""
Lab 04 - Pulumi Infrastructure as Code
Recreate the same VM infrastructure from Terraform using Pulumi and Python
This is an imperative approach vs Terraform's declarative HCL syntax
"""

import pulumi
import pulumi_yandex as yandex
import os

# Read configuration
config = pulumi.Config()
yandex_config = pulumi.Config("yandex")
cloud_id = yandex_config.require("cloud_id")
folder_id = yandex_config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
instance_name = config.get("instance_name") or "lab04-vm"
cores = int(config.get("cores") or "2")
core_fraction = int(config.get("core_fraction") or "20")
memory = int(config.get("memory") or "2")
boot_disk_size = int(config.get("boot_disk_size") or "10")
ssh_user = config.get("ssh_user") or "ubuntu"
my_ip_cidr = config.get("my_ip_cidr") or "0.0.0.0/0"

# Read SSH public key from file
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/lab04_id_rsa.pub"
ssh_public_key_path = os.path.expanduser(ssh_public_key_path)

try:
    with open(ssh_public_key_path, "r") as f:
        ssh_public_key = f.read().strip()
except FileNotFoundError:
    raise Exception(f"SSH public key not found at {ssh_public_key_path}")

# Create VPC Network
lab_network = yandex.VpcNetwork(
    "lab_network",
    name="lab04-network"
)

# Create Subnet
lab_subnet = yandex.VpcSubnet(
    "lab_subnet",
    name="lab04-subnet",
    zone=zone,
    network_id=lab_network.id,
    v4_cidr_blocks=["10.128.0.0/24"]
)

# Create Security Group
lab_sg = yandex.VpcSecurityGroup(
    "lab_sg",
    name="lab04-sg",
    network_id=lab_network.id,
    description="Allow SSH, HTTP, and app port 5000 from my IP"
)

# Add SSH ingress rule
ssh_rule = yandex.VpcSecurityGroupRule(
    "ssh-rule",
    security_group_binding=lab_sg.id,
    direction="ingress",
    protocol="TCP",
    from_port=22,
    to_port=22,
    v4_cidr_blocks=[my_ip_cidr],
    description="ssh"
)

# Add HTTP ingress rule
http_rule = yandex.VpcSecurityGroupRule(
    "http-rule",
    security_group_binding=lab_sg.id,
    direction="ingress",
    protocol="TCP",
    from_port=80,
    to_port=80,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="http"
)

# Add app port 5000 ingress rule
app_rule = yandex.VpcSecurityGroupRule(
    "app-rule",
    security_group_binding=lab_sg.id,
    direction="ingress",
    protocol="TCP",
    from_port=5000,
    to_port=5000,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="app port 5000"
)

# Add egress rule for all outbound traffic
egress_rule = yandex.VpcSecurityGroupRule(
    "egress-rule",
    security_group_binding=lab_sg.id,
    direction="egress",
    protocol="ANY",
    from_port=-1,
    to_port=-1,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="allow all outbound"
)

# Get the latest Ubuntu 24.04 LTS image
ubuntu_image = yandex.get_compute_image(
    family="ubuntu-24-04-lts"
)

# Create the VM instance
lab_vm = yandex.ComputeInstance(
    "lab_vm",
    name=instance_name,
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=cores,
        core_fraction=core_fraction,
        memory=memory
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=boot_disk_size,
            type="network-ssd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=lab_subnet.id,
            nat=True
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}"
    },
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(
        preemptible=False
    ),
    labels={
        "lab": "lab04"
    }
)

# Export outputs
pulumi.export("instance_id", lab_vm.id)
pulumi.export("public_ip", lab_vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_name", lab_vm.name)
pulumi.export("internal_ip", lab_vm.network_interfaces[0].ip_address)
