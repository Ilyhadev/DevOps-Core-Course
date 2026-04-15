# Lab 04 — Terraform
This folder contains a minimal Terraform template for creating a VM in Yandex Cloud for the course lab.

What I added:
- `main.tf` — template resources (network, subnet, security group, compute instance)
- `variables.tf` — variables used by the template
- `outputs.tf` — outputs for the VM
- `terraform.tfvars.example` — example values; copy to `terraform.tfvars` and fill
- `.gitignore` — ignores state and credentials

Quick steps (local):

1. Generate SSH keys

2. Fill `terraform/terraform.tfvars` by copying `terraform.tfvars.example` and providing real values.

3. Export Yandex Cloud credentials or configure Application Default Credentials.
   See Yandex Cloud docs. Typical method is creating a service account and setting `YC_SERVICE_ACCOUNT_KEY_FILE` or using `gcloud`-style ADC.

4. Initialize and apply (in `terraform/`):
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

5. After apply, Terraform prints `public_ip`. Connect via SSH:
   ```bash
   ssh -l <username> ${var.ssh_user}@<public_ip>
   ```

Notes:
- See all outputs and reasoning at /terraform/docs/ folder!
