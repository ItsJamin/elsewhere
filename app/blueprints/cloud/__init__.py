from flask import Blueprint

cloud_bp = Blueprint("cloud", __name__, url_prefix="/cloud", template_folder="templates")

from . import routes  # noqa
