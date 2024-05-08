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

# Openstack Packages
from keystoneauth1.identity import v2, v3
from keystoneauth1 import session

class OpenStackAuth:
    def __init__(self, auth_dict, logger):
        self.auth_dict = auth_dict
        self.auth_methods = {
            v3.Password: [
                {'auth_url', 'user_id', 'password', 'project_id'},
                {'auth_url', 'username', 'password', 'project_id', 'user_domain_name'},
                {'auth_url', 'username', 'password', 'project_name', 'project_domain_id', 'user_domain_id'},
                {'auth_url', 'username', 'password', 'project_name', 'project_domain_name', 'user_domain_name'}
            ],
            v2.Password: [
                {'auth_url', 'username', 'password', 'tenant_id'},
                {'auth_url', 'username', 'password', 'tenant_name'}
            ]
        }
        self.logger = logger

    def get_session(self):
        for method, required_params_list in self.auth_methods.items():
            for required_params in required_params_list:
                if required_params.issubset(self.auth_dict.keys()):
                    self.__log()
                    return session.Session(auth=method(**self.auth_dict), timeout=30)
        raise ValueError(f"Invalid auth_dict provided. It must contain one of the valid sets of parameters: {self.auth_methods}")

    def __log(self):
        sanitized = {k: self.auth_dict[k] for k in self.auth_dict.keys() if not k == "password"}
        self.logger.debug(f'getting openstack session {sanitized}')

