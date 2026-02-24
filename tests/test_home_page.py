from http import HTTPStatus
from pathlib import Path

import pytest

from config import views

pytestmark = pytest.mark.django_db


def test_home_page_renders_project_readme(client):
    response = client.get("/")
    response_html = response.content.decode()
    first_heading = Path("README.md").read_text(encoding="utf-8").splitlines()[0]

    assert response.status_code == HTTPStatus.OK
    assert "<h1" in response_html
    assert first_heading.replace("# ", "") in response_html


def test_home_page_fallback_if_readme_missing(client, monkeypatch, tmp_path):
    monkeypatch.setattr(views, "README_PATH", tmp_path / "README.md")

    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert "README.md not found." in response.content.decode()
