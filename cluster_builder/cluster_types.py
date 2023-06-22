from flask import (Blueprint)

from .models import ClusterType

bp = Blueprint('cluster-types', __name__, url_prefix="/cluster-types")

@bp.route('/')
def index():
    return ClusterType.all()
