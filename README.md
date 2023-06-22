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
type definitions.  This is done by copying (or symlinking) files into
[instance/cluster-types-enabled/](instance/cluster-types-enabled/).

Currently, there is no documentation on the format for the cluster type
definition files beyond the [well-documented
examples](cluster-types-examples/).  They should prove sufficient.

In production, you may wish to use a docker volume to contain the cluster type
definitions.  If so, the volume should be mounted on the container at
`/app/instance/cluster-types-enabled/`.

## Installation

Concertim Cluster Builder is intended to be deployed as a Docker container.
There is a Dockerfile in this repo that the image can be built from.  The
cluster builder service is configured to run on port `42378` of the container.

An image can be built with the following command:

```
docker build --tag concertim-cluster-builder:latest .
```

## Usage

Once the docker image is built (see [Installation](#installation) above) a
container can be started from that image with the following command.  You may
wish to change the port and interface that the service is published on.

```
docker run --rm --name concertim-cluster-builder --publish 127.0.0.1:42378:42378 concertim-cluster-builder
```

The container will need to be able to receive HTTP requests from the
concertim-visualisation-app container and be able to make HTTP requests to the
openstack containers, specifically keystone and heat.  Configuring the
container networks to support that is left as an exercise for the reader.

## HTTP API

The HTTP API is documented in the [API documentation](/docs/api.md).


## Development

There is a [docker-compose](docker-compose.yml) file that creates a docker
container suitable for development. Note this docker-compose.yml file is not
intended for a production deployment.

The development docker container can be started with:

```
docker compose up
```

Any changes made to the local source code will be automatically picked up by
the service running inside the container.

[Example cluster type definitions](cluster-types-examples/) are available.
These can be installed by symlinking them into
`instance/cluster-types-enabled/`.

```
for i in cluster-types-examples/* ; do
  ln -s ../../${i} instance/cluster-types-enabled/
done
```
