locals {
  is_prod_environment = var.environment == "prod"
  use_shared_network  = !local.is_prod_environment
  resource_prefix     = "diploma-${var.environment}"
}
