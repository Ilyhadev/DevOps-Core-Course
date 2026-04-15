terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.74.0"
    }
  }
}

provider "yandex" {
  # Authentication: configure with env vars or application default
  # See README.md for instructions.
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}

resource "yandex_vpc_network" "lab_network" {
  name = "lab04-network"
}

resource "yandex_vpc_subnet" "lab_subnet" {
  name           = "lab04-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab_network.id
  v4_cidr_blocks = ["10.128.0.0/24"]
}

resource "yandex_vpc_security_group" "lab_sg" {
  name        = "lab04-sg"
  network_id  = yandex_vpc_network.lab_network.id
  description = "Allow SSH, HTTP, and app port 5000 from my IP"

  ingress {
    description    = "ssh"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    description    = "http"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "app port 5000"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # allow all outbound traffic
  egress {
    description    = "allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_compute_instance" "lab_vm" {
  name = var.instance_name

  resources {
    cores         = var.cores
    core_fraction = var.core_fraction
    memory        = var.memory
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.boot_disk_size
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.lab_subnet.id
    nat       = true
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  scheduling_policy {
    preemptible = false
  }

  labels = {
    lab = "lab04"
  }
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-24-04-lts"
}