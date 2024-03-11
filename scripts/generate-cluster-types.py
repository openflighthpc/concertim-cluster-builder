#!/usr/bin/env python

from typing import Any
from urllib.parse import urlparse
import pathlib
import shutil

from heatclient.common import template_utils
from jsonschema.exceptions import (best_match)
import click
import jsonschema
import ruamel.yaml

yaml = ruamel.yaml.YAML(typ="rt", pure=True)
yaml.indent(sequence=4, offset=2)

DEFAULT_TEMPLATES_DIR = pathlib.Path(__file__).parent.parent.joinpath('examples', 'templates')

@click.command()
@click.argument('cluster_types', nargs=-1, type=click.Path(exists=True, path_type=pathlib.Path))
@click.option('--templates_dir',
              help="Path to the templates directory",
              default=DEFAULT_TEMPLATES_DIR,
              show_default=True,
              metavar='TEMPLATES_DIR',
              type=click.Path(exists=True, path_type=pathlib.Path, file_okay=False)
              )
@click.option('-v', '--verbose', is_flag=True)
def main(cluster_types, templates_dir, verbose):
    """
    Generate components and user data for CLUSTER_TYPES from their
    cluster-type.yaml using the templates found in TEMPLATES_DIR.
    """
    for ct in cluster_types:
        if ct.is_file():
            name = ct.parent.name
            definition_path = ct.resolve()
            cluster_type_dir = ct.parent.resolve()
        else:
            name = ct.name
            definition_path = ct.joinpath("cluster-type.yaml").resolve()
            cluster_type_dir = ct.resolve()
        click.echo(f"Generating cluster type {format_path(name, fg='blue')}...")
        if verbose:
            click.echo(f"--> Using cluster type definition {format_path(definition_path)}")

        definition = load_definition(definition_path, verbose=verbose)
        if definition is None:
            click.echo(f'--> {click.style("Failed", fg="red")}')
            continue
        success = generate_cluster_type(cluster_type_dir, definition, templates_dir, verbose)
        if verbose:
            if success:
                click.echo(f'--> {click.style("Completed", fg="green")}')
            else:
                click.echo(f'--> {click.style("Failed", fg="red")}')


Components = list[Any]
ParameterOverrides = dict[str, Any]
Definition = tuple[Components, ParameterOverrides]

SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {
            "type": "string",
            "enum": ["heat"]
        },
        "components": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "optional": {"type": "boolean"},
                    "user_data": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "write_files": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["name", "write_files"],
                    },
                },
                "required": ["name"],
            }
        },
        "parameter_overrides": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "properties": {
                        "label": { "type": "string" },
                        "description": { "type": "string" },
                        "default": {},
                        "hidden": { "type": "boolean" },
                        "constraints": { "type": "array" },
                        "immutable": { "type": "boolean" },
                        "tags": {}
                    },
                    "additionalProperties": False,
                }
            }
        }
    },
    "required": ["kind", "components"],
}
def load_definition(definition_path, verbose) -> Definition | None:
    try:
        definition = yaml.load(definition_path)
        jsonschema.validate(instance=definition, schema=SCHEMA)
        return definition["components"], definition.get("parameter_overrides", {})
    except FileNotFoundError as exc:
        click.secho(f"  {exc.strerror}: {exc.filename}", err=True, fg="red")
        return None
    except (ruamel.yaml.parser.ParserError, ruamel.yaml.scanner.ScannerError) as exc:
        click.echo(f"  Failed to parse {format_path(definition_path)}: {exc}", err=True)
        return None
    except jsonschema.ValidationError as exc:
        error_message = best_match([exc]).message
        click.echo(f'--> Validating schema failed: {error_message}', err=True)
        if verbose:
            click.echo(f'--> Validating schema failed: {exc}', err=True)
        return None


def generate_cluster_type(cluster_type_dir, definition, templates_dir, verbose) -> bool:
    components = definition[0]
    param_overrides = definition[1]
    user_data_snippets_dir = templates_dir.joinpath('snippets', 'user_data/')
    component_templates_dir = templates_dir.joinpath('components')
    component_dest_dir = cluster_type_dir.joinpath('components')
    user_data_dest_dir = cluster_type_dir.joinpath('user_data')

    for component in components:
        if verbose:
            click.echo(f"--> Processing component {component['name']}")

        # Install the component itself.
        template_path = component_templates_dir.joinpath(f"{component['name']}.yaml")
        if not template_path.exists():
            click.secho(f"    Component {template_path} does not exist", err=True, fg="red")
            return False
        component_dest_dir.mkdir(exist_ok=True)
        if verbose:
            click.echo(f"    Installing component from {format_path(template_path)} to {format_path(component_dest_dir)}")
        shutil.copy(template_path, component_dest_dir)

        # Install any files the component references.  These might be
        # referenced via the `get_file` intrinsic function or via a `type`
        # string ending in `.yaml` or `.json`.  If these aren't copied over the
        # component will not be valid.
        files, _ = template_utils.get_template_contents(str(template_path), fetch_child=True)
        for strpath in files:
            url = urlparse(strpath)
            if url.scheme == "file":
                path = pathlib.Path(url.path)
                if path.is_relative_to(templates_dir):
                    dest = cluster_type_dir.joinpath(path.relative_to(templates_dir))
                    if verbose:
                        click.echo(f"    Installing referenced file {format_path(path)} to {format_path(dest)}")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, dest)
                else:
                    # A relative path that isn't under the templates directory.
                    # This is probably not something that we should support.
                    if verbose:
                        click.secho(f"    Ignoring referenced file {format_path(path)}: it is outside of {format_path(templates_dir)}.  Your template may not work correctly!", fg="red")

        # Generate and install user_data files as described in
        # cluster-type.yaml.  These might override a reference file install.
        # That is to be expected.
        if component.get('user_data') is not None:
            if verbose:
                click.echo(f"    Creating user_data")
            user_data = parse_file(user_data_snippets_dir.joinpath('base.yaml'))
            if user_data is None:
                return False
            for write_file in component['user_data']['write_files']:
                snippet_path = user_data_snippets_dir.joinpath('write_files', f'{write_file}.yaml')
                if verbose:
                    click.echo(f"    --> Including snippet from {format_path(snippet_path, relative_to=templates_dir)}")
                content = parse_file(snippet_path)
                if content is None:
                    return False
                user_data['write_files'].append(content)
            dest = user_data_dest_dir.joinpath(f"{component['user_data']['name']}.yaml")
            dest.parent.mkdir(exist_ok=True)
            if verbose:
                click.echo(f"    Installing user_data to {format_path(dest)}")
            yaml.dump(user_data, dest)

    if len(param_overrides) > 0:
        if verbose:
            click.echo(f"--> Merging parameter overrides")
        # Merge parameter overrides.
        for component in components:
            component_path = component_dest_dir.joinpath(f"{component['name']}.yaml")
            if verbose:
                click.echo(f"    Merging overrides into {format_path(component_path)}")
            if not merge_parameter_overrides(param_overrides, component_path):
                click.secho(f"    Failed to merge parameter overrides into {format_path(component_path)}", err=True, fg="red")
                return False

    return True


def merge_parameter_overrides(param_overrides, component_file) -> bool:
    component = parse_file(component_file)
    if component is None:
        return False
    for id, overrides in param_overrides.items():
        if id not in component['parameters']:
            continue
        for key, value in overrides.items():
            component['parameters'][id][key] = value

    yaml.dump(component, component_file)
    return True


def parse_file(path) -> dict[str, Any]|None:
    try:
        return yaml.load(path)
    except FileNotFoundError as exc:
        click.secho(f"    {exc.strerror}: {exc.filename}", err=True, fg="red")
        return None
    except (ruamel.yaml.parser.ParserError, ruamel.yaml.scanner.ScannerError) as exc:
        click.echo(f"  Failed to parse {format_path(path, 'red')}: {exc}", err=True)
        return None


def format_path(path, fg='cyan', relative_to=None) -> str:
    if relative_to:
        path = path.relative_to(relative_to)
    return click.style(click.format_filename(path), fg=fg)


if __name__ == '__main__':
    main()
