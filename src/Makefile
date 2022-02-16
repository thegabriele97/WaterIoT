.PHONY: all build up down closeall create_service exec_shell genreq

all: up

down:
	docker-compose down

up: genreq 
	docker-compose up -d --build
	docker image prune -f

build: genreq
	docker-compose build
	docker image prune -f

closeall:
	docker-compose rm -f

exec_shell:
	docker exec -it $(CONT) bash

genreq:
	@pip3 install pipreqs
	@for a in $$(ls); do \
        if [ -d $$a ]; then \
            $(MAKE) -C $$a genreq; \
        fi; \
    done;

create_service:
	@cp -rnv ../utils/example services/$(NAME)
	@sed -i 's/services\/example/services\/$(NAME)/g' services/$(NAME)/Dockerfile  
	@cat ../utils/docker-compose.yml  | sed 's/services:/\n\n/' | sed 's/services\/example/services\/$(NAME)/' | sed 's/example:/$(NAME):/' >> docker-compose.yml

