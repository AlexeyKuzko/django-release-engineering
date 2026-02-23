resource "yandex_compute_instance" "monitoring" {
  name        = "${local.resource_prefix}-monitoring-vm"
  platform_id = "standard-v3"

  resources {
    cores  = 2
    memory = 4
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.base_os.id
      size     = 20
    }
  }

  network_interface {
    subnet_id          = local.public_subnet_id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.monitoring_sg.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${var.ssh_public_key}"
  }
}
