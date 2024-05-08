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

from dataclasses import asdict, dataclass, field
import datetime


@dataclass(kw_only=True)
class Instruction:
    """
    Instruction contains the written instructions for launching, administering
    and using a cluster type.
    """
    id: str
    title: str
    text: str


@dataclass(kw_only=True)
class BaseClusterType:
    """
    BaseClusterType is a base class for the different cluster type kinds.

    Derived classes are expected to provide a parameters property in some
    manner, along with any additional properties they require themselves.
    """
    # Instance variables used by dataclass decorator.
    id: str
    path: str
    title: str
    description: str
    kind: str
    last_modified: str
    parameter_groups: list
    hardcoded_parameters: dict = field(default_factory=dict)
    order: int
    logo_url: str
    instructions: list[Instruction]


    def asdict(self, attributes=None):
        if attributes is None:
            return self._serializable_attributes()
        else:
            return {k: v for k, v in self._serializable_attributes().items() if k in attributes}


    def _serializable_attributes(self):
        """Return a dict of serializable attributes"""
        return asdict(self)


@dataclass(kw_only=True)
class SaharaClusterType(BaseClusterType):
    """
    SaharaClusterType represents a sahara based cluster type.  It uses sahara
    directly to launch the cluster.
    """
    parameters: dict
    upstream_template: str


@dataclass(kw_only=True)
class MagnumClusterType(BaseClusterType):
    """
    MagnumClusterType represents a magnum based cluster type.  It uses magnum
    directly to launch the cluster.
    """
    parameters: dict
    upstream_template: str


@dataclass(kw_only=True)
class Component:
    """
    Component represents a single components/*.yaml file for a heat based cluster type.
    """
    path: str
    heat_template_version: str
    parameters: dict = field(default_factory=dict)
    resources: dict = field(default_factory=dict)
    conditions: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    last_modified: datetime.datetime
    is_optional: bool
    name: str


@dataclass(kw_only=True)
class HeatClusterType(BaseClusterType):
    """
    HeatClusterType represents a heat based cluster type.
    """
    components: list[Component]


    @property
    def parameters(self):
        # Load parameters from all components giving precendence to parameters
        # defined in earlier components where there is an id clash.
        parameters = {}
        for component in self.components:
            for id, parameter in component.parameters.items():
                if id not in parameters:
                    parameters[id] = parameter

        if self.hardcoded_parameters is None:
            return parameters
        else:
            params = {}
            hardcoded_names = self.hardcoded_parameters.keys()
            for key, value in parameters.items():
                if key in hardcoded_names:
                    # Hardcoded params are not displayed to the user.  The
                    # hardcoded value will be provided to OpenStack exactly as
                    # provided in the cluster definition.
                    pass
                else:
                    params[key] = value
            return params


    def _serializable_attributes(self):
        """Return a dict of serializable attributes"""
        attrs = {"parameters": self.parameters}
        attrs.update(asdict(self))
        return attrs
