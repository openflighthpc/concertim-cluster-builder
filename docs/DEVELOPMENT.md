# Development

There is a [docker-compose-dev.yml](docker-compose.yml) file that creates a docker
container suitable for development. The contents of this repository are shared
with the docker container using docker volumes, meaning that any changes made
to the local source code will be automatically picked up by the service running
inside the container.

Note: this docker-compose-dev.yml file is not intended for a production deployment.

To setup for development you will need to:

1. Create a docker-compose.override.yml file.
2. Copy across the example cluter type definitions and their HOT templates.
3. Start the docker container.

These are explained in more detail below.

## Create the docker-compose.override.yml file

Copy the example [dev
docker-compose-override](docker-compose.override.yml.dev.example) to
`docker-compose.override.yml` and edit to set your local user's (that is the
user on your laptop) UID and GID. Doing this will prevent issues with file
permissions for the shared files.  By default, the service is exposed on all of
the host machine's IP addresses, you can change this by editing the `ports`
section of the override file.

```bash
cp docker-compose.override.yml.dev.example docker-compose.override.yml
$EDITOR docker-compose.override.yml
```

## Copy across the example cluster type definitions.

```bash
for i in examples/cluster-types/* ; do
  ln -s ../../${i} instance/cluster-types-enabled/
done

for i in examples/hot/* ; do
  ln -s ../../${i} instance/hot/
done
```

## Start the docker container

Start the docker container by running the following.

```bash
docker compose -f docker-compose-dev.yml up
```
