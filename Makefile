.PHONY: config-check build up down logs status init verify
config-check:
	docker compose config --quiet
build:
	docker compose build
up:
	docker compose up -d
down:
	docker compose down
logs:
	docker compose logs --tail=100
status:
	docker compose ps
init:
	docker compose run --rm app python manage.py migrate
	docker compose run --rm app python manage.py seed_demo
verify:
	docker compose exec app python manage.py check
	docker compose exec app python manage.py test sketches catalog
