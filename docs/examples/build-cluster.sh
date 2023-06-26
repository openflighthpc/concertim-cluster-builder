#!/bin/bash

set -e
set -o pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# The base URL against which relative URLs are constructed.
BASE_URL="http://localhost:42378"

USERNAME=${1}
PASSWORD=${2}
PROJECT_NAME=${3}
CLUSTER_NAME=${4}
GATEWAY_IP=${5}
SSH_KEY=${6}

BODY=$(jq --null-input \
    --arg username "${USERNAME}" \
    --arg password "${PASSWORD}" \
    --arg project_name "${PROJECT_NAME}" \
    --arg cluster_name "${CLUSTER_NAME}" \
    --arg gateway_pri_ip "${GATEWAY_IP}" \
    --arg ssh_key "${SSH_KEY}" \
    '
{
    "cloud_env": {
        "auth_url": "http://10.151.0.184:35357/v3",
        "username": $username,
        "password": $password,
        "project_name": $project_name,
        "user_domain_name": "default",
        "project_domain_name": "default"
    },
    "cluster": {
        "name": $cluster_name,
        "cluster_type_id": "hpc-cluster-building-blocks",
        "parameters": {
          "clustername": $cluster_name,
          "ssh-key": $ssh_key,
          "gateway-pri-ip": $gateway_pri_ip
        }
    }
}
'
)

# Run curl with funky redirection to capture response body and status code.
BODY_FILE=$(mktemp)
HTTP_STATUS=$(
curl -s -k \
    -w "%{http_code}" \
    -o >(cat > "${BODY_FILE}") \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json' \
    -X POST "${BASE_URL}/clusters/" \
    -d "${BODY}"
)

if [ "${HTTP_STATUS}" == "200" ] || [ "${HTTP_STATUS}" == "201" ] ; then
    cat "$BODY_FILE"
else
    echo "Building cluster failed" >&2
    cat "$BODY_FILE" >&2
    exit 1
fi
