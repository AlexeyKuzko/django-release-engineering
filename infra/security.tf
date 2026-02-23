resource "yandex_vpc_security_group" "app_sg" {
  name       = "${local.resource_prefix}-app-sg"
  network_id = local.network_id

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTPS"
    port           = 443
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_vpc_security_group" "db_sg" {
  name       = "${local.resource_prefix}-db-sg"
  network_id = local.network_id

  ingress {
    protocol          = "TCP"
    description       = "SSH from App"
    port              = 22
    security_group_id = yandex_vpc_security_group.app_sg.id
  }

  ingress {
    protocol       = "TCP"
    description    = "SSH from App subnet"
    port           = 22
    v4_cidr_blocks = [local.public_subnet_cidr]
  }

  ingress {
    protocol          = "TCP"
    description       = "Postgres from App"
    port              = 5432
    security_group_id = yandex_vpc_security_group.app_sg.id
  }

  ingress {
    protocol       = "TCP"
    description    = "Postgres from App subnet"
    port           = 5432
    v4_cidr_blocks = [local.public_subnet_cidr]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_vpc_security_group" "monitoring_sg" {
  name       = "${local.resource_prefix}-monitoring-sg"
  network_id = local.network_id

  ingress {
    protocol       = "TCP"
    port           = 3000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    port           = 9090
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}
