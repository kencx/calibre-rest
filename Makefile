.PHONY: help all base dev upgrade check clean run test unittest build

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

## run: run Gunicorn server
run:
	python3 app.py

## test: run all tests
test:
	pytest

## test: run unit tests only
unittest:
	pytest --ignore=tests/integration

%.build: docker/Dockerfile
	docker build . -f $< -t ghcr.io/kencx/calibre_rest:$(version)-$* --target=$*

## build: build all Docker images
build: app.build calibre.build
