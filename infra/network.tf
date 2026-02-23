resource "yandex_vpc_network" "main" {
  name = "${local.resource_prefix}-network"
}

resource "yandex_vpc_gateway" "nat" {
  name = "${local.resource_prefix}-nat-gateway"

  shared_egress_gateway {}
}

resource "yandex_vpc_route_table" "private" {
  name       = "${local.resource_prefix}-private-rt"
  network_id = yandex_vpc_network.main.id

  static_route {
    destination_prefix = "0.0.0.0/0"
    gateway_id         = yandex_vpc_gateway.nat.id
  }
}

resource "yandex_vpc_subnet" "public" {
  name           = "${local.resource_prefix}-public-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = [var.public_cidr]
}

resource "yandex_vpc_subnet" "private" {
  name           = "${local.resource_prefix}-private-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.main.id
  route_table_id = yandex_vpc_route_table.private.id
  v4_cidr_blocks = [var.private_cidr]
}

resource "yandex_vpc_address" "app_public_ip" {
  name = "${local.resource_prefix}-app-public-ip"

  external_ipv4_address {
    zone_id = var.zone
  }
}
