DOCKER_BUILDKIT=1
RUN_ARGS?=

all: run-ioc

initialize:
	# git submodule update --init --recursive
	:

build-base: initialize docker/Dockerfile.base
	DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
		docker build --tag pcds-ioc-machine-base:latest --file docker/Dockerfile.base .

build-epics: build-base docker/Dockerfile.R7.0.2-2.0
	DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
		docker build --tag pcds-epics-base:latest --file docker/Dockerfile.R7.0.2-2.0 .

build-ioc: build-base build-epics docker/Dockerfile.ioc ./afs ./cds ./usr
	DOCKER_BUILDKIT=$(DOCKER_BUILDKIT) && \
		docker build --tag pcds-ioc:latest --file docker/Dockerfile.ioc . 

run-ioc: build-ioc
	docker run -it $(RUN_ARGS) pcds-ioc:latest

run-ioc-as-root:
	make RUN_ARGS="--user root" run-ioc

.PHONY: build-ioc build-base build-epics initialize run-ioc run-ioc-as-root all
