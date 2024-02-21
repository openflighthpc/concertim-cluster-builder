from dataclasses import asdict, dataclass, field
import datetime


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
