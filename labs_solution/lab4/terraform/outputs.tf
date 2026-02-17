output "instance_id" {
  description = "ID of created instance"
  value       = yandex_compute_instance.lab_vm.id
}

output "public_ip" {
  description = "Public IP address assigned to the VM"
  value       = yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address
}
