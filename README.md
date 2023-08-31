# Concertim Cluster Builder

The Concertim Cluster Builder is a Python daemon process providing an HTTP API
to receive requests to build clusters of pre-defined types.

It is expected that such requests will be made by the [Concertim Visualisation
App](https://github.com/alces-flight/concertim-ct-visualisation-app) and that
the [Concertim OpenStack
Service](https://github.com/alces-flight/concertim-openstack-service) will
report the existence of those clusters to Concertim Visualisation App as and
when they become available.

## Installation

Concertim Cluster Builder is intended to be deployed as a Docker container.
There is a Dockerfile in this repo that the image can be built from and a
docker compose file that should be used to start the container.

1. Clone the repository
    ```bash
    git clone https://github.com/alces-flight/concertim-cluster-builder.git
    ```
2. Build the docker image
    ```bash
    docker build --network=host --tag concertim-cluster-builder:latest .
    ```

## Configuration

Concertim Cluster Builder has three separate elements to its configuration: 1)
configuring access to the cloud environment; 2) configuring the network the
service is exposed on; and 3) configuring the enabled cluster type definitions.
These are detailed below.

### Cloud environment access

All required configuration to access the cloud environment is sent in the
request to build a cluster.  More details on the format can be found in the
[API documentation](/docs/api.md).

### Exposing the service on the desired network

By default, Concertim cluster builder is configured to expose its service on
all of the host machine's IP addresses.  If this is not suitable for you, it
can be configured by editing the `docker-compose.prod.yml` file and changing
the `ports` entry.

### Cluster type definitions

Concertim cluster builder needs to be configured with the enabled cluster type
definitions. The enabled definitions are to be created in the docker
container's `/app/instance/cluster-types-enabled/` directory.

The Docker image is built with some example cluster type definitions enabled by
default.

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

Optionally, enable the example definitions

```bash
cd /usr/share/concertim-cluster-builder/cluster-types-enabled/
for i in ../cluster-types-available/* ; do
  ln -s ${i} .
done
```

Edit the [docker-compose.prod.yml](docker-compose.prod.yml) file and uncomment
the `services.cluster_builder.volumes` section.  It should look like this:

```
    # Optionally, mount a volume to `/app/instance` to allow configuration of
    # the cluster type definitions.  Without this (or some similar mechanism),
    # the example cluster types will be used.
    volumes:
      - /usr/share/concertim-cluster-builder/:/app/instance
```

If the container is already running, restart it.

Currently, there is no documentation on the format for the cluster type
definition files beyond the [well-documented
examples](cluster-types-examples/).  They should prove sufficient.


## Usage

Once the docker image is configured with cluster type definitions and has been
built (see [Cluster type definitions](#cluster-type-definitions) and
[Installation](#installation) above) a container can be started from that image
with the following command.

```bash
docker compose -f docker-compose.prod.yml up
```

## HTTP API

The HTTP API is documented in the [API documentation](/docs/api.md).


## Development

See the [development docs](docs/DEVELOPMENT.md) for details on development and
getting started with development.
