DOCKER_BUILDKIT=1

all: run-ioc

initialize:
	# git submodule update --init --recursive
	:

build-base: initialize
	DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
		docker build --tag pcds-ioc-machine-base:latest --file docker/Dockerfile.base .

build-epics: build-base
	DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
		docker build --tag pcds-epics-base:latest --file docker/Dockerfile.R7.0.2-2.0 .

build-ioc: build-base build-epics
	DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
		docker build --tag pcds-ioc:latest --file docker/Dockerfile.ioc . 

run-ioc: build-ioc
	docker run -it pcds-ioc:latest

.PHONY: build-ioc build-base build-epics initialize run-ioc all
