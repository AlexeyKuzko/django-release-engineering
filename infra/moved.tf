moved {
  from = yandex_vpc_network.main
  to   = yandex_vpc_network.main[0]
}

moved {
  from = yandex_vpc_gateway.nat
  to   = yandex_vpc_gateway.nat[0]
}

moved {
  from = yandex_vpc_route_table.private
  to   = yandex_vpc_route_table.private[0]
}

moved {
  from = yandex_vpc_subnet.public
  to   = yandex_vpc_subnet.public[0]
}

moved {
  from = yandex_vpc_subnet.private
  to   = yandex_vpc_subnet.private[0]
}
