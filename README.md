# AdcBackend
This project was generated with [DJANGO](https://www.djangoproject.com/) version 3.2.9.
Django is a high-level Python web framework.

## Install python 3
Please install [Python 3](https://www.python.org/downloads/).

## Install Django
Run `python -m pip install Django`.

## Create symlink
To link Django (backend) to Angular (builded frontend)
Run `cd /adc_backend/`
`ln -s ../adc-front/dist/adc-front/ static`

## Development server
Run `python manage.py runserver` for a dev server. Navigate to `http://127.0.0.1:8000/`. 
The app will automatically reload if you change any of the source files.

## Postgres Database
Create a docker image for Postgresql.

docker run -d \
--name adc-postgres \
-e POSTGRES_PASSWORD=postgres \
-v /data:/var/lib/postgresql/data \
-p 5432:5432 \
postgres:14.1-alpine

## Start Postgres Database
Run `docker start adc-postgres`

## Make migrations for database
Edit `/backend/models.py`.
Run `python manage.py makemigrations` to generate a new migration.
Run `python manage.py migrate` to apply migrations.

## Create certificates for TLS connections
Java is needed to get the keytool command
Run `export PATH=${PATH}:<path to JDK>/bin/`
Run `cd certificates`
Run `./createCertificates.sh`

## Build and run Artemis broker
Run `cd artemis_broker`
Run `docker build -t artemis_broker .`
Run `docker run -e AMQ_USER=admin -e AMQ_PASSWORD=admin -p5771:5771 -v '<absolute path to adc-broker-backend>/certificates/certs:/certs' --name artemis_broker artemis_broker`

