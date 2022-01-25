#!/bin/sh

#broker_url="http://admin:admin@localhost:8161"

function usage
{
    echo 'usage : manage_artemis <broker_url> <action> ...'
    echo 'action :'
    echo ' - add-user'
    echo ' - rm-user'
    echo ' - create-address'
    echo ' - delete-address'
    echo ' - create-queue'
    echo ' - delete-queue'
}

function sendRequest
# $1 url
# $2 operation
# $3 operations
{
    body='{
        "type": "exec",
        "mbean": "org.apache.activemq.artemis:broker=\"0.0.0.0\"",
        "operation":"'$2'"
        "arguments":['$3']
    }'

    header='Content-Type:application/json'

    curl -H ${header} -d "${body}" $1/console/jolokia
    echo
}

# $1 user
# $2 password
# $3 queue prefix
function add_user
{
    local user=$1
    local password=$2
    local queue_prefix=$3

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

    if [ -z "$queue_prefix" ]
    then
        echo "Missing parameter queue_prefix"
        return
    fi

    echo "Adding user $user..."

    sendRequest ${broker_url} addUser "\"$user\", \"$password\", \"$user\", false"

    add_consuming_permission_for_user ${user} ${queue_prefix}\#
}

# $1 user
# $2 queue prefix
function remove_user
{
    local user=$1
    local queue_prefix=$2

    if [ -z "$user" ]
    then
        echo "Missing parameter user"
        return
    fi

    if [ -z "$queue_prefix" ]
    then
        echo "Missing parameter queue_prefix"
        return
    fi

    echo "Removing user $user..."

    sendRequest ${broker_url} removeUser "\"$user\""

    remove_consuming_permission_for_user ${user} ${queue_prefix}\#
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

    # params :
    # addressMatch, send, consume, createDurableQueueRoles, deleteDurableQueueRoles, createNonDurableQueueRoles, deleteNonDurableQueueRoles, manage, browse
    sendRequest ${broker_url} 'addSecuritySettings(java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String)' "\"$pattern\", \"amq\", \"$user, amq\", \"\", \"\", \"\", \"\", \"\", \"\""
}

# $1 pattern
function remove_consuming_permission_for_user
{
    local pattern=$1

    if [ -z "$pattern" ]
    then
        echo "Missing parameter pattern"
        return
    fi

    echo "Removing the consume permission for pattern $pattern..."

    sendRequest ${broker_url} removeSecuritySettings "\"$pattern\""
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

    # params : address, name, durable, routing type
    sendRequest ${broker_url} 'createQueue(java.lang.String,java.lang.String,boolean,java.lang.String)' "\"$address\", \"$address\", true, \"MULTICAST\""
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

    # params : name, remove consumers, autoDeleteAddress
    sendRequest ${broker_url} 'destroyQueue' "\"$address\", true, true"
}

#-------------- MAIN ---------------------------

if [ -z "$1" ] || [ -z "$2" ]
then
    usage
    exit
fi

broker_url=$1
action=$2
shift
shift

case ${action} in
    add-user)
        add_user $*
        ;;
    rm-user)
        remove_user $*
        ;;
    create-queue)
        create_queue $*
        ;;
    delete-queue)
        delete_queue $*
        ;;
    *)
        echo "Unknown action : \"$action\""
        usage
esac