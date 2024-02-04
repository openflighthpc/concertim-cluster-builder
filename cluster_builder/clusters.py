from flask import (Blueprint, abort, current_app, g, request, make_response)
from flask_expects_json import expects_json

from .models import ClusterType
from .openstack.auth import OpenStackAuth
from .openstack.heat_handler import HeatHandler
from .openstack.magnum_handler import MagnumHandler
from .openstack.sahara_handler import SaharaHandler
from .middleware.middleware import MiddlewareService
from .middleware.utils.auth import authenticate_headers

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
            "middleware_url" : {"type" : "string"},
        "required": ["cloud_env", "cluster", "billing_account_id", "middleware_url"]
        }

handlers = {
        "heat": HeatHandler,
        "magnum": MagnumHandler,
        "sahara": SaharaHandler,
        }

@bp.post('/')
@expects_json(create_schema, check_formats=True)
def create_cluster():

    auth_status, message = authenticate_headers(request.headers, current_app.logger)
    if not auth_status:
        abort(401,description=message)
    
    cluster_type = ClusterType.find(g.data["cluster"]["cluster_type_id"])
    cluster_type.assert_parameters_present(g.data["cluster"]["parameters"])
    handler_class = handlers.get(cluster_type.kind)
    if handler_class is None:
        raise TypeError(f"Unknown cluster type kind '{cluster_type.kind}' for cluster type '{cluster_type.id}'")
    
    # Creating Middleware Service Object
    middlewareservice  = MiddlewareService(current_app.config, current_app.logger, g.data['middleware_url'])

    billing_account_credits = middlewareservice.get_credits({'billing_account_id' : g.data['billing_account_id']})
    current_app.logger.info(f" Billing account credits available : {billing_account_credits}")

    # Checking for enough credits
    if not  int(billing_account_credits['credits']) > 0:
        body = {
                "errors": [
                    {
                    "status": "400",
                    "title":  "Insufficient credits",
                    "detail": "Not enough credits to launch a cluster"
                    }
                ]
               }
        return make_response(body, 400)
    
    sess = OpenStackAuth(g.data["cloud_env"], current_app.logger).get_session()
    handler = handler_class(sess, current_app.logger)
    cluster = handler.create_cluster(g.data["cluster"], cluster_type)
    current_app.logger.debug(f"created cluster {cluster.id}:{cluster.name}")

    # Creating Billing Order/Subscription
    order = middlewareservice.create_order({'billing_account_id' : g.data['billing_account_id']})

    # Associating Openstack stack ID with Billing order/subscription
    middlewareservice.add_order_tag({'order_id' : order['order'], 'tag_name' : 'openstack_stack_id', 'tag_value' : cluster.id})
        
    body = {"id": cluster.id, "name": cluster.name}
    return make_response(body, 201)
