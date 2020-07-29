#!/bin/sh
docker build --no-cache -f images/test/Dockerfile -t atf_docker/test:latest images/test
