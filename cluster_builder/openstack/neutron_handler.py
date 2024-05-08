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

from dataclasses import dataclass
import time

from neutronclient.v2_0 import client

@dataclass
class Network:
    id: str
    name: str
    external: bool

class NeutronHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.neutron = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                neutron = client.Client(session=sess)
                self.logger.debug("Neutron client connected")
                return neutron
            except Exception as e:
                self.logger.error(f"Failed to create Neutron client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Neutron client after multiple attempts.")


    def list_networks(self):
        networks = []
        for network in self.neutron.list_networks()["networks"]:
            kwargs = {"id": network["id"], "name": network["name"], "external": network["router:external"]}
            networks.append(Network(**kwargs))
        return networks
