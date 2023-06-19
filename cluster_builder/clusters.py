from flask import (Blueprint, abort, current_app, g, make_response)
from flask_expects_json import expects_json

from .openstack.auth import OpenStackAuth
from .openstack.heat_handler import HeatHandler

import keystoneauth1.exceptions.http as ks_exceptions

bp = Blueprint('clusters', __name__, url_prefix="/clusters")

create_schema = {
        "type": "object",
        "properties": {
            "cloud_env": {
                "type": "object",
                "properties": {
                    "auth_url": { "type": "string", "format": "uri" },
                    "username": { "type": "string" },
                    "password": { "type": "string" },
                    "project_name": { "type": "string" },
                    "project_domain_name": { "type": "string" },
                    "user_domain_name": { "type": "string" }
                    },
                "required": ["auth_url", "username", "password", "project_name", "project_domain_name", "user_domain_name"]
                },
            "cluster": {
                "type": "object",
                "properties": {
                    "name": { "type": "string" },
                    "type_id": { "type": "string" },
                    "parameters": { "type": "object" }
                    },
                "required": ["name", "type_id"]
                }
            },
        "required": ["cloud_env", "cluster"]
        }

@bp.post('/')
@expects_json(create_schema, check_formats=True)
def create_cluster():
    # * [X] Authenticate request
    # * [X] Connect to HEAT
    # * [ ] Create cluster via HEAT

    sess = OpenStackAuth(g.data["cloud_env"], current_app.logger).get_session()
    handler = HeatHandler(sess, current_app.logger)
    try:
        cluster = handler.create_cluster(g.data["cluster"])
        current_app.logger.debug(f"created cluster {cluster}")
    except Exception as e:
        raise e
    else:
        data =  { "id": cluster.id, "name": cluster.name }
        return make_response(data, 201)


@bp.get('/<uuid:cluster_id>')
def show_cluster(cluster_id):
    return {
            "id": cluster_id,
            "name": "test-cluster",
            "status": "pending"
            }
