#!/bin/sh

echo "Waiting for PostgreSQL..."

while ! nc -z ${DATABASE_HOST} 5432
do
    sleep 0.1
done

echo "PostgreSQL started"

python3 manage.py flush --no-input
python3 manage.py migrate

echo "Creating admin user..."

# TODO Check if the user admin@mail.com already exists. If it does don't erase it 
# create user admin
python3 manage.py loaddata fixtures/base_data.json

exec "$@"