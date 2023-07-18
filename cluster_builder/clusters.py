from flask import (Blueprint, abort, current_app, g, make_response)
from flask_expects_json import expects_json

from .models import ClusterType
from .openstack.auth import OpenStackAuth
from .openstack.heat_handler import HeatHandler
from .openstack.magnum_handler import MagnumHandler

bp = Blueprint('clusters', __name__, url_prefix="/clusters")

# XXX Consider if we want to support using both project_name and project_id here.
create_schema = {
        "$defs": {
            "project_id": {
                "$id": "/schemas/project_id",

                "type": "object",
                "properties": {
                    "auth_url": { "type": "string", "format": "uri" },
                    "username": { "type": "string" },
                    "password": { "type": "string" },
                    "project_id": { "type": "string" },
                    "user_domain_name": { "type": "string" }
                    },
                "required": ["auth_url", "username", "password", "project_id", "user_domain_name"]

                },

            "project_name": {
                "$id": "/schemas/project_name",

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
                }
            },

        "type": "object",
        "properties": {
            "cloud_env": {
                "type": "object",
                "oneOf": [{"$ref": "/schemas/project_id"}, {"$ref": "/schemas/project_name"}]
                },
            "cluster": {
                "type": "object",
                "properties": {
                    "name": { "type": "string" },
                    "cluster_type_id": { "type": "string" },
                    "parameters": { "type": "object" }
                    },
                "required": ["name", "cluster_type_id"]
                }
            },
        "required": ["cloud_env", "cluster"]
        }

handlers = {
        "heat": HeatHandler,
        "magnum": MagnumHandler,
        }

@bp.post('/')
@expects_json(create_schema, check_formats=True)
def create_cluster():
    cluster_type = ClusterType.find(g.data["cluster"]["cluster_type_id"])
    cluster_type.assert_parameters_present(g.data["cluster"]["parameters"])
    handler_class = handlers.get(cluster_type.kind)
    if handler_class is None:
        raise TypeError(f"Unknown cluster type kind '{cluster_type.kind}' for cluster type '{cluster_type.id}'")
    sess = OpenStackAuth(g.data["cloud_env"], current_app.logger).get_session()
    handler = handler_class(sess, current_app.logger)
    cluster = handler.create_cluster(g.data["cluster"], cluster_type)
    current_app.logger.debug(f"created cluster {cluster.id}:{cluster.name}")
    body = {"id": cluster.id, "name": cluster.name}
    return make_response(body, 201)
