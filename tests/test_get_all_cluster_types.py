import json

from .utils import (write_cluster_definition, write_hot)

def test_cluster_types_when_empty(client):
    """
    When there are no cluster definitions we get an empty response.
    """
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 0


def test_valid_magnum_definition(client, app):
    definition = {
            "title": "test-title",
            "description": "test-description",
            "parameters": {},
            "kind": "magnum",
            "magnum_cluster_template": "test-template",
            }
    write_cluster_definition(app, definition, "test-id")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["id"] == "test-id"
    assert data[0]["title"] == "test-title"
    assert data[0]["description"] == "test-description"
    assert data[0]["parameters"] == {}


def test_valid_heat_definition(client, app):
    definition = {
            "title": "test-heat",
            "description": "test-description",
            "kind": "heat",
            "heat_template_url": "test-hot.yaml",
            }
    hot = {
            "heat_template_version": "2021-04-16",
            "resources": {
                "router": { "type": "OS::Neutron::Router" },
                "network": { "type": "OS::Neutron::Net" },
                }
            }
    write_cluster_definition(app, definition, "test")
    write_hot(app, hot, "test-hot.yaml")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["id"] == "test"
    assert data[0]["title"] == "test-heat"
    assert data[0]["description"] == "test-description"
    assert data[0]["parameters"] == {}


def test_cluster_types_with_invalid_template(client, app):
    # Invalid cluster types are not included in the output.
    write_cluster_definition(app, '{"title": "oops invalid json/YAML')
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 0


def test_heat_definitions_load_params_from_hot(client, app):
    definition = {
            "title": "test-heat",
            "description": "test-description",
            "kind": "heat",
            "heat_template_url": "test-hot.yaml",
            }
    hot = {
            "heat_template_version": "2021-04-16",
            "resources": {
                "router": { "type": "OS::Neutron::Router" },
                "network": { "type": "OS::Neutron::Net" },
                },
            "parameters": {
                "foo": { "type": "string" },
                "bar": { "type": "string" },
                }
            }
    write_cluster_definition(app, definition, "test")
    write_hot(app, hot, "test-hot.yaml")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["parameters"] == {
            "foo": { "type": "string" },
            "bar": { "type": "string" },
            }


def test_hardcoded_params_are_not_included_in_output(client, app):
    definition = {
            "title": "test-heat",
            "description": "test-description",
            "kind": "heat",
            "heat_template_url": "test-hot.yaml",
            "hardcoded_parameters": {
                "foo": "foo value"
                }
            }
    hot = {
            "heat_template_version": "2021-04-16",
            "resources": {
                "router": { "type": "OS::Neutron::Router" },
                "network": { "type": "OS::Neutron::Net" },
                },
            "parameters": {
                "foo": { "type": "string" },
                "bar": { "type": "string" },
                }
            }
    write_cluster_definition(app, definition, "test")
    write_hot(app, hot, "test-hot.yaml")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["parameters"] == {
            "bar": { "type": "string" },
            }


def test_invalid_definitions_are_ignored(client, app):
    """
    Invalid definitions are ignored; they don't result in a 500 error.
    """
    broken_definition = {
            "title": "broken-heat",
            "description": "fake",
            "kind": "heat",
            "heat_template_url": "does-not-exist.yaml",
            }
    good_definition = {
            "title": "good-heat",
            "description": "fake",
            "kind": "heat",
            "heat_template_url": "test-hot.yaml",
            }
    hot = {
            "heat_template_version": "2021-04-16",
            "resources": {
                "router": { "type": "OS::Neutron::Router" },
                "network": { "type": "OS::Neutron::Net" },
                },
            }
    write_cluster_definition(app, broken_definition, "broken")
    write_cluster_definition(app, good_definition, "good")
    write_hot(app, hot, "test-hot.yaml")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["id"] == "good"
