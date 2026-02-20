locals {
  app_domain_normalized = trimsuffix(var.app_domain, ".")
  dns_zone_normalized   = trimsuffix(var.dns_zone, ".")
}

resource "yandex_dns_zone" "app_zone" {
  count       = var.manage_dns ? 1 : 0
  name        = var.dns_zone_resource_name
  description = "Managed DNS zone for diploma project"
  zone        = "${local.dns_zone_normalized}."
  public      = true
}

resource "yandex_dns_recordset" "app_a" {
  count   = var.manage_dns ? 1 : 0
  zone_id = yandex_dns_zone.app_zone[0].id
  name    = "${local.app_domain_normalized}."
  type    = "A"
  ttl     = 300
  data    = [yandex_vpc_address.app_public_ip.external_ipv4_address[0].address]
}
