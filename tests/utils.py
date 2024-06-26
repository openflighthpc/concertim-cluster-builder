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

from datetime import datetime
import json
import os

def write_cluster_definition(app, definition, name="test", last_modified=None):
    enabled_dir = os.path.join(app.instance_path, "cluster-types-enabled")
    path = os.path.join(enabled_dir, name, "cluster-type.yaml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as test_file:
        if isinstance(definition, dict):
            test_file.write(json.dumps(definition))
        elif isinstance(definition, str):
            test_file.write(definition)
        else:
            raise TypeError(f"expected definition to be dict or str, got {type(definition)}")
    if last_modified:
        if type(last_modified) is str:
            last_modified = datetime.timestamp(datetime.fromisoformat(last_modified))
        last_accessed = last_modified
        os.utime(path, (last_accessed, last_modified))


def write_hot_component(app, hot, parent_dir, name="test", last_modified=None):
    enabled_dir = os.path.join(app.instance_path, "cluster-types-enabled")
    path = os.path.join(enabled_dir, parent_dir, 'components', f"{name}.yaml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as test_file:
        if isinstance(hot, dict):
            test_file.write(json.dumps(hot))
        elif isinstance(hot, str):
            test_file.write(hot)
        else:
            raise TypeError(f"expected hot to be dict or str, got {type(hot)}")
    if last_modified:
        if type(last_modified) is str:
            last_modified = datetime.timestamp(datetime.fromisoformat(last_modified))
        last_accessed = last_modified
        os.utime(path, (last_accessed, last_modified))


def remove_path(path):
    """
    Return a function that takes a dict and removes the given path from it.

    >>> fn = remove_path(["foo", "bar"])
    >>> d = {"foo": {"bar": "target", "baz": "remains"}, "quux": "also remains"}
    >>> fn(d)
    >>> d
    {'foo': {'baz': 'remains'}, 'quux': 'also remains'}
    """
    def inner(data):
        def worker(data, path):
            if len(path) == 1:
                del data[path[0]]
            else:
                p = path.pop()
                worker(data[p], path)

        worker(data, list(reversed(path)))

    return inner

def set_path(path, value):
    """
    Return a function that takes a dict and sets the value at the given path.

    >>> fn = set_path(["foo", "bar"], "added")
    >>> d = {"foo": {"baz": "remains"}, "quux": "also remains"}
    >>> fn(d)
    >>> d
    {'foo': {'baz': 'remains', 'foo': 'added'}, 'quux': 'also remains'}
    """
    def inner(data):
        pass

        def worker(data, path):
            if len(path) == 1:
                data[path[0]] = value
            else:
                p = path.pop()
                worker(data[p], path)

        worker(data, list(reversed(path)))

    return inner


