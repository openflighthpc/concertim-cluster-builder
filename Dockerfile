# syntax=docker/dockerfile:1.4
FROM python:3.8-slim-buster
LABEL com.alces-flight.concertim.role=cluster_builder com.alces-flight.concertim.version=0.0.1

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 42378

CMD ["flask", "--app", "cluster_builder", "run", "-h", "0.0.0.0", "-p", "42378"]
