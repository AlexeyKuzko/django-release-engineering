output "network_id" {
  value = local.network_id
}

output "public_subnet_id" {
  value = local.public_subnet_id
}

output "private_subnet_id" {
  value = local.private_subnet_id
}

output "public_subnet_cidr" {
  value = local.public_subnet_cidr
}

output "private_subnet_cidr" {
  value = local.private_subnet_cidr
}

output "app_public_ip" {
  value = yandex_vpc_address.app_public_ip.external_ipv4_address[0].address
}

output "monitoring_public_ip" {
  value = yandex_compute_instance.monitoring.network_interface.0.nat_ip_address
}

output "db_private_ip" {
  value = yandex_compute_instance.db.network_interface.0.ip_address
}

output "app_domain" {
  value = trimsuffix(var.app_domain, ".")
}

output "dns_zone_id" {
  value = try(yandex_dns_zone.app_zone[0].id, null)
}

output "dns_zone_name" {
  value = var.manage_dns ? "${trimsuffix(var.dns_zone, ".")}." : null
}

output "dns_delegation_name_servers" {
  description = "Name servers to set at registrar when manage_dns=true."
  value = var.manage_dns ? [
    "ns1.yandexcloud.net.",
    "ns2.yandexcloud.net.",
  ] : []
}
