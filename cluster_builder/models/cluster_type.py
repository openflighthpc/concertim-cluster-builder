from dataclasses import asdict, dataclass, field
import datetime


@dataclass(kw_only=True)
class BaseClusterType:
    """
    BaseClusterType is a base class for the different cluster type kinds.

    Derived classes are expected to provide a parameters and parameter_groups
    properties in some manner, along with any additional properties they
    require themselves.
    """
    # Instance variables used by dataclass decorator.
    id: str
    path: str
    title: str
    description: str
    kind: str
    last_modified: str
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
    parameter_groups: list
    upstream_template: str


@dataclass(kw_only=True)
class MagnumClusterType(BaseClusterType):
    """
    MagnumClusterType represents a magnum based cluster type.  It uses magnum
    directly to launch the cluster.
    """
    parameters: dict
    parameter_groups: list
    upstream_template: str


@dataclass()
class ParametersFile:
    """
    ParametersFile represents the parameters.yaml file for a heat based cluster type.
    """
    path: str
    parameters: dict
    parameter_groups: list
    last_modified: datetime.datetime


@dataclass(kw_only=True)
class Component:
    """
    Component represents a single components/*.yaml file for a heat based cluster type.
    """
    path: str
    heat_template_version: str
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
    parameters_file: ParametersFile
    components: list[Component]


    @property
    def parameters(self):
        if self.hardcoded_parameters is None:
            return self.parameters_file.parameters
        else:
            params = {}
            hardcoded_names = self.hardcoded_parameters.keys()
            for key, value in self.parameters_file.parameters.items():
                if key in hardcoded_names:
                    # Hardcoded params are not displayed to the user.  The
                    # hardcoded value will be provided to OpenStack exactly as
                    # provided in the cluster definition.
                    pass
                else:
                    params[key] = value
            return params


    @property
    def parameter_groups(self):
        return self.parameters_file.parameter_groups


    def _serializable_attributes(self):
        """Return a dict of serializable attributes"""
        attrs = {"parameters": self.parameters, "parameter_groups": self.parameter_groups}
        attrs.update(asdict(self))
        return attrs
