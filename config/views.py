from pathlib import Path

import markdown
from django.conf import settings
from django.http import JsonResponse
from django.views.generic import TemplateView

README_PATH = Path(settings.BASE_DIR) / "README.md"


def health_view(_request):
    return JsonResponse({"status": "ok"})


def render_readme_as_html() -> str:
    try:
        readme_markdown = README_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "<p>README.md not found.</p>"

    return markdown.markdown(
        readme_markdown,
        extensions=["fenced_code", "tables", "toc"],
        output_format="html5",
    )


class HomeReadmeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["readme_html"] = render_readme_as_html()
        return context
