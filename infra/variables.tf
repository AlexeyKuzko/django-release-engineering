variable "yc_token" {}
variable "cloud_id" {}
variable "folder_id" {}

variable "zone" {
  default = "ru-central1-a"
}

variable "public_cidr" {
  default = "10.10.1.0/24"
}

variable "private_cidr" {
  default = "10.10.2.0/24"
}

variable "ssh_public_key" {}
