from http import HTTPStatus

import pytest

pytestmark = pytest.mark.django_db


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}
