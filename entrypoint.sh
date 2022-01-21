#!/bin/sh

echo "Waiting for PostgreSQL..."

while ! nc -z ${DATABASE_HOST} 5432
do
    sleep 0.1
done

echo "PostgreSQL started"

python3 manage.py flush --no-input
python3 manage.py migrate

exec "$@"