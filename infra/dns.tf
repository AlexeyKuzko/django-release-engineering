locals {
  app_domain_normalized = trimsuffix(var.app_domain, ".")
  dns_zone_normalized   = trimsuffix(var.dns_zone, ".")
  app_domain_in_dns_zone = (
    local.app_domain_normalized == local.dns_zone_normalized
    || endswith(local.app_domain_normalized, ".${local.dns_zone_normalized}")
  )
  app_domain_is_ipv4 = can(regex("^\\d+\\.\\d+\\.\\d+\\.\\d+$", local.app_domain_normalized))
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

  lifecycle {
    precondition {
      condition     = !local.app_domain_is_ipv4
      error_message = "manage_dns=true requires app_domain to be a DNS name, not an IP address."
    }
    precondition {
      condition = local.app_domain_in_dns_zone
      error_message = "app_domain must be equal to dns_zone or be its subdomain when manage_dns=true. Example: app.dedapp.ru for dns_zone=dedapp.ru."
    }
  }
}
