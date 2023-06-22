import glob
import os
import re
import yaml

from flask import (Blueprint, current_app)

bp = Blueprint('cluster-types', __name__, url_prefix="/cluster-types")

@bp.route('/')
def index():
    return get_cluster_types()


def get_cluster_types():
    """
    Return list of cluster types.

    The cluster types are defined as HOT templates located in the
    cluster-types-enabled directory in the app's instance path.
    """
    types_dir = os.path.join(current_app.instance_path, "cluster-types-enabled")
    files = glob.glob(os.path.join(types_dir, "*.yaml"))

    types = []

    for file in files:
        id = os.path.splitext(os.path.basename(file))[0]
        with open(file, 'r') as stream:
            try:
                hot_template = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                current_app.logger.error(f'failed to load template: {id} {exc}')
            else:
                cluster_type = {
                        "id": id,
                        "title": hot_template.get("title", id),
                        "description": hot_template.get("description", id),
                        "parameters": hot_template.get("parameters", [])
                        }
                types.append(cluster_type)

    return types
