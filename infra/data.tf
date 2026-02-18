data "yandex_compute_image" "ubuntu_2204_lts" {
  family = var.os_image_family
}
