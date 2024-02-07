from flask import (Blueprint, current_app, request, make_response)

from .openstack.auth import OpenStackAuth
from .openstack.nova_handler import NovaHandler
from .openstack.glance_handler import GlanceHandler
from .openstack.neutron_handler import NeutronHandler

bp = Blueprint('cloud_assets', __name__, url_prefix="/cloud_assets")

@bp.get('/')
def cloud_assets():
    sess = OpenStackAuth(request.args, current_app.logger).get_session()
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
