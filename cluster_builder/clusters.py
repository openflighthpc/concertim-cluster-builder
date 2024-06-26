"""
==============================================================================
 Copyright (C) 2024-present Alces Flight Ltd.

 This file is part of Concertim Cluster Builder.

 This program and the accompanying materials are made available under
 the terms of the Eclipse Public License 2.0 which is available at
 <https://www.eclipse.org/legal/epl-2.0>, or alternative license
 terms made available by Alces Flight Ltd - please direct inquiries
 about licensing to licensing@alces-flight.com.

 Concertim Visualisation App is distributed in the hope that it will be useful, but
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
 IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
 OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
 PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
 details.

 You should have received a copy of the Eclipse Public License 2.0
 along with Concertim Visualisation App. If not, see:

  https://opensource.org/licenses/EPL-2.0

 For more information on Concertim Cluster Builder, please visit:
 https://github.com/openflighthpc/concertim-cluster-builder
==============================================================================
"""

from flask import (Blueprint, current_app, g, request, make_response)
from flask_expects_json import expects_json

from .models import (ClusterTypeRepo, utils as model_utils)
from .openstack.auth import OpenStackAuth
from .openstack.heat_handler import HeatHandler
from .openstack.magnum_handler import MagnumHandler
from .openstack.sahara_handler import SaharaHandler
from .openstack.nova_handler import NovaHandler
from .openstack.cinder_handler import CinderHandler
from .middleware.middleware import MiddlewareService
from .middleware.utils.auth import assert_authenticated

from .middleware.utils.exceptions import MiddlewareInsufficientCredits

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
                    "parameters": { "type": "object" },
                    "selections": { "type": "object" }
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

    # Authenticating JWT headers
    assert_authenticated(current_app.config, request.headers, current_app.logger)

    # Creating Cluster handler
    cluster_type = ClusterTypeRepo.find(g.data["cluster"]["cluster_type_id"])
    model_utils.assert_parameters_present(cluster_type, g.data["cluster"]["parameters"])
    handler_class = handlers.get(cluster_type.kind)
    if handler_class is None:
        raise TypeError(f"Unknown cluster type kind '{cluster_type.kind}' for cluster type '{cluster_type.id}'")
    

    # Creating Middleware Service Object
    middlewareservice  = MiddlewareService(current_app.config, current_app.logger, g.data['middleware_url'])


    # Obtaining Billing account credits
    billing_account_credits = middlewareservice.get_credits({'billing_account_id' : g.data['billing_account_id']})
    current_app.logger.info(f"Billing account credits available : {billing_account_credits}")

    # Checking for enough credits
    if not int(billing_account_credits) > 0:
       raise MiddlewareInsufficientCredits("Insufficient credits to launch a cluster")

    # Creating Billing Order/Subscription
    order_id = middlewareservice.create_order({'billing_account_id' : g.data['billing_account_id']})

    # Creating Openstack Cluster
    sess = OpenStackAuth(g.data["cloud_env"], current_app.logger).get_session()
    handler = handler_class(sess, current_app.logger)

    # Get flavours and limits for usage checks
    nova = NovaHandler(sess, current_app.logger)
    flavors = nova.list_flavors()
    project_limits = get_project_limits(sess, current_app.logger)
    current_app.logger.info(f"Project limits : {project_limits}")

    try:
        cluster = handler.create_cluster(g.data["cluster"], cluster_type, project_limits, flavors)
    except Exception as e:
        # Deleting Billing order if cluster creation fails
        current_app.logger.error(f"Cluster creation failed : {e}")
        middlewareservice.delete_order({'order_id' : order_id})
        # Re-raise error so that it is processed by the error handling defined
        # in the .openstack.error_handling module.
        raise e

    current_app.logger.debug(f"created cluster {cluster.id}:{cluster.name}")

    # Associating Openstack stack ID with Billing order/subscription
    middlewareservice.add_order_tag({'order_id' : order_id, 'tag_name' : 'openstack_stack_id', 'tag_value' : cluster.id})
    middlewareservice.add_order_tag({'order_id' : order_id, 'tag_name' : 'openstack_stack_name', 'tag_value' : cluster.name})

    body = {"id": cluster.id, "name": cluster.name}
    return make_response(body, 201)

# Project id is determined by session (i.e. whichever project id is used for auth)
def get_project_limits(session, logger):
    nova = NovaHandler(session, logger)
    cinder = CinderHandler(session, logger)
    limits = nova.get_limits()
    volume_limits = cinder.get_limits()
    limits.update(volume_limits)
    return limits
