from flask import Blueprint
from flask import make_response
from flask import request
from dateutil import parser

from .models import ClusterType

bp = Blueprint('cluster-types', __name__, url_prefix="/cluster-types")
ATTRIBUTES = ["id", "title", "description", "parameters", "last_modified"]

@bp.route('/')
def index():
    cluster_types = []
    last_modified = None
    for ct in ClusterType.all():
        if last_modified == None or ct.last_modified > last_modified: last_modified = ct.last_modified
        cluster_types.append(ct.asdict(ATTRIBUTES))
    if (request.if_modified_since and last_modified != None and
       int(request.if_modified_since.timestamp()) == int(last_modified.timestamp())):
       return '', 304

    r = make_response(cluster_types)
    r.last_modified = last_modified
    return r

@bp.route('/<string:id>')
def show_cluster_type(id):
    type = ClusterType.find(id)
    last_modified = type.last_modified
    if (request.if_modified_since and int(request.if_modified_since.timestamp()) == int(last_modified.timestamp())):
           return '', 304

    r = make_response(type.asdict(ATTRIBUTES))
    r.last_modified = type.last_modified
    return r
