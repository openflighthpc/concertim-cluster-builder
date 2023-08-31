# Development

There is a [docker-compose.yml](docker-compose.yml) file that creates a docker
container suitable for development. The contents of this repository are shared
with the docker container using docker volumes, meaning that any changes made
to the local source code will be automatically picked up by the service running
inside the container.

Note: this docker-compose.yml file is not intended for a production deployment.

To setup for development you will need to:

1. Copy the example cluter type definitions and their HOT templates to the
   flask app's instance directory.
2. Optionally, create a docker-compose.override.yml file.
3. Start the docker container.

These are explained in more detail below.

## Copy across the example cluster type definitions.

```bash
for i in examples/cluster-types/* ; do
  ln -s ../../${i} instance/cluster-types-enabled/
done

for i in examples/hot/* ; do
  ln -s ../../${i} instance/hot/
done
```

## Optionally, create a docker-compose.override.yml file

It is expected that the settings in [docker-compose.yml](docker-compose.yml)
will work for most all local setups.  However, there may be cases where some
local configuration that should not be committed to the git repo may be
necessary.

If this is the case, copy the example
[docker-compose.override.yml.example](docker-compose.override.yml.example) to
`docker-compose.override.yml` and edit it to override the configuration in
`docker-compose.yml`.

For example, your local user id may not be the expected `1000`.  If so, you
will want to set the correct user and group id to prevent issues with file
permissions for the shared files.

By default, the service is exposed on all of the host machine's IP addresses,
you can change this by editing the `ports` section of the override file.

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
$EDITOR docker-compose.override.yml
```

## Start the docker container

Start the docker container by running the following.

```bash
docker compose up
```

## Test suite

There is a test suite located in the `tests` directory.  It can be ran in a
temporary container by using the `pytest` test runner:

```
docker compose run --rm cluster_builder pytest -v
```

Documentation on writting tests can be found at
https://docs.pytest.org/en/7.4.x/ and
https://flask.palletsprojects.com/en/2.3.x/testing/.
