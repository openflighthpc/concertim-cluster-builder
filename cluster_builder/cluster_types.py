from flask import Blueprint
from flask import make_response
from flask import request
from dateutil import parser

from .models import ClusterType

bp = Blueprint('cluster-types', __name__, url_prefix="/cluster-types")

@bp.route('/')
def index():
    attributes = ["id", "title", "description", "parameters", "last_modified"]
    cluster_types = []
    last_modified = ""
    for ct in ClusterType.all():
        if last_modified == "" or ct.last_modified > last_modified: last_modified = ct.last_modified
        cluster_types.append(ct.asdict(attributes))
    if (request.if_modified_since and last_modified != "" and
       int(request.if_modified_since.timestamp()) == int(last_modified.timestamp())):
       return '', 304

    r = make_response(cluster_types)
    r.last_modified = last_modified
    return r
