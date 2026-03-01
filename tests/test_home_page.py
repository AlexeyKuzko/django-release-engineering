from http import HTTPStatus

import pytest

from django_educational_demo_application.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_home_page_renders_project_readme(client):
    user = UserFactory()
    client.force_login(user)
    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert b"Dashboard" in response.content
    assert b"Educational Project Management" in response.content


def test_home_page_requires_login(client):
    response = client.get("/")

    assert response.status_code == HTTPStatus.FOUND
    assert "/accounts/login/" in response.url
