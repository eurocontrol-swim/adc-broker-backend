#!/bin/bash

cd $(dirname $0)

image_name="artemis_broker"
container_name="artemis_broker"

certificates_dir=../certificates

function build
{
    echo "Building artemis broker image..."

    if [ -d ${certificates_dir} ]
    then
        mkdir -p certs
        # we need to duplicate the certificates because the docker COPY doesn't work on targets outside the docker build context dir
        cp ../certificates/certs/broker.ks ../certificates/certs/broker.ts certs
        sudo docker build -t ${image_name} .
    else
        echo "Certificates directory \"$certificates_dir\" not found."
    fi
}

function start
{
    echo "Starting artemis broker..."
    # starting the container detached
    sudo docker run -e AMQ_USER=admin -e AMQ_PASSWORD=admin -p5771:5771 -d --name ${image_name} ${container_name}
}

function stop
{
    echo "Stoping artemis broker..."
    sudo docker stop ${container_name}
    sudo docker rm ${container_name}
}

# $1 user
# $2 password
function add_user
{
    local user=$1
    local password=$2

    if [ -z "$user" ]
    then
        echo "Missing parameter user"
        return
    fi

    if [ -z "$password" ]
    then
        echo "Missing parameter password"
        return
    fi

    echo "Adding user $user..."

    local command="./adc_broker/bin/artemis user add --user-command-user $user --user-command-password $password --role $user --user admin --password admin"
    sudo docker exec ${container_name} ${command}

    add_consuming_permission_for_user $user $user.\#
}

# $1 user
function remove_user
{
    local user=$1

    if [ -z "$user" ]
    then
        echo "Missing parameter user"
        return
    fi

    echo "Removing user $user..."

    local command="./adc_broker/bin/artemis user rm --user-command-user $user --user admin --password admin"
    sudo docker exec ${container_name} ${command}

    remove_consuming_permission_for_user $user $user.\#
}

# $1 user
# $2 pattern
function add_consuming_permission_for_user
{
    local user=$1
    local pattern=$2

    if [ -z "$user" ]
    then
        echo "Missing parameter user"
        return
    fi

    if [ -z "$pattern" ]
    then
        echo "Missing parameter pattern"
        return
    fi

    echo "Adding a consume permission for user $user..."

    # modify broker.xml to add a consume permission for the user (the broker reload it's configuration if the config file is modified)
    local line_to_add='<security-setting match="'${pattern}'"> <permission type="send" roles="amq"/> <permission type="consume" roles="'${user}', amq"/> </security-setting>'
    sudo docker exec ${container_name} sed -i "s|<security-settings>|<security-settings>\n${line_to_add}|" adc_broker/etc/broker.xml
}

# $1 user
# $2 pattern
function remove_consuming_permission_for_user
{
    local user=$1
    local pattern=$2

    if [ -z "$user" ]
    then
        echo "Missing parameter user"
        return
    fi

    if [ -z "$pattern" ]
    then
        echo "Missing parameter pattern"
        return
    fi

    echo "Removing the consume permission for user $user..."

    # modify broker.xml to remove the consume permission for the user (the broker reload it's configuration if the config file is modified)
    sudo docker exec ${container_name} sed -i '/<security-setting match="'${pattern}'">/d' adc_broker/etc/broker.xml
}

# $1 address
function create_address
{
    local address=$1

    if [ -z "$address" ]
    then
        echo "Missing parameter address"
        return
    fi

    echo "Creating address $address..."

    local command="./adc_broker/bin/artemis address create --name $address --user admin --password admin --protocol amqp --anycast --multicast"
    sudo docker exec ${container_name} ${command}
}

# $1 address
function delete_address
{
    local address=$1

    if [ -z "$address" ]
    then
        echo "Missing parameter address"
        return
    fi

    echo "Deleting address $address..."

    local command="./adc_broker/bin/artemis address delete --name $address --user admin --password admin"
    sudo docker exec ${container_name} ${command}
}

# $1 address
function create_queue
{
    local address=$1

    if [ -z "$address" ]
    then
        echo "Missing parameter address"
        return
    fi

    echo "Creating queue $address..."

    local command="./adc_broker/bin/artemis queue create --name $address --user admin --password admin --auto-create-address --preserve-on-no-consumers --durable --address $address --protocol amqp --anycast"
    sudo docker exec ${container_name} ${command}
}

# $1 address
function delete_queue
{
    local address=$1

    if [ -z "$address" ]
    then
        echo "Missing parameter address"
        return
    fi

    echo "Deleting queue $address..."

    local command="./adc_broker/bin/artemis queue delete --name $address --user admin --password admin"
    sudo docker exec ${container_name} ${command}
}

#-------------- MAIN ---------------------------

[ -n "$1" ] || exit 1

action=$1
shift

case ${action} in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    add-user)
        add_user $*
        ;;
    rm-user)
        remove_user $*
        ;;
    create-address)
        create_address $*
        ;;
    delete-address)
        delete_address $*
        ;;
    create-queue)
        create_queue $*
        ;;
    delete-queue)
        delete_queue $*
        ;;
    *)
        echo "Unknown action : \"$action\""
esac