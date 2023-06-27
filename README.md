# Concertim Cluster Builder

The Concertim Cluster Builder is a Python daemon process providing an HTTP API
to receive requests to build clusters of pre-defined types.

It is expected that such requests will be made by the [Concertim Visualisation
App](https://github.com/alces-flight/concertim-ct-visualisation-app) and that
the [Concertim OpenStack
Service](https://github.com/alces-flight/concertim-openstack-service) will
report the existence of those clusters to Concertim Visualisation App as and
when they become available.

## Configuration

All required configuration to access the cloud environment is sent in the
request to build a cluster.  More details can be found in the [API
documentation](/docs/api.md).

### Cluster type definitions

Concertim cluster builder needs to be configured with the available cluster
type definitions.  This is done by copying (or symlinking) files into the
docker container's `/app/instance/cluster-types-enabled/` directory.

Currently, all cluster types are backed by OpenStack HEAT and need to specify a
path to a HOT template.  The path should be relative to the docker container's
`/app/instance/hot/` directory.

In production, you should configure the `instance` directory prior to building
the image.  To use the example cluster types, run the following:

```
mkdir -p instance/cluster-types-enabled
mkdir -p instance/hot

for i in examples/cluster-types/* ; do
  ln -s ../../${i} instance/cluster-types-enabled/
done

for i in examples/hot/* ; do
  ln -s ../../${i} instance/hot/
done
```

Currently, each time the cluster types definitions are changed, the image will
need to be rebuilt.

Currently, there is no documentation on the format for the cluster type
definition files beyond the [well-documented
examples](cluster-types-examples/).  They should prove sufficient.


## Installation

Concertim Cluster Builder is intended to be deployed as a Docker container.
There is a Dockerfile in this repo that the image can be built from.  The
cluster builder service is configured to run on port `42378` of the container.

An image can be built with the following command:

```
docker build --tag concertim-cluster-builder:latest .
```

## Usage

Once the docker image is configured with cluster type definitions and has been
built (see [Cluster type definitions](#cluster-type-definitions) and
[Installation](#installation) above) a container can be started from that image
with the following command.

```
docker compose -f docker-compose-prod.yml up
```

The container will need to be able to receive HTTP requests from the
concertim-visualisation-app container and be able to make HTTP requests to the
openstack containers, specifically keystone and heat.  You may wish to edit the
docker compose file to achieve that.

## HTTP API

The HTTP API is documented in the [API documentation](/docs/api.md).


## Development

There is a [docker-compose-dev.yml](docker-compose.yml) file that creates a docker
container suitable for development. The contents of this repository are shared
with the docker container using docker volumes, meaning that any changes made
to the local source code will be automatically picked up by the service running
inside the container.

Note: this docker-compose-dev.yml file is not intended for a production deployment.

To setup for development you will need to:

1. Create a docker-compose.override.yml file.
2. Start the docker container.
3. Copy across the example cluter type definitions and their HOT templates.

These are explained in more detail below.

Copy the example [docker-compose-override](docker-compose.override.yml.example)
to `docker-compose.override.yml` and edit to set your local user's (that is the
user on your laptop) UID and GID. Doing this will prevent issues with file
permissions for the shared files.

```
cp docker-compose.override.yml.example docker-compose.override.yml
$EDITOR docker-compose.override.yml
```

Start the docker container by running the following.  This will cause certain
"per-instance" directories to be created.

```
docker compose -f docker-compose-dev.yml up
```

Finally, copy across the example cluster type definitions.  See [installing
example cluster types](#installing-example-cluster-types) below.


### Installing example cluster types

When the service first starts it will create the expected directory hierarchy
in its instance directory.  Once it has done so, you can copy across the
example cluster type definitions and their HOT templates.

```
for i in examples/cluster-types/* ; do
  ln -s ../../${i} instance/cluster-types-enabled/
done

for i in examples/hot/* ; do
  ln -s ../../${i} instance/hot/
done
```

