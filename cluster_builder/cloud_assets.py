from flask import (Blueprint, abort, current_app, g, request, make_response)
from flask_expects_json import expects_json

from .openstack.auth import OpenStackAuth
from .openstack.nova_handler import NovaHandler
from .openstack.glance_handler import GlanceHandler
from .openstack.neutron_handler import NeutronHandler

bp = Blueprint('cloud_assets', __name__, url_prefix="/cloud_assets")

auth_schema = {
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
    },
    "required": ["cloud_env"],
}

@bp.post('/')
@expects_json(auth_schema, check_formats=True)
def cloud_assets():
    sess = OpenStackAuth(g.data["cloud_env"], current_app.logger).get_session()
    nova = NovaHandler(sess, current_app.logger)
    glance = GlanceHandler(sess, current_app.logger)
    neutron = NeutronHandler(sess, current_app.logger)
    cloud_assets = {"flavors": [], "images": [], "networks": [], "keypairs": []}
    for flavor in nova.list_flavors():
        cloud_assets["flavors"].append({"id": flavor.id, "name": flavor.name})
    for keypair in nova.list_keypairs():
        cloud_assets["keypairs"].append({"id": keypair.id, "name": keypair.name})
    for image in glance.list_images():
        cloud_assets["images"].append({"id": image.id, "name": image.name})
    for network in neutron.list_networks():
        cloud_assets["networks"].append({"id": network.id, "name": network.name, "external": network.external})
    r = make_response(cloud_assets)
    return r
