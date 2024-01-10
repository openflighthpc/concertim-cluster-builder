from flask import (Blueprint, abort, current_app, g, make_response)
from flask_expects_json import expects_json

from .models import ClusterType
from .openstack.auth import OpenStackAuth
from .openstack.heat_handler import HeatHandler
from .openstack.magnum_handler import MagnumHandler
from .openstack.sahara_handler import SaharaHandler
from .middleware.middleware import MiddlewareService

bp = Blueprint('clusters', __name__, url_prefix="/clusters")

# XXX Consider if we want to support all of these different ways of specifying a user/project.
create_schema = {
        "$defs": {
            "user_id_and_project_id": {
                "$id": "/schemas/user_id_and_project_id",

                "type": "object",
                "properties": {
                    "auth_url": { "type": "string", "format": "uri" },
                    "user_id": { "type": "string" },
                    "password": { "type": "string" },
                    "project_id": { "type": "string" },
                    },
                "required": ["auth_url", "user_id", "password", "project_id"]
                },

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
                "oneOf": [{"$ref": "/schemas/user_id_and_project_id"}, {"$ref": "/schemas/project_id"}, {"$ref": "/schemas/project_name"}]
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
            "billing_account_id" : {"type": "string"},
        "required": ["cloud_env", "cluster", "billing_account_id"]
        }

handlers = {
        "heat": HeatHandler,
        "magnum": MagnumHandler,
        "sahara": SaharaHandler,
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

    middlewareservice  = MiddlewareService()

    billing_account_credits = middlewareservice.get_credits(g.data['billing_account_id'])

    if billing_account_credits > 0:

        cluster = handler.create_cluster(g.data["cluster"], cluster_type)
        current_app.logger.debug(f"created cluster {cluster.id}:{cluster.name}")
        body = {"id": cluster.id, "name": cluster.name}
        return make_response(body, 201)
    
    else:
        body = {"message" : "Not enough credits to launch a cluster"}
        return make_response(body, 500)
