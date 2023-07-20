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

Concertim Cluster Builder has two separate elements to its configuration: 1)
configuring access to the cloud environment; and 2) configuring the enabled
cluster type definitions.  These are detailed below.

### Cloud environment access

All required configuration to access the cloud environment is sent in the
request to build a cluster.  More details on the format can be found in the
[API documentation](/docs/api.md).

### Exposing the service on the desired network

By default, Concertim cluster builder is configured to expose its service on
all of the host machine's IP addresses.  If this is not suitable for you, it
can be configured by editing the `docker-compose-prod.yml` file and changing
the `ports` entry.

### Cluster type definitions

Concertim cluster builder needs to be configured with the enabled cluster type
definitions. The enabled definitions are to be created in the docker
container's `/app/instance/cluster-types-enabled/` directory.

Currently, all cluster types are backed by OpenStack HEAT and need to specify a
path to a HOT template.  The path should be relative to the docker container's
`/app/instance/hot/` directory.

The Docker image is built with an example cluster type definition (and its HOT
template) enabled by default.

If you wish to configure additional cluster type definitions, the docker
container should be started with a host directory, say,
`/usr/share/concertim-cluster-builder/` mounted to `/app/instance/`. The
example cluster type definitions can then be copied to
`/usr/share/concertim-cluster-builder/` and new definitions added. To do this
follow the steps below:

Create the directory structure.

```bash
mkdir -p /usr/share/concertim-cluster-builder/{cluster-types-available,cluster-types-enabled,hot}
```

Copy across the example definition and its HOT template.

```bash
for i in examples/cluster-types/* ; do
  cp -a $i /usr/share/concertim-cluster-builder/cluster-types-available/
done
for i in examples/hot/* ; do
  cp -a $i /usr/share/concertim-cluster-builder/hot/
done
```

Optionally, enable the example definition

```bash
cd /usr/share/concertim-cluster-builder/cluster-types-enabled/
for i in ../cluster-types-available/* ; do
  ln -s ${i} .
done
```

Copy the example
[docker-compose.override.yml.prod.example](docker-compose.override.yml.prod.example)
to `docker-compose.override.yml` to enable the mount
`/usr/share/concertim-cluster-builder/`.

```bash
cp docker-compose.override.yml.prod.example docker-compose.override.yml
```

If the container is already running, restart it.

Currently, there is no documentation on the format for the cluster type
definition files beyond the [well-documented
examples](cluster-types-examples/).  They should prove sufficient.


## Installation

Concertim Cluster Builder is intended to be deployed as a Docker container.
There is a Dockerfile in this repo that the image can be built from.  The
cluster builder service is configured to run on port `42378` of the container.

An image can be built with the following command:

```bash
docker build --tag concertim-cluster-builder:latest .
```

## Usage

Once the docker image is configured with cluster type definitions and has been
built (see [Cluster type definitions](#cluster-type-definitions) and
[Installation](#installation) above) a container can be started from that image
with the following command.

```bash
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

Copy the example [dev
docker-compose-override](docker-compose.override.yml.dev.example) to
`docker-compose.override.yml` and edit to set your local user's (that is the
user on your laptop) UID and GID. Doing this will prevent issues with file
permissions for the shared files.  By default, the service is exposed on all of
the host machine's IP addresses, you can change this by editing the `ports`
section of the override file.

```bash
cp docker-compose.override.yml.dev.example docker-compose.override.yml
$EDITOR docker-compose.override.yml
```

Copy across the example cluster type definitions.

```bash
for i in examples/cluster-types/* ; do
  ln -s ../../${i} instance/cluster-types-enabled/
done

for i in examples/hot/* ; do
  ln -s ../../${i} instance/hot/
done
```

Start the docker container by running the following.

```bash
docker compose -f docker-compose-dev.yml up
```
