"""
==============================================================================
 Copyright (C) 2024-present Alces Flight Ltd.

 This file is part of Concertim Cluster Builder.

 This program and the accompanying materials are made available under
 the terms of the Eclipse Public License 2.0 which is available at
 <https://www.eclipse.org/legal/epl-2.0>, or alternative license
 terms made available by Alces Flight Ltd - please direct inquiries
 about licensing to licensing@alces-flight.com.

 Concertim Visualisation App is distributed in the hope that it will be useful, but
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
 IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
 OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
 PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
 details.

 You should have received a copy of the Eclipse Public License 2.0
 along with Concertim Visualisation App. If not, see:

  https://opensource.org/licenses/EPL-2.0

 For more information on Concertim Cluster Builder, please visit:
 https://github.com/openflighthpc/concertim-cluster-builder
==============================================================================
"""

from flask import Blueprint
from flask import make_response
from flask import request

from .models import ClusterTypeRepo

bp = Blueprint('cluster-types', __name__, url_prefix="/cluster-types")
ATTRIBUTES = ["id", "title", "description", "parameters", "parameter_groups", "last_modified", "order", "logo_url", "instructions"]

@bp.route('/')
def index():
    cluster_types = []
    last_modified = None
    for ct in ClusterTypeRepo.all():
        if last_modified == None or ct.last_modified > last_modified: last_modified = ct.last_modified
        cluster_types.append(ct.asdict(ATTRIBUTES))
    if (request.if_modified_since and last_modified != None and
       int(request.if_modified_since.timestamp()) == int(last_modified.timestamp())):
        return '', 304

    r = make_response(cluster_types)
    r.last_modified = last_modified
    return r

@bp.route('/<string:id>')
def show_cluster_type(id):
    type = ClusterTypeRepo.find(id)
    last_modified = type.last_modified
    if (request.if_modified_since and int(request.if_modified_since.timestamp()) == int(last_modified.timestamp())):
        return '', 304

    r = make_response(type.asdict(ATTRIBUTES))
    r.last_modified = type.last_modified
    return r
