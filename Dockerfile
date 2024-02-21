# syntax=docker/dockerfile:1.4
FROM python:3.10-slim-bookworm

ARG BUILD_DATE
ARG BUILD_VERSION
ARG BUILD_REVISION

LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.version=$BUILD_VERSION
LABEL org.opencontainers.image.revision=$BUILD_REVISION
LABEL org.opencontainers.image.title="Alces Concertim Cluster Builder"

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
         build-essential \
    && apt-get clean \
    && rm -rf /usr/share/doc /usr/share/man /var/lib/apt/lists/*

COPY requirements.txt /app
RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt-get remove --yes \
         build-essential

COPY . /app

# Copy across the example cluster types and enable them all.
#
# In a production deployment it is expected that a docker volume will be
# mounted at /app/instance to provide the production cluster types.
RUN rm -f /app/instance/cluster-types-enabled/* \
          /app/instance/cluster-types-available/*
COPY ./examples/cluster-types/ /app/instance/cluster-types-available/
RUN <<EOT
    cd /app/instance/cluster-types-enabled/
    for i in ../cluster-types-available/* ; do
        ln -s ${i} .
    done
EOT

ENV HOST=0.0.0.0
ENV PORT=42378
EXPOSE 42378

CMD flask --app cluster_builder run -h $HOST -p $PORT
