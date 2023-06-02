DC_PATH := docker-compose.yml
HOST_API_ABS_PATH := ${PWD}

.PHONY: build
build:
	docker-compose -f $(DC_PATH) build

.PHONY:
up:
	docker-compose -f $(DC_PATH) up -d

.PHONY: stop
stop:
	docker-compose -f $(DC_PATH) stop

.PHONY:
rm:
	docker-compose -f $(DC_PATH) rm

.PHONY:
down:
	docker-compose -f $(DC_PATH) down -v

# .PHONY: lint
# check_lint:
# 	docker run --rm --name test_dasboard -v  $(HOST_API_ABS_PATH):/app python:3.7.13-slim bin/bash -c "cd /app/ && pip install flake8 && flake8 --config=.flake8 ."

.PHONY: test
test:
	docker-compose -f $(DC_PATH) exec web /bin/bash -c "python manage.py test ${ARG}"


att: ## View the att of the specified service container.
	docker attach cleancode_app

logs: ## View the logs of the specified service container.
	docker logs -f --tail=500 cleancode_app

shell: ## Run a shell on the specified service's container.
	docker-compose -f $(DC_PATH) exec web /bin/bash

restart: ## Run a shell on the specified service's container.
	docker-compose restart web