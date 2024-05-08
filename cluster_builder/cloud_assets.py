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

from flask import (Blueprint, current_app, request, make_response)

from .openstack.auth import OpenStackAuth
from .openstack.glance_handler import GlanceHandler
from .openstack.neutron_handler import NeutronHandler
from .openstack.nova_handler import NovaHandler
from .openstack.sahara_handler import SaharaHandler

bp = Blueprint('cloud_assets', __name__, url_prefix="/cloud_assets")

@bp.get('/')
def cloud_assets():
    sess = OpenStackAuth(request.args, current_app.logger).get_session()
    nova = NovaHandler(sess, current_app.logger)
    glance = GlanceHandler(sess, current_app.logger)
    neutron = NeutronHandler(sess, current_app.logger)
    sahara = SaharaHandler(sess, current_app.logger)
    cloud_assets = {
        "flavors": [],
        "images": [],
        "networks": [],
        "keypairs": [],
        "sahara.plugins": [],
        "sahara.images": [],
        "sahara.cluster_templates": [],
    }

    # For the following, we intentionally use name as the id.  This allows us to
    # have easy defaults specified in the cluster type definitions.
    for flavor in nova.list_flavors():
        cloud_assets["flavors"].append({"id": flavor.name, "name": flavor.name})
    for keypair in nova.list_keypairs():
        cloud_assets["keypairs"].append({"id": keypair.name, "name": keypair.name})
    for image in glance.list_images():
        cloud_assets["images"].append({"id": image.name, "name": image.name})
    for network in neutron.list_networks():
        cloud_assets["networks"].append({"id": network.name, "name": network.name, "external": network.external})

    # For the following, we intentionally use id as the id.  This allows our
    # sahara examples to work but does not support easy specification of
    # defaults.  We could fix that with more effort put into the sahara handler
    # and/or the sahara example cluster types.
    for plugin in sahara.list_plugins():
        cloud_assets["sahara.plugins"].append({"id": plugin.id, "name": plugin.name})
    for image in sahara.list_images():
        cloud_assets["sahara.images"].append({"id": image.id, "name": image.name})
    for template in sahara.list_cluster_templates():
        cloud_assets["sahara.cluster_templates"].append({"id": template.id, "name": template.name})

    r = make_response(cloud_assets)
    return r
