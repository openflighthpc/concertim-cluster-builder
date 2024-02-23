# Cluster type generation

The heat-backed example cluster type definitions' components and user data can
be generated using [a build script](../scripts/generate-cluster-types.py) the
cluster type's `cluster-type.yaml` files and the [example template
files](../examples/templates/).  This document describes that process.

It is also possible to hand-craft a heat-backed cluster type if the limitations
of the build process are not suitable for your requirements.


## Running the build script

The build script can be ran as follows.  Replace `path/to/cluster/type` with
the path to the cluster type you wish to generate.

```bash
docker run --rm \
    --stop-signal SIGINT \
    --network=host \
    --volume .:/app \
    --user $(id -u):$(id -g) \
    concertim-cluster-builder \
    path/to/cluster/type/
```

By default, it will build the cluster type at the specified path using the
templates at [../examples/templates/](../examples/templates/). For more details
run the script with the `--help` flag.


## Build process limitations

The build process currently has a few limitations and makes certain assumptions.

1. It can only build heat-backed cluster types.  Sahara and Magnum backed
   cluster types must be manually created.
2. It is optimised for building cluster types which select from a handful of
   predefined components.
3. The only configuration supported when including a component is specifying
   the user data that should be included.
4. The user data will be in `#cloud-config` format and the only part of the
   user data that can be configured is the contents of the `write_files`
   section.


## Template directory layout

The template directory has a specific layout:

```
templates/
├── components
│   ├── <component name>.yaml
│   └── ...
├── snippets
│   └── user_data
│       ├── base.yaml
│       └── write_files
│           ├── <user data snippet name>.yaml
│           └── ...
└── user_data
    ├── <referenced user data file>.yaml
    └── ...
```

The components that constitue a cluster type are defined in the
`templates/components/` directory.  They are expected to be a HOT template.  If
any of their resources require user data they should load it via the `get_file`
intrinsic function, e.g.,

```yaml
  my-resource:
    type: OS::Nova::Server
    properties:
      # ...
      user_data:
        str_replace:
          template: { get_file: ../user_data/my-resource.yaml }
          params: {}
```

The reference should be a relative path to an entry in the
`templates/user_data` directory.  That file needs to exist and needs to be
valid YAML, but its content is otherwise unimportant.

The entries in `templates/snippets/user_data/write_files/` are expected to be
valid content for a `write_files` entry for a `#cloud-config` user data file.  E.g.,

```yaml
content: |
    echo "Hello, world!"
path: /var/lib/firstrun/scripts/99_hello.bash
permissions: '0600'
owner: root:root
```

These snippets are used, by the build script, to dynamically build the user
data for different clusters types.



## cluster-type.yaml format

The `cluster-type.yaml` file serves two purposes, one is to generate the
cluster type's components and user data files, the other is to present the
cluster type to the user for launching a cluster from that type.  Here we
document only the first aspect; generation of the cluster type's components and
user data files.

Generation is only supported for cluster type's of `kind: heat`.  `magnum` and
`sahara` cluster types need to have their files generated manually.

The `cluster-type.yaml` file needs to contain the following:

```yaml
kind: heat

components:
  # A component that requires user data generating.
  - name: <component name>
    user_data:
      name: <user data name>
      write_files:
        - <user data snippet name>
  # A component that doesn't require user data generating.
  - name: <component name>
```

For each component named in `components` the build script will (1) copy the
component from the templates directory; (2) copy any files referenced by that
component; (3) optionally generate the user data for that component.  These are
explained in more detail below.

The build script will look for a file named `<component name>.yaml` in the
[component templates directory](../examples/templates/components). If one
cannot be found, processing the cluster type is aborted with an error. If it is
found it is copied to the cluster type's `component` directory.

The component is then parsed for uses of the openstack `get_file` intrinsic
function and for resources with a type that is a string ending in `.yaml` or
`.json`, such as might be used in a `OS::Heat::ResourceGroup`'s `resource_def`.
If any references are found to files in the templates directory, they are
copied to the cluster type directory.  If any other references are found they
are ignored.

If the `user_data` section is provided for a component it is created by
starting with the [base user data
snippet](../examples/templates/snippets/user_data/base.yaml).  Then for each
entry in the `write_files` list the build script looks for a file named `<user
data name>.yaml` in the [user data snippets
directory](../examples/templates/snippets/user_data/write_files/). If one
cannot be found, processing the cluster type is aborted with an error. If it is
found it is appended to the `write_files` array in the base user data snippet.
Once the user data is generated it is saved to the cluster type's `user_data`
directory as `<user data name>.yaml`.

NOTE: This process requires that the user data is (1) referenced via the
`get_file` intrinsic function; (2) the reference is a relative path to
`../user_data/<user data name>.yaml`; and (3) that the `<user data name>` used
in the component matches the `<user data name>` used for that component in the
cluster type's `cluster-type.yaml`.
