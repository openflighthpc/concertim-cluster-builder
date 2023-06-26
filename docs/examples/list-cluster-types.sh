#!/bin/bash

set -e
set -o pipefail

# The base URL against which relative URLs are constructed.
BASE_URL="http://localhost:42378"

curl -s -k \
  -H 'Accept: application/json' \
  -X GET "${BASE_URL}/cluster-types/"
