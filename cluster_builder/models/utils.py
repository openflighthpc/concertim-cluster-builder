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

from flask import (abort)

def merge_parameters(cluster_type, given_answers):
    """
    Return the parameters to be sent to the cloud service.

    The value for each parameter can come from (in order of precedence):

    1. Hardcoded parameters in the cluster type definition.
    2. User given answer.
    3. Default set in either the cluster type definition or the HOT
    template.
    """
    merged_parameters = {}
    for name, parameter in cluster_type.parameters.items():
        given_answer = given_answers is not None and given_answers.get(name)
        if given_answer is not None:
            merged_parameters[name] = given_answer
        else:
            merged_parameters[name] = parameter.get("default")
    for name, value in cluster_type.hardcoded_parameters.items():
        merged_parameters[name] = value
    return merged_parameters


def remove_unwanted_answers(cluster_type, selections, answers):
    """
    Filter answers to remove any that are for a parameter only defined in a
    de-selected optional component.
    """
    filtered_answers = {}
    filtered_parameter_ids = []
    for component in cluster_type.components:
        is_selected = selections.get(component.name, False)
        if component.is_optional and not is_selected:
            continue
        for id in component.parameters:
            if id not in filtered_parameter_ids:
                filtered_parameter_ids.append(id)
    for id, answer in answers.items():
        if id in filtered_parameter_ids:
            filtered_answers[id] = answer
    return filtered_answers


def assert_parameters_present(cluster_type, answers):
    """
    Asserts that all parameters defined in the cluster type either have a
    default or are present in answers.
    """
    missing = []
    for name, parameter in cluster_type.parameters.items():
        if parameter.get("default") is not None:
            continue
        if answers is not None and answers.get(name) is not None:
            continue
        missing.append(name)
    if len(missing) > 0:
        abort(400, "Missing parameters: {}".format(", ".join(missing)))
