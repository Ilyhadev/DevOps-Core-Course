# Lab 04 — Pulumi

This folder contains a Pulumi project for creating a VM in Yandex Cloud, implementing the same infrastructure as the Terraform version but using Python (imperative approach).

## Key Differences from Terraform

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Language** | HCL (declarative) | Python (imperative) |
| **Approach** | "Declare what infrastructure should exist" | "Write code to create infrastructure" |
| **State** | terraform.tfstate file | Pulumi service or local backend |
| **Testing** | External tools | Native Python tests |
| **Secrets** | Plain in state | Encrypted |

## Quick Steps

1. **Create Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure stack:**
   ```bash
   pulumi config set yandex:cloud_id YOUR_CLOUD_ID
   pulumi config set yandex:folder_id YOUR_FOLDER_ID
   pulumi config set zone ru-central1-a
   pulumi config set instance_name lab04-vm
   pulumi config set cores 2
   pulumi config set core_fraction 20
   pulumi config set memory 2
   pulumi config set boot_disk_size 10
   pulumi config set ssh_public_key_path ~/.ssh/lab04_id_rsa.pub
   pulumi config set ssh_user ubuntu
   pulumi config set my_ip_cidr YOUR_IP/32
   ```

4. **Preview and deploy:**
   ```bash
   pulumi preview   # See what will be created
   pulumi up        # Deploy infrastructure
   ```

5. **View outputs:**
   ```bash
   pulumi stack output public_ip
   ```

6. **Destroy resources:**
   ```bash
   pulumi destroy
   ```

## Notes

- State is stored locally in `.pulumi/` by default
- Configuration values are in `Pulumi.dev.yaml` (or `.gitignore` sensitive values)
- SSH connection: `ssh -l ubuntu <public_ip>`
- See `__main__.py` for imperative infrastructure definitions
- See `docs/` folder for detailed documentation and terminal outputs
