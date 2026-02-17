variable "cloud_id" {
  description = "Yandex Cloud cloud id"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder id where resources will be created"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud zone (e.g. ru-central1-a)"
  type        = string
  default     = "ru-central1-a"
}

variable "instance_name" {
  description = "Name of the VM instance"
  type        = string
  default     = "lab04-vm"
}


variable "cores" {
  description = "Number of cores"
  type        = number
  default     = 2
}

variable "core_fraction" {
  description = "Core fraction for standard-v2 fractional CPU"
  type        = number
  default     = 20
}

variable "memory" {
  description = "Memory in MB"
  type        = number
  default     = 1024
}

variable "boot_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key file (used to provision VM metadata)"
  type        = string
  default     = "~/.ssh/lab04_id_rsa.pub"
}

variable "ssh_user" {
  description = "Username for SSH key metadata (cloud image user, e.g. ubuntu)"
  type        = string
  default     = "ubuntu"
}

variable "my_ip_cidr" {
  description = "CIDR used to restrict SSH (set to your public IP/32)"
  type        = string
  default     = "0.0.0.0/0"
}
