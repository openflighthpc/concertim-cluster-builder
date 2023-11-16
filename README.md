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
There is a Dockerfile in this repo for building the image.

1. Clone the repository
    ```bash
    git clone https://github.com/alces-flight/concertim-cluster-builder.git
    ```
2. Build the docker image
    ```bash
    docker build --network=host --tag concertim-cluster-builder:latest .
    ```
3. Start the docker container
    ```bash
	docker run -d --name concertim-cluster-builder \
        --stop-signal SIGINT \
		--network=host \
		--publish <Host>:42378:42378 \
		concertim-cluster-builder
    ```

The above will start Cluster Builder with the example cluster type definitions
enabled.  To use alternate cluster type definitions see below.

## Configuration

Concertim Cluster Builder has three separate elements to its configuration: 1)
configuring access to the cloud environment; and 2) configuring the enabled
cluster type definitions. These are detailed below.

### Cloud environment access

All required configuration to access the cloud environment is sent in the
request to build a cluster.  More details on the format can be found in the
[API documentation](/docs/api.md).

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

Copy across the example definitions and their HOT templates.

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

Mount the directory `/usr/share/concertim-cluster-builder/` to `/app/instance`,
when starting the docker container.

```bash
docker run -d --name concertim-cluster-builder \
    --stop-signal SIGINT \
    --network=host \
    --publish <Host>:42378:42378 \
    --volume /usr/share/concertim-cluster-builder/:/app/instance \
    concertim-cluster-builder
```

Currently, there is no documentation on the format for the cluster type
definition files beyond the [well-documented
examples](cluster-types-examples/).  They should prove sufficient.


## Usage

Once the docker image has been built and the cluster type definitions have been
configured (see [Cluster type definitions](#cluster-type-definitions) and
[Installation](#installation) above), start the container with the following
command.

```bash
docker run -d --name concertim-cluster-builder \
    --stop-signal SIGINT \
    --network=host \
    --publish <Host>:42378:42378 \
    --volume /usr/share/concertim-cluster-builder/:/app/instance \
    concertim-cluster-builder
```

## HTTP API

The HTTP API is documented in the [API documentation](/docs/api.md).


## Development

See the [development docs](docs/DEVELOPMENT.md) for details on development and
getting started with development.
