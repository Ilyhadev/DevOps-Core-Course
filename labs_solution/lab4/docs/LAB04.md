# Lab 04 — Infrastructure as Code Documentation

**Cloud Provider:** Yandex Cloud  
**IaC Tools:** Terraform v1.14.5 + Pulumi v3.220.0

---

## 1. Cloud Provider & Infrastructure

### Cloud Provider Selection

- **Provider:** Yandex Cloud
- **Region/Zone:** ru-central1-b
- **Rationale:** Free tier availability, suitable for testing IaC concepts without costs

### Infrastructure Specifications

| Component | Specification |
|-----------|---------------|
| Instance Type | standard-v2 (fractional) |
| vCPU | 2 cores @ 20% core fraction |
| Memory | 2 GB RAM |
| Storage | 10 GB network-ssd boot disk |
| OS | Ubuntu 24.04 LTS |
| Network | Custom VPC with subnet |
| Estimated Cost | $0 USD (free tier) |

### Resources Created

Both Terraform and Pulumi deployed identical infrastructure:

| Resource | Type | Details |
|----------|------|---------|
| VPC Network | `yandex_vpc_network` | lab04-network (10.128.0.0/16) |
| Subnet | `yandex_vpc_subnet` | lab04-subnet (10.128.0.0/24 in ru-central1-b) |
| Security Group | `yandex_vpc_security_group` | lab04-sg with 4 rules (SSH:22, HTTP:80, APP:5000, Egress:ANY) |
| Compute Instance | `yandex_compute_instance` | lab04-vm (2vCPU@20%, 2GB RAM, 10GB SSD) |

---

## 2. Terraform Implementation

### Tools & Versions

- **Terraform:** v1.14.5
- **Yandex Provider:** v0.187.0
- **Language:** HCL (HashiCorp Configuration Language)

### Project Structure

```
terraform/
├── main.tf               # VPC, subnet, security group, compute instance
├── variables.tf          # Input variable declarations
├── outputs.tf            # VM instance ID and public IP exports
├── terraform.tfvars      # Runtime configuration values (gitignored)
├── terraform.tfstate     # State tracking file (gitignored)
├── .terraform/           # Downloaded provider plugins
├── .terraform.lock.hcl   # Lock file for reproducible deployments
└── README.md             # Setup and usage instructions
```

### Key Configuration Decisions

1. **Variable-driven configuration:** All values (cloud_id, folder_id, instance specs) extracted to variables for template reusability
2. **SSH security hardening:** SSH access restricted to single IP CIDR (`51.250.124.22/32`) instead of open (`0.0.0.0/0`)
3. **Inline security group rules:** Rules defined within security group resource (native HCL pattern)
4. **Custom VPC isolation:** Dedicated VPC and subnet created for infrastructure isolation
5. **Data source for images:** Dynamic image lookup instead of hardcoded IDs ensures latest Ubuntu LTS version

### Challenges & Solutions

| Challenge | Root Cause | Solution |
|-----------|-----------|----------|
| Provider authentication | Missing credentials | Set `YC_SERVICE_ACCOUNT_KEY_FILE` env variable |
| Zone mismatch | Zone specified only in provider | Added zone to both provider and instance config |
| Image ID discovery | Cannot hardcode image IDs | Used `data.yandex_compute_image` data source |
| SSH access failure | Incorrect metadata format | Format as `username:public-key` in metadata field |

### Execution & Verification

#### Step 1: Initialize Terraform
```bash
$ terraform init
```

**Output:** Provider plugin yandex v0.187.0 installed successfully  


#### Step 2: Plan Infrastructure
```bash
$ terraform plan
```

**Output Summary:**
- Infrastructure audit against remote state
- Plan: 1 to add (compute instance)
- Resources required: VPC, Subnet, Security Group, Instance


#### Step 3: Apply Infrastructure
```bash
$ terraform apply
```

**Deployment Results:**
- **Instance ID:** epd8mm4pk2mpamkh1vhe
- **Public IP:** 158.160.92.144
- **Internal IP:** 10.128.0.24
- **Creation Time:** ~51 seconds

 - Infrastructure successfully created

#### Step 4: SSH Connectivity Test
```bash
$ ssh -l ubuntu 158.160.95.138
```

**Result:**
```
Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-53-generic x86_64)

System information as of Tue Feb 17 09:42:26 AM UTC 2026
  System load:  0.0
  Memory usage: 9%
  IPv4 address for eth0: 10.128.0.24

ubuntu@epd8mm4pk2mpamkh1vhe:~$
```

**Verification:**
-  SSH public key authentication working
-  Ubuntu system responsive
-  Network connectivity confirmed
-  User `ubuntu` accessible with correct SSH key

 - Full VM connectivity verified

**Screenshot Note:** A screenshot showing the SSH terminal with successful connection prompt and Ubuntu login banner would be beneficial here for visual proof.

#### Step 5: Destroy Infrastructure
```bash
$ terraform destroy
```

**Destruction Summary:**
- Compute instance destroyed: 33 seconds
- Security group removed: 1 second
- Subnet removed: 7 seconds
- VPC network removed: immediate

**Total Destruction Time:** ~41 seconds  
**Resources Deleted:** 4/4 

 - All infrastructure successfully cleaned up

** Screenshot Note:** Yandex Cloud console showing empty resources in the region would provide visual confirmation of cleanup.

---

## Pulumi Implementation

### Tools & Versions

- **Pulumi:** v3.220.0
- **Language:** Python 3.12
- **Provider:** pulumi-yandex v0.6.0

### Project Structure

```
pulumi/
├── __main__.py           # Infrastructure code (Python/imperative approach)
├── requirements.txt
├── Pulumi.yaml           # Project metadata (name, runtime, description)
├── Pulumi.dev.yaml       # Stack configuration (cloud_id, folder_id, etc)
├── README.md             # Setup and usage instructions
├── .gitignore            # Excludes venv, .pulumi/, state files
├── venv/                 # Python virtual environment
└── .pulumi/              # Pulumi state and configuration
```

### Key Differences from Terraform

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Paradigm** | Declarative (HCL DSL) | Imperative (Python code) |
| **Language Features** | Limited (count, for_each) | Full Python features |
| **Rules Definition** | Inline in security group | Separate VpcSecurityGroupRule resources |
| **State Management** | Local or remote tfstate | Pulumi Cloud or self-hosted |
| **Testing** | External tools required | Native Python unit tests |
| **Debugging** | Limited logging | Full Python debug capabilities |

### Code Pattern Comparison

**Terraform (HCL - Declarative):**
```hcl
resource "yandex_vpc_network" "lab_network" {
  name = "lab04-network"
}

resource "yandex_vpc_security_group" "lab_sg" {
  name = "lab04-sg"
  network_id = yandex_vpc_network.lab_network.id
  
  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.my_ip_cidr]
  }
}
```

**Pulumi (Python - Imperative):**
```python
lab_network = yandex.VpcNetwork(
    "lab_network",
    name="lab04-network"
)

lab_sg = yandex.VpcSecurityGroup(
    "lab_sg",
    name="lab04-sg",
    network_id=lab_network.id
)

ssh_rule = yandex.VpcSecurityGroupRule(
    "ssh-rule",
    security_group_binding=lab_sg.id,
    direction="ingress",
    protocol="TCP",
    from_port=22,
    to_port=22,
    v4_cidr_blocks=[my_ip_cidr]
)
```

### Challenges & Solutions

| Challenge | Root Cause | Solution |
|-----------|-----------|----------|
| Config key prefix missing | Yandex config uses "yandex:" prefix | Read config with `pulumi.Config("yandex")` |
| Security group rule syntax | Used wrong parameter name | Changed to `security_group_binding` (not `security_group_binding_id`) |
| SSH key metadata format | Used dict key as username | Fixed to proper format: `"ssh-keys": f"{user}:{key}"` |

### Execution & Verification

#### Step 1: Install Dependencies
```bash
$ cd pulumi
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

**Packages Installed:**
- pulumi 3.220.0
- pulumi-yandex 0.6.0
- setuptools 65.0.0+
- wheel 0.40.0+



#### Step 2: Configure Stack
```bash
$ pulumi config set yandex:cloud_id <cloud-id>
$ pulumi config set yandex:folder_id <folder-id>
$ pulumi config set zone ru-central1-b
$ pulumi config set my_ip_cidr "51.250.124.22/32"
```

**Configuration Set:**
- Cloud ID: <cloud-id>
- Folder ID: <folder-id>
- Zone: ru-central1-b
- SSH IP restriction: 51.250.124.22/32



#### Step 3: Preview Deployment
```bash
$ pulumi preview
```

**Preview Output:**
```
Previewing update (dev)

Resources to create:
  + pulumi:pulumi:Stack                   lab04-pulumi-dev
  + ├─ yandex:index:VpcNetwork            lab_network
  + ├─ yandex:index:VpcSubnet             lab_subnet
  + ├─ yandex:index:VpcSecurityGroup      lab_sg
  + ├─ yandex:index:VpcSecurityGroupRule  ssh-rule
  + ├─ yandex:index:VpcSecurityGroupRule  http-rule
  + ├─ yandex:index:VpcSecurityGroupRule  app-rule
  + ├─ yandex:index:VpcSecurityGroupRule  egress-rule
  + └─ yandex:index:ComputeInstance       lab_vm

Outputs:
  instance_id: [unknown]
  internal_ip: [unknown]
  public_ip:   [unknown]
  vm_name:     "lab04-vm"

Resources: + 9 to create
```

**Key Finding:** 9 resources vs Terraform's 5 because Pulumi requires separate VpcSecurityGroupRule resources (architectural difference, same final infrastructure)

 - Preview shows all required resources

**Note:** The discrepancy in resource count (9 vs 5) demonstrates different IaC philosophies - Terraform's inline rules vs Pulumi's explicit resource separation. Both create identical security group configuration in Yandex Cloud.

#### Step 4: Apply Infrastructure
```bash
$ pulumi up --yes
```

**Deployment Output:**
```
Updating (dev)

  Type                                 Name              Status
+ pulumi:pulumi:Stack                lab04-pulumi-dev  created (71s)
+ ├─ yandex:index:VpcNetwork         lab_network       created (2s)
+ ├─ yandex:index:VpcSubnet          lab_subnet        created (1s)
+ ├─ yandex:index:VpcSecurityGroup   lab_sg            created (2s)
+ ├─ yandex:index:ComputeInstance    lab_vm            created (64s)
+ ├─ yandex:index:VpcSecurityGroupRule ssh-rule        created (1s)
+ ├─ yandex:index:VpcSecurityGroupRule http-rule       created (2s)
+ ├─ yandex:index:VpcSecurityGroupRule egress-rule     created (2s)
+ └─ yandex:index:VpcSecurityGroupRule app-rule        created (3s)

Outputs:
  instance_id: "<instance-id>"
  internal_ip: "<internal-ip>"
  public_ip:   "178.154.198.112"
  vm_name:     "lab04-vm"

Duration: 1m14s
```

**Deployment Results:**
- **Instance ID:** <instance-id>
- **Public IP:** 178.154.198.112
- **Internal IP:** <internal-ip>
- **VM Name:** lab04-vm
- **Total Creation Time:** 74 seconds (longer than Terraform due to larger resource count)

 - Infrastructure successfully deployed

#### Step 5: SSH Connectivity Test
```bash
$ ssh -i ~/.ssh/lab04_id_rsa ubuntu@178.154.198.112 \
  "echo 'SSH connection successful!' && uname -a"
```

**Result:**
```
The authenticity of host '178.154.198.112' can't be established.
ED25519 key fingerprint is SHA256:qq+0JsmXg31ohd0BcNxtI0VBqwR0wQABLfBt72H4lnk.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '178.154.198.112' (ED25519) to known_hosts.

SSH connection successful!
Linux <instance-id> 6.8.0-53-generic #55-Ubuntu SMP PREEMPT_DYNAMIC Fri Jan 17 15:37:52 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
```

**Verification:**
-  SSH public key authentication working
-  Ubuntu 24.04 system responsive
-  Network connectivity confirmed
-  Correct SSH key format in metadata

 - Full VM connectivity verified

**Screenshot Note:** Terminal showing SSH connection sequence and system information would provide visual evidence.

#### Step 6: Destroy Infrastructure
```bash
$ pulumi destroy --yes
```

**Destruction Output:**
```
Destroying (dev)

  Type                                 Name              Status
- yandex:index:VpcSecurityGroupRule app-rule          deleted (2s)
- yandex:index:VpcSecurityGroupRule ssh-rule          deleted (2s)
- yandex:index:VpcSecurityGroupRule http-rule         deleted (3s)
- yandex:index:VpcSecurityGroupRule egress-rule       deleted (3s)
- yandex:index:ComputeInstance      lab_vm            deleted (68s)
- yandex:index:VpcSubnet            lab_subnet        deleted (5s)
- yandex:index:VpcSecurityGroup     lab_sg            deleted (2s)
- yandex:index:VpcNetwork           lab_network       deleted (1s)
- pulumi:pulumi:Stack               lab04-pulumi-dev  deleted (0.34s)

Resources: - 9 deleted
Duration: 1m19s
```

**Deletion Summary:**
- All 9 resources successfully deleted
- Security group rules cleaned first (proper dependency order)
- Compute instance deleted: 68 seconds
- Network infrastructure removed: 1 second

 - All infrastructure successfully cleaned up

**Screenshot Note:** Yandex Cloud console screenshot showing no resources remaining would confirm cleanup.

---

## 4.Terraform vs Pulumi Comparison

### Ease of Learning

**Terraform:**
- HCL syntax similar to JSON/YAML - familiar to most developers
- Declarative nature makes intended state clear
- Large community and extensive documentation
- Good for teams with mixed technical backgrounds

**Pulumi:**
- Python familiar to many developers, but requires understanding provider APIs
- Steeper initial learning curve for infrastructure concepts
- More powerful for those comfortable with programming
- Smaller community than Terraform

**Winner:** Terraform for beginners; Pulumi for experienced programmers

---

### Code Readability

**Terraform:**
- Pure readability focused on infrastructure clarity
- DSL syntax minimizes cognitive load
- Clear resource boundaries
- Easy to scan and understand configuration

**Pulumi:**
- Python code is readable but can become complex
- Mixing logic with infrastructure definition
- Better for dynamic/conditional infrastructure
- IDE support (autocomplete, type hints) improves readability

**Winner:** Terraform for static infrastructure; Pulumi for complex scenarios

---

### Use Cases

**Choose Terraform When:**
-  Team has mixed technical backgrounds
-  Infrastructure is relatively static
-  Portability between tools matters
-  Strong emphasis on code readability for non-programmers
-  Need extensive community support and examples
-  Compliance requires audit trail of configuration changes

**Choose Pulumi When:**
-  Team has strong programming background
-  Infrastructure is complex and dynamic
-  Need full language features (loops, functions, classes)
-  Testing infrastructure code is priority
-  Secrets management important (encrypted by default)
-  Rapid iteration on infrastructure changes
-  Sharing code patterns via libraries/packages

---

## 5. Lab Cleanup & Summary

### Deployment Summary

| Tool | Status | Resources | Duration | Cost |
|------|--------|-----------|----------|------|
| Terraform |  Completed | 4 created, 4 destroyed | ~2 min total | $0 |
| Pulumi |  Completed | 9 created, 9 destroyed | ~2.5 min total | $0 |

### Infrastructure Cleanup Status

**Terraform Infrastructure:**  DESTROYED
- All 4 resources removed from Yandex Cloud
- State file preserved for reference
- No associated costs

**Pulumi Infrastructure:**  DESTROYED
- All 9 resources removed from Yandex Cloud
- Pulumi stack removed with `pulumi stack rm dev`
- No associated costs

### Why Both Destroyed After Testing

Both cloud VMs have been destroyed to:
1. Avoid unnecessary costs
2. Clean up resources before Lab 5
3. Demonstrate full infrastructure cleanup capability

### For Lab 5

On next week i will use teraform to create VM on yandex cloud

**Terraform**
```bash
cd terraform
terraform init
terraform apply --auto-approve
```


---

## Key Learnings & Observations

### Terraform Observations
- Execution was straightforward and fast
- Plan output clearly showed expected changes
- HCL syntax intuitive for infrastructure definition
- State management worked seamlessly

### Pulumi Observations
- Python implementation offers familiar syntax for programmers
- Separate security group rule resources (vs inline) creates more resources
- Initial setup required more environment configuration

### General IaC Insights
1. **Resource Representation:** Different tools may represent same infrastructure differently (9 vs 5 resources)
2. **Trade-offs:** Declarative (Terraform) vs Imperative (Pulumi) each have distinct advantages
3. **State Management Matters:** Both tools track state; understanding state is crucial for IaC
4. **Idempotency:** Both tools are idempotent - running multiple times produces same result

---

## File Organization

```
lab4/
├── terraform/              # Terraform implementation
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars    (gitignored)
│   ├── .terraform/         (gitignored)
│   └── README.md
├── pulumi/                 # Pulumi implementation
│   ├── __main__.py
│   ├── requirements.txt
│   ├── Pulumi.yaml
│   ├── Pulumi.dev.yaml     (gitignored)
│   ├── venv/               (gitignored)
│   ├── .pulumi/            (gitignored)
│   └── README.md
└── docs/
    ├── LAB04.md            # This documentation
    └── screenshots
        ├── terraform
        └── pulumi
```

---

## Conclusion

Lab 04 successfully demonstrated Infrastructure as Code using two different paradigms (declarative HCL vs imperative Python), with full infrastructure lifecycle management (create, verify, destroy).

**Ready for Lab 5:** Infrastructure code and experience in place for next week's Ansible implementation.
