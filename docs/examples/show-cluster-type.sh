#!/bin/bash

set -e
set -o pipefail

# The base URL against which relative URLs are constructed.
BASE_URL="http://localhost:42378"

CLUSTER_TYPE_ID="${1:-slurm-team-edition}"

curl -s -k \
  -H 'Accept: application/json' \
  -X GET "${BASE_URL}/cluster-types/${CLUSTER_TYPE_ID}"
