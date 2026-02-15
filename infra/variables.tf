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

variable "app_domain" {
  description = "FQDN of the app, used by DNS and TLS."
  type        = string
  default     = "app.example.com"
}

variable "manage_dns" {
  description = "Create/manage DNS zone and A record in Yandex Cloud DNS."
  type        = bool
  default     = false
}

variable "dns_zone" {
  description = "Base DNS zone, e.g. example.com"
  type        = string
  default     = "example.com"
}

variable "dns_zone_resource_name" {
  description = "Terraform resource name for Yandex DNS zone."
  type        = string
  default     = "diploma-zone"
}
