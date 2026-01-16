from flask import Blueprint

blog_bp = Blueprint(
    "blog",
    __name__,
    template_folder="templates/blog",
    url_prefix="/blog",
)

# Import routes to register views
from . import routes  # noqa: F401
