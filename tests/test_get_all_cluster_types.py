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

import json

from .utils import (write_cluster_definition, write_hot_component)

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
        "order": 123,
        "logo_url": "/images/foo.svg",
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
        "components": [{"name": "test-hot"}],
        "parameter_groups": [],
        "order": 123,
        "logo_url": "/images/foo.svg",
    }
    hot = {
        "heat_template_version": "2021-04-16",
        "parameters": {},
        "resources": {
            "router": { "type": "OS::Neutron::Router" },
            "network": { "type": "OS::Neutron::Net" },
        }
    }
    write_cluster_definition(app, definition, "test")
    write_hot_component(app, hot, "test", "test-hot")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["id"] == "test"
    assert data[0]["title"] == "test-heat"
    assert data[0]["description"] == "test-description"
    assert data[0]["parameters"] == {}
    assert data[0]["parameter_groups"] == []


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
        "components": [{"name": "test-hot"}],
        "parameter_groups": [],
        "order": 123,
        "logo_url": "/images/foo.svg",
    }
    hot = {
        "heat_template_version": "2021-04-16",
        "parameters": {
            "foo": { "type": "string" },
            "bar": { "type": "string" },
        },
        "resources": {
            "router": { "type": "OS::Neutron::Router" },
            "network": { "type": "OS::Neutron::Net" },
        },
    }
    write_cluster_definition(app, definition, "test")
    write_hot_component(app, hot, "test", "test-hot")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    app.logger.info(f'data: {data}')
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
        "components": [{"name": "test-hot"}],
        "hardcoded_parameters": {
            "foo": "foo value"
        },
        "parameter_groups": [],
        "order": 123,
        "logo_url": "/images/foo.svg",
    }
    hot = {
        "heat_template_version": "2021-04-16",
        "parameters": {
            "foo": { "type": "string" },
            "bar": { "type": "string" },
        },
        "resources": {
            "router": { "type": "OS::Neutron::Router" },
            "network": { "type": "OS::Neutron::Net" },
        },
    }
    write_cluster_definition(app, definition, "test")
    write_hot_component(app, hot, "test", "test-hot")
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
        "components": "should be a list",
    }
    good_definition = {
        "title": "good-heat",
        "description": "fake",
        "kind": "heat",
        "components": [{"name": "test-hot"}],
        "parameter_groups": [],
        "order": 123,
        "logo_url": "/images/foo.svg",
    }
    hot = {
        "heat_template_version": "2021-04-16",
        "parameters": {},
        "resources": {
            "router": { "type": "OS::Neutron::Router" },
            "network": { "type": "OS::Neutron::Net" },
        },
    }
    write_cluster_definition(app, broken_definition, "broken")
    write_cluster_definition(app, good_definition, "good")
    write_hot_component(app, hot, "good", "test-hot")
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["id"] == "good"
