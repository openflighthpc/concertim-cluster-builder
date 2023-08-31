# syntax=docker/dockerfile:1.4
FROM python:3.8-slim-buster
LABEL com.alces-flight.concertim.role=cluster_builder com.alces-flight.concertim.version=0.0.1

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

# Copy across the example cluster types and HOT templates.
#
# In a production deployment it is expected that a docker volume will be
# mounted at /app/instance to provide the production cluster types.
COPY ./examples/cluster-types/ /app/instance/cluster-types-enabled/
COPY ./examples/hot/ /app/instance/hot/

EXPOSE 42378

CMD ["flask", "--app", "cluster_builder", "run", "-h", "0.0.0.0", "-p", "42378"]
