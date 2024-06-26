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
import pytest
import jwt
import time

from .utils import (remove_path, set_path, write_cluster_definition)

JWT_SECRET = "TEST_SECRET"

def test_launch_cluster_without_authorization(client):
    body = {
        "cloud_env": {
            "auth_url": "fake",
            "user_id": "fake",
            "password": "fake",
            "project_id": "fake"
        },
        "cluster": {
            "name": "test-cluster",
            "cluster_type_id": "does-not-exist",
            "parameters": {}
        },
        "billing_account_id" : "fake",
        "middleware_url" : "fake"
    }

    response = client.post("/clusters/", json=body)
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "errors" in data.keys()
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["title"] == "MiddlewareAuthenticationError"
    assert error["status"] == "401"


def test_launch_non_existent_cluster(client):
    body = {
        "cloud_env": {
            "auth_url": "fake",
            "user_id": "fake",
            "password": "fake",
            "project_id": "fake"
        },
        "cluster": {
            "name": "test-cluster",
            "cluster_type_id": "does-not-exist",
            "parameters": {}
        },
        "billing_account_id" : "fake",
        "middleware_url" : "fake"
    }
    
    bearer_token = "Bearer " + jwt.encode({"exp" : time.time() + 60}, JWT_SECRET, algorithm="HS256")
    headers = {"Authorization" : bearer_token}
    response = client.post("/clusters/", json=body, headers=headers)
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "errors" in data.keys()
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["title"] == "Not Found"
    assert error["status"] == "404"


def test_launch_with_missing_params(client, app):
    definition = {
        "title": "test-title",
        "description": "test-description",
        "parameters": {
            "master_count": {"type": "number"}
        },
        "kind": "magnum",
        "magnum_cluster_template": "test-template",
        "components": [{"name": "test-hot"}],
        "order": 123,
        "logo_url": "/images/foo.svg",
    }
    write_cluster_definition(app, definition, "test-id")
    body = {
        "cloud_env": {
            "auth_url": "fake",
            "user_id": "fake",
            "password": "fake",
            "project_id": "fake"
        },
        "cluster": {
            "name": "test-cluster",
            "cluster_type_id": "test-id",
            "parameters": {}
        },
        "billing_account_id" : "fake",
        "middleware_url" : "fake"
    }
    bearer_token = "Bearer " + jwt.encode({"exp" : time.time() + 60}, JWT_SECRET, algorithm="HS256")
    headers = {"Authorization" : bearer_token}
    response = client.post("/clusters/", json=body, headers=headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "errors" in data.keys()
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["title"] == "Bad Request"
    assert error["status"] == "400"
    assert "Missing param" in error["detail"]
    assert "master_count" in error["detail"]


@pytest.mark.parametrize("pointer,detail,body_mutator", [
    ("/",                   "'cloud_env' is a required property", remove_path(["cloud_env"])),
    ("/cluster",            "'name' is a required property",      remove_path(["cluster", "name"])),
    ("/cluster/name",       "not of type 'string'",               set_path(["cluster", "name"], 42)),
    # ("/cloud_env/auth_url", "not of type 'string'",               set_path(["cloud_env", "auth_url"], [])),
    ("/cloud_env",          "'password' is a required property",  remove_path(["cloud_env", "password"])),
    ])
def test_invalid_body(client, app, pointer, detail, body_mutator):
    body = {
        "cloud_env": {
            "auth_url": "fake",
            "user_id": "fake",
            "password": "fake",
            "project_id": "fake"
        },
        "cluster": {
            "name": "fake",
            "cluster_type_id": "test-id",
            "parameters": {}
        },
        "billing_account_id" : "fake",
        "middleware_url" : "fake"
    }
    body_mutator(body)
    response = client.post("/clusters/", json=body)
    assert response.status_code == 400
    data = json.loads(response.data)
    print(data)
    assert "errors" in data.keys()
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["title"] == "JSON schema error"
    assert error["status"] == "400"
    assert "source" in error
    assert "pointer" in error["source"]
    assert error["source"]["pointer"] == pointer
    assert detail in error["detail"]
