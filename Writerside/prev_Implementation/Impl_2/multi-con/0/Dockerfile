# Dockerfile
FROM openthread/environment:latest

WORKDIR /openthread

RUN ./script/cmake-build simulation
#/openthread/build/simulation/examples/apps/cli
#RUN ./script/cmake-build posix
#:/openthread/build/posix/src/posix#

ENV PATH="/openthread/build/simulation/examples/apps/cli:${PATH}"
# ot-cli-ftd 1
