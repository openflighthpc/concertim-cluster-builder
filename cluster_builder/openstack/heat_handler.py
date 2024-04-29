import os
import secrets
import tempfile
import time
import yaml

from heatclient.client import Client as HeatClient
from heatclient.common import template_utils
from .error_handling import ProjectLimitError

from ..models import utils as model_utils

class Cluster:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class HeatHandler:
    def __init__(self, sess, logger):
        self.logger = logger
        self.client = self.__get_client(sess)


    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = HeatClient(version='1', session=sess)
                self.logger.debug("Heat client connected")
                return client
            except Exception as e:
                self.logger.error(f"Failed to create Heat client: {e}. Retrying...")
                time.sleep(1)

        raise Exception("Failed to create Heat client after multiple attempts.")


    def create_cluster(self, cluster_data, cluster_type, project_limits, flavors):
        self.logger.info(f"Creating cluster {cluster_data['name']} from {cluster_data['cluster_type_id']}")
        self.logger.debug(f"type: {cluster_type}")
        # Allow errors to be propagated.  They will be caught and handled in
        # either `openstack.error_handling.py` or `__init__.py`.
        parameters = model_utils.merge_parameters(cluster_type, cluster_data.get("parameters"))
        parameters = model_utils.remove_unwanted_answers(cluster_type, cluster_data.get("selections"), parameters)
        stack_name = "{}--{}".format(cluster_data["name"], secrets.token_urlsafe(16))
        files, template = self._get_template_contents(cluster_type, cluster_data.get("selections"))
        counts = self.determine_quota_counts(parameters, template["resources"], cluster_data.get("selections"), flavors)
        self.logger.debug(f"gibbons {counts}")
        self.logger.debug(f"limits {project_limits}")
        self.check_limits(counts, project_limits)
        response = self.client.stacks.create(
                stack_name=stack_name,
                template=yaml.safe_dump(template, sort_keys=False),
                files=files,
                parameters=parameters
                )
        return Cluster(id=response["stack"]["id"], name=stack_name)


    def _build_template(self, cluster_type, selections):
        merged_parameters = {}
        merged_resources = {}
        merged_outputs = {}
        merged_conditions = {}
        heat_template_versions = []

        self.logger.info(f"Building HEAT template for {cluster_type.id}: optional selections={selections}")
        for component in cluster_type.components:
            is_selected = selections.get(component.name, False)
            if component.is_optional and not is_selected:
                self.logger.info(f"skipping deselected component {component.name}")
                continue
            self.logger.info(f"including {'selected optional' if component.is_optional else 'mandatory'} component {component.name}")
            heat_template_versions.append(component.heat_template_version)

            for id, parameter in component.parameters.items():
                if id not in merged_parameters:
                    merged_parameters[id] = parameter

            for resource in component.resources:
                if resource in merged_resources:
                    raise RuntimeError(f"no good! duplicate resource identifiers {resource}")
            merged_resources.update(component.resources)

            for output in component.outputs:
                if output in merged_outputs:
                    raise RuntimeError(f"no good! duplicate output identifiers {output}")
            merged_outputs.update(component.outputs)

            for condition in component.conditions:
                if condition in merged_conditions:
                    raise RuntimeError(f"no good! duplicate condition identifiers {condition}")
            merged_conditions.update(component.conditions)

        if len(list(set(heat_template_versions))) > 1:
            raise RuntimeError(f"no good! incompatible heat template versions {heat_template_versions}")

        template = {
            "heat_template_version": heat_template_versions[0],
            "parameters": merged_parameters,
            "resources": merged_resources,
            "conditions": merged_conditions,
            "outputs": merged_outputs,
        }

        return template


    def _get_template_contents(self, cluster_type, selections):
        template = self._build_template(cluster_type, selections)
        tmpdir = os.path.join(os.path.dirname(cluster_type.path), 'tmp')
        os.makedirs(tmpdir, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=tmpdir, mode="w", delete=False) as tf:
            yaml.safe_dump(template, tf.file)
            tf.close()
            files, hot_template = template_utils.get_template_contents(tf.name, fetch_child=True)
            os.unlink(tf.name)
            return files, hot_template

    def determine_quota_counts(self, parameters, resources, selections, flavors):
        instances = 0
        volumes = 0
        ram = 0
        vcpus = 0
        volume_disk = 0
        for resource in resources.values():
            if resource["type"] == "OS::Nova::Server":
                instances += 1
                flavor_name = self.resolve_parameter_value(parameters, resource, 'flavor')
                details = self.get_flavour_details(flavors, flavor_name)
                ram += details["ram"]
                vcpus += details["vcpus"]
                volume_disk += details["volume_disk"]
            elif resource["type"] == "OS::Cinder::Volume":
                volumes += 1
                volume_disk += self.resolve_parameter_value(parameters, resource, "size")
            elif resource["type"] == "OS::Heat::ResourceGroup":
                file_path = resource["properties"]["resource_def"]["type"].replace("file://", "")
                with open(file_path, "r") as f:
                    file_data = yaml.safe_load(f)
                group_counts = self.determine_quota_counts(parameters, file_data["resources"], selections, flavors)
                multiplier = self.resolve_parameter_value(parameters, resource, "count") or 1
                instances += group_counts["instances"] * multiplier
                volumes += group_counts["volumes"] * multiplier
                ram += group_counts["ram"] * multiplier
                vcpus += group_counts["vcpus"] * multiplier
                volume_disk += group_counts["volume_disk"] * multiplier
        return { "instances": instances, "volumes": volumes, "ram": ram, "vcpus": vcpus, "volume_disk": volume_disk }

    def get_flavour_details(self, flavors, flavor_name):
        flavor = next((flavor for flavor in flavors if flavor.name == flavor_name), None)
        return {
            "ram": flavor.ram,
            "vcpus": flavor.vcpus,
            "volume_disk": flavor.disk
        }

    # Try to make this neater/ less repetitive. Should probably list all errors, not just first reached.
    def check_limits(self, counts, project_limits):
        if project_limits["remaining_instances"] and counts["instances"] > project_limits["remaining_instances"]:
            if project_limits["remaining_instances"] < 0:
                raise ProjectLimitError(f"Project's maximum number of instances ({project_limits['maxTotalInstances']}) exceeded")

            raise ProjectLimitError(f"Cluster would exceed project's instance limit: requires {counts['instances']}, {project_limits['remaining_instances']} possible")

        if project_limits["remaining_volumes"] and counts["volumes"] > project_limits["remaining_volumes"]:
            if project_limits["remaining_volumes"] < 0:
                raise ProjectLimitError(f"Project's maximum number of volumes ({project_limits['maxTotalVolumes']}) exceeded")

            raise ProjectLimitError(f"Cluster would exceed project's volume limit: requires {counts['volumes']}, {project_limits['remaining_volumes']} possible")

        if project_limits["remaining_cores"] and counts["vcpus"] > project_limits["remaining_cores"]:
            if project_limits["remaining_vcpus"] < 0:
                raise ProjectLimitError(f"Project's maximum number of vcpus ({project_limits['maxTotalCores']}) exceeded")

            raise ProjectLimitError(f"Cluster would exceed project's vcpus limit: requires {counts['vcpus']}, {project_limits['remaining_vcpus']} possible")

        if project_limits["remaining_ram"] and counts["ram"] > project_limits["remaining_ram"]:
            if project_limits["remaining_ram"] < 0:
                raise ProjectLimitError(f"Project's maximum RAM ({project_limits['maxTotalRAM']})MB exceeded")

            raise ProjectLimitError(f"Cluster would exceed project's RAM limit: requires {counts['ram']}MB, {project_limits['remaining_ram']}MB possible")

        if project_limits["remaining_disk"] and counts["disk"] > project_limits["remaining_disk"]:
            if project_limits["remaining_disk"] < 0:
                raise ProjectLimitError(f"Project's maximum volume disk usage ({project_limits['maxTotalVolumeGigabytes']})GB exceeded")

            raise ProjectLimitError(f"Cluster would exceed project's volume disk limit: requires {counts['disk']}GB, {project_limits['remaining_disk']}MB possible")

    def resolve_parameter_value(self, parameters, resource, param_name):
        if param_name not in resource["properties"]: return None

        result = resource["properties"][param_name]
        if type(result) is dict:
            return parameters[result["get_param"]]
        else:
            return result
