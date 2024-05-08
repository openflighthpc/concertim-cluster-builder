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

from cinderclient import client

VERSION = '3'

class CinderHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.cinder = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                nova = client.Client(VERSION, session=sess)
                self.logger.debug("Cinder client connected")
                return nova
            except Exception as e:
                self.logger.error(f"Failed to create Cinder client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Cinder client after multiple attempts.")


    # A limit of -1 represents no limit
    def get_limits(self):
        grouped_limits = {}
        limits = self.cinder.limits.get().to_dict()["absolute"]
        grouped_limits["volume_disk"] = {
            "total_allowed": limits["maxTotalVolumeGigabytes"], "used": limits["totalGigabytesUsed"], "units": "GB"
        }
        grouped_limits["volume_disk"]["remaining"] = None if limits["maxTotalVolumeGigabytes"] == -1 else limits["maxTotalVolumeGigabytes"] - limits["totalGigabytesUsed"]

        grouped_limits["volumes"] = {
            "total_allowed": limits["maxTotalVolumes"], "used": limits["totalVolumesUsed"], "units": ""
        }
        grouped_limits["volumes"]["remaining"] = None if limits["maxTotalVolumes"] == -1 else limits["maxTotalVolumes"] - limits["totalVolumesUsed"]

        return grouped_limits
