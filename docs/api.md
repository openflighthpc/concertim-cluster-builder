# Cluster types

## `GET /cluster-types/`  List available cluster types

Lists all enabled cluster types.

### Response Codes

* `200 - OK`  Request was successful.
* `500 - Internal Server Error`  An unexpected error occurred.  This should not
  happen.

### Response Parameters

* `id` : `string` : A unique identifier for this cluster type.
* `title` : `string` : Brief description of the purpose of the cluster.
* `description` : `string` : Fuller description of the purpose of the cluster and how to use it.
* `parameters` : `object` : Parameters for the cluster creation.  See https://docs.openstack.org/heat/latest/template_guide/hot_spec.html#parameters-section for details.

### Response Example

```
[
  {
    "description": "Create a high-availability database cluster using MySQL/MariaDB Galera,\nPostgreSQL with Patroni, or Cassandra.\n\nOnce the database cluster is ready...\n",
    "id": "database-cluster",
    "parameters": {
      "clustername": {
        "constraints": [
          {
            "description": "Cluster name must be between 6 and 255 characters",
            "length": {
              "max": 255,
              "min": 6
            }
          },
          {
            "allowed_pattern": "[a-zA-Z]+[a-zA-Z0-9\\-\\_]*",
            "description": "Cluster name can contain only alphanumeric characters, hyphens and underscores"
          }
        ],
        "default": "mycluster",
        "description": "The name your cluster should be given",
        "label": "Cluster name",
        "type": "string"
      },
      "count": {
        "constraints": [
          {
            "description": "Number of replicas cannot be less than one",
            "range": {
              "min": 1
            }
          }
        ],
        "default": 3,
        "description": "How many replicas should your cluster contain?",
        "label": "Number of database replicas",
        "type": "number"
      },
      "database-flavour": {
        "constraints": [
          {
            "allowed_values": [
              "MariaDB",
              "PostgreSQL",
              "Cassandra"
            ]
          }
        ],
        "default": "m1.small",
        "description": "Which database flavour do you want?",
        "label": "Database flavour",
        "type": "string"
      },
      "node-flavour": {
        "constraints": [
          {
            "allowed_values": [
              "m1.small",
              "m1.medium",
              "m1.large",
              "m1.xxlarge",
              "m1.xxxlarge"
            ]
          }
        ],
        "default": "m1.small",
        "description": "Which flavour should be be used for the database servers?",
        "label": "Node flavour",
        "type": "string"
      }
    },
    "title": "Database Clustering"
  }
]
```

# Clusters

## `POST /clusters/` Create a cluster

Creates a cluster.


### Response Codes

* `201 - Created`  Request was successful.
* `400 - Bad Request`  Some content in the request was invalid.
* `500 - Internal Server Error`  An unexpected error occurred.  This should not
  happen.


### Request Parameters

* `cloud_env` : `object` : Object defining how to connect to the cloud environment
* `cloud_env.auth_url` : `string` : URL for connecting to the cloud environment's identification service, e.g., openstack's keystone.
* `cloud_env.username` : `string` : Username to use for connecting to the cloud environment's identification service.
* `cloud_env.password` : `string` : Password to use for connecting to the cloud environment's identification service.
* `cloud_env.project_name` : `string` : Project name to use for connecting to the cloud environment's identification service.
* `cloud_env.user_domain_name` : `string` : User domain name to use for connecting to the cloud environment's identification service.
* `cloud_env.project_domain_name` : `string` : Project domain name to use for connecting to the cloud environment's identification service.
* `cluster` : `object` : Object defining configuration for the cluster.
* `cluster.name` : `string` : The name of the cluster.
* `cluster.cluster_type_id` : `string` : The identifier of the cluster type this cluster will be created from.
* `cluster.parameters` : `object` : Object defining the parameters passed to the cluster creation mechanism.  They keys should match the keys in the `parameters` section for the cluster type specified in `cluster.cluster_type_id`.


### Request Example

```
{
  "cloud_env": {
    "auth_url": "http://10.151.0.184:35357/v3",
    "username": "test-user",
    "password": "reelshanRojPak8",
    "project_name": "test-project",
    "user_domain_name": "default",
    "project_domain_name": "default"
  },
  "cluster": {
    "name": "my-cluster",
    "cluster_type_id": "database-cluster",
    "parameters": {
      "clustername": "my-cluster",
      "database-flavour": "PostgreSQL"
    }
  }
}
```


# Errors

The error format is based on the [JSON:API
error](https://jsonapi.org/format/#errors) format.

If a URL is not found:

```
{
  "errors": [
    {
      "title": "Not Found",
      "detail": "...",
      "status": "404"
    }
  ]
}
```

If the JSON body is not parsable a 400 error response is given with a body of:

```
{
  "errors": [
    {
      "detail": "<detail of parse error>",
      "status": "400",
      "title": "Bad Request"
    }
  ]
}
```

If the JSON body has the wrong structure a 400 error response is given.  For
example, if the cluster property is specified as an array instead of an object:

```
{
  "errors": [
    {
      "detail": "[] is not of type 'object'",
      "source": {
        "pointer": "/cluster"
      },
      "status": "400",
      "title": "JSON schema error"
    }
  ]
}
```

If the JSON body has the correct structure, but the values are not valid, a 400
error response is given with a body of:

```
{
  "errors": [
    {
      "status": "400",
      "title": "JSON schema erorr",
      "detail": "<details about this failure>",
      "source": {
        "pointer": "<field that the validation is for>"
      }
    }
  ],
}

```

For example if `cloud_env.username` was set to `null`:


```
{
  "errors": [
    {
      "detail": "None is not of type 'string'",
      "source": {
        "pointer": "/cloud_env/username"
      },
      "status": "400",
      "title": "JSON schema error"
    }
  ]
}
```

# Authentication

Any requests requiring authentication send the necessary credentials in the
body of the request as part of the `cloud_env` object.  See `POST /clusters/`
for more details.
