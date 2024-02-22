# Development

To setup for development you will need to:

1. Copy the example cluter type definitions and their HOT templates to the
   flask app's instance directory.
2. Build the docker image.
3. Start the docker container with the correct volumes and user settings.

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

## Build the docker image

```bash
docker build --network=host --tag concertim-cluster-builder:latest .
```

## Start the docker container

Start the docker container by running the following.  The `--user` setting will
prevent issues with the file permissions for the shared files.

```bash
docker run -d \
    --stop-signal SIGINT \
    --network=host \
    --publish 42378:42378 \
    --volume .:/app \
    --user "$(id -u):$(id -g)" \
    concertim-cluster-builder \
    flask --app cluster_builder run -h 0.0.0.0 -p 42378 --debug
```

## Test suite

There is a test suite located in the `tests` directory.  It can be ran in a
temporary container by using the `pytest` test runner:

```bash
docker run --rm \
    --stop-signal SIGINT \
    --network=host \
    --publish 42378:42378 \
    --volume .:/app \
    concertim-cluster-builder \
    pytest -v
```

Documentation on writting tests can be found at
https://docs.pytest.org/en/7.4.x/ and
https://flask.palletsprojects.com/en/2.3.x/testing/.
