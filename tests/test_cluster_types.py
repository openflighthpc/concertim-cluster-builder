import json
import os

def test_cluster_types_when_empty(client):
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 0


def test_cluster_types_when_non_empty(client, app):
    cluster_type = {
            "title": "test-title",
            "description": "test-description",
            "parameters": []
            }
    write_cluster_types(app, cluster_type)
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]["title"] == "test-title"
    assert data[0]["description"] == "test-description"
    assert data[0]["parameters"] == []


def test_cluster_types_with_invalid_template(client, app):
    write_cluster_types(app, '{"title": "oops invalid json/YAML')
    response = client.get("/cluster-types/")
    data = json.loads(response.data)
    assert len(data) == 0


def write_cluster_types(app, cluster_type):
    enabled_dir = os.path.join(app.instance_path, "cluster-types-enabled")
    with open(os.path.join(enabled_dir, "test.yaml"), "w") as test_file:
        if isinstance(cluster_type, dict):
            test_file.write(json.dumps(cluster_type))
        elif isinstance(cluster_type, str):
            test_file.write(cluster_type)
        else:
            raise TypeError(f"expected cluster_type to be dict or str, got {type(cluster_type)}")
