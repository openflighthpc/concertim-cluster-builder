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

import time

from magnumclient.client import Client

from ..models import utils as model_utils

class Cluster:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class MagnumHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.client = self.__get_client(sess)


    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = Client(version='1', session=sess)
                self.logger.debug("Magnum client connected")
                return client
            except Exception as e:
                self.logger.error(f"Failed to create Magnum client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Magnum client after multiple attempts.")

    # Project limit checks not implemented
    def create_cluster(self, cluster_data, cluster_type, project_limits, flavors):
        self.logger.info(f"Creating cluster {cluster_data['name']} from {cluster_data['cluster_type_id']}")
        # Allow errors to be propagated.  They will be caught and handled in
        # either `openstack.error_handling.py` or `__init__.py`.
        cluster_name = cluster_data["name"]
        self.logger.debug(f"getting cluster template {cluster_type.upstream_template}")
        magnum_cluster_template = self.client.cluster_templates.get(cluster_type.upstream_template)
        parameters = model_utils.merge_parameters(cluster_type, cluster_data.get("parameters"))
        self.logger.debug(f"parameters: {parameters}")
        magnum_cluster = self.client.clusters.create(
                name=cluster_name,
                cluster_template_id=magnum_cluster_template.uuid,
                **parameters
                )
        return Cluster(id=magnum_cluster.uuid, name=cluster_name)
    
