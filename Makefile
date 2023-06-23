.PHONY: help all base dev upgrade check clean run test build base.build

help:
	@echo 'Usage:'
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' | sed -e 's/^/ /'

objects = $(wildcard *.in)
outputs := $(objects:.in=.txt)

## all: build all .txt files
all: $(outputs)

%.txt: %.in
	pip-compile --verbose --generate-hashes --output-file $@ $<

dev-requirements.txt: requirements.txt

## base: build requirements.txt
base: requirements.txt

## dev: build dev-requirements.txt
dev: dev-requirements.txt

## pip.install: install all dependencies
pip.install: $(outputs)
	pip-sync --ask $(outputs)

## pip.install-base: install base dependencies only
pip.install-base: requirements.txt
	pip-sync --ask requirements.txt

## pip.upgrade: upgrade base dependencies only
pip.upgrade: requirements.txt
	pip-compile --upgrade --generate-hashes $<

## check: check pip-tools installed
check:
	@if ! command -v pip-compile > /dev/null; then echo "pip-tools not installed!"; fi

## clean: clean all *.txt files
clean: check
	- rm *.txt

## run.dev: run Flask debug server
run.dev:
	flask --app 'calibre_rest:create_app("dev")' run --debug

## run: run gunicorn server
run:
	gunicorn 'calibre_rest:create_app("prod")' -c gunicorn.py

## test: run unit tests
test:
	pytest -v

## build.base: build base Docker image
base.build: docker/base.Dockerfile
	docker build . -f docker/base.Dockerfile -t calibre_rest_base:latest

%.build: docker/%.Dockerfile base.build
	docker build . -f $< -t calibre_rest:$(version)-$*

## build: build all Docker images
build: app.build calibre.build
