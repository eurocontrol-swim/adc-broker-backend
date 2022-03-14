#!/bin/sh

echo "Waiting for PostgreSQL..."

while ! nc -z ${DATABASE_HOST} 5432
do
    sleep 0.1
done

echo "PostgreSQL started"

python3 manage.py flush --no-input
python3 manage.py migrate

echo "Creating users..."

# TODO Check if the user admin@mail.com already exists. If it does don't erase it 
# create users
python3 manage.py loaddata fixtures/base_data.json

# Define variables from env or localhost
if [ -z "$AMQP_BROKER_HOST" ];
then
AMQP_BROKER_HOST=localhost
fi

if [ -z "$AMQP_BROKER_ADMIN" ];
then
AMQP_BROKER_ADMIN=localhost
fi

if [ -z "$AMQP_BROKER_ADMIN_PASSWORD" ];
then
AMQP_BROKER_ADMIN_PASSWORD=localhost
fi

url='http://'$AMQP_BROKER_ADMIN':'$AMQP_BROKER_ADMIN_PASSWORD'@'$AMQP_BROKER_HOST':8161'

echo $url

# Break before Broker init
sleep 15

# Create consumer on the broker
./artemis_broker/manage_artemis.sh $url add-user consumer@swimlake.com consumer 2.consumer@swimlake.com

if [ $? = 0 ]
then
echo "Consumer created"
else
echo "Consumer doesn't created"
fi

exec "$@"
