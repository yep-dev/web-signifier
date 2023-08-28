up:
	docker-compose up --build

makemigrations:
	docker-compose run django python manage.py makemigrations && find . -path "./signifier/*/migrations/*.py" -exec sed -i '/# Generated by Django/{N; s/# Generated by Django.*\n//;}' {} +

migrate:
	docker-compose run django python manage.py migrate

reset_migrations:
	find . -path "*/migrations/*.py" -not -name "__init__.py" -not -path "./signifier/contrib/*" -delete && make makemigrations

reset_data:
	docker-compose stop postgres && docker-compose rm -f postgres && docker volume remove signifier_signifier_local_postgres_data && make migrate

reset:
	make reset_migrations && make reset_data

schema:
	docker-compose run django python manage.py spectacular --file schema.yml --validate

lint:
	black . && autoflake  --remove-all-unused-imports --in-place -r  .