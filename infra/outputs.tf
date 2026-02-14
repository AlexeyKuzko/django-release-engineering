output "app_public_ip" {
  value = yandex_compute_instance.app.network_interface.0.nat_ip_address
}

output "monitoring_public_ip" {
  value = yandex_compute_instance.monitoring.network_interface.0.nat_ip_address
}

output "db_private_ip" {
  value = yandex_compute_instance.db.network_interface.0.ip_address
}
