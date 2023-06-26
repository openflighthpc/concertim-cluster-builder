from flask import Blueprint

from .models import ClusterType

bp = Blueprint('cluster-types', __name__, url_prefix="/cluster-types")

@bp.route('/')
def index():
    attributes = ["id", "title", "description", "parameters"]
    cluster_types = []
    for ct in ClusterType.all():
        cluster_types.append(ct.asdict(attributes))
    return cluster_types
