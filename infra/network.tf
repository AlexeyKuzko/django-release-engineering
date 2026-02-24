data "terraform_remote_state" "prod" {
  count   = local.use_shared_network ? 1 : 0
  backend = "s3"
  config = {
    endpoints = {
      s3 = "https://storage.yandexcloud.net"
    }
    bucket = "diploma-terraform-state"
    region = "ru-central1"
    key    = "prod/terraform.tfstate"

    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }
}

resource "yandex_vpc_network" "main" {
  count = 1
  name  = "${local.resource_prefix}-network"
}

resource "yandex_vpc_gateway" "nat" {
  count = 1
  name  = "${local.resource_prefix}-nat-gateway"

  shared_egress_gateway {}
}

resource "yandex_vpc_route_table" "private" {
  count      = 1
  name       = "${local.resource_prefix}-private-rt"
  network_id = yandex_vpc_network.main[0].id

  static_route {
    destination_prefix = "0.0.0.0/0"
    gateway_id         = yandex_vpc_gateway.nat[0].id
  }
}

resource "yandex_vpc_subnet" "public" {
  count          = 1
  name           = "${local.resource_prefix}-public-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.main[0].id
  v4_cidr_blocks = [var.public_cidr]
}

resource "yandex_vpc_subnet" "private" {
  count          = 1
  name           = "${local.resource_prefix}-private-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.main[0].id
  route_table_id = yandex_vpc_route_table.private[0].id
  v4_cidr_blocks = [var.private_cidr]
}

resource "yandex_vpc_address" "app_public_ip" {
  name = "${local.resource_prefix}-app-public-ip"

  external_ipv4_address {
    zone_id = var.zone
  }
}

locals {
  network_id = yandex_vpc_network.main[0].id

  public_subnet_id = yandex_vpc_subnet.public[0].id

  private_subnet_id = yandex_vpc_subnet.private[0].id

  public_subnet_cidr = var.public_cidr

  private_subnet_cidr = var.private_cidr
}
