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


## Installation

XXX TBC


## Usage

XXX TBC: How to start the service.

[API documentation](/docs/api.md) is available.
