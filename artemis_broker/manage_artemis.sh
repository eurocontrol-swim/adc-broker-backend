#!/bin/sh

#broker_url="http://admin:admin@localhost:8161"

function usage
{
    echo 'usage : manage_artemis <broker_url> <action> ...'
    echo 'action :'
    echo ' - status'
    echo ' - add-user'
    echo ' - update-user-password'
    echo ' - rm-user'
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

    local request_result=$(curl --no-progress-meter -H ${header} -d "${body}" $1/console/jolokia)

    echo $request_result

    local code=$(echo "$request_result" | grep -o -E '"status":[0-9]+' | cut -f2 -d:)

    if [ "$code" == "200" ]
    then
        return 0
    else
        return 1
    fi
}

function status
{
    sendRequest ${broker_url} listBrokerConnections
    return $?
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
        return 2
    fi

    if [ -z "$password" ]
    then
        echo "Missing parameter password"
        return 2
    fi

    if [ -z "$queue_prefix" ]
    then
        echo "Missing parameter queue_prefix"
        return 2
    fi

    echo "Adding user $user..."

    sendRequest ${broker_url} addUser "\"$user\", \"$password\", \"$user\", false"
    [ $? == 0 ] || return 1

    add_consuming_permission_for_user ${user} ${queue_prefix}\#
    return $?
}

# $1 user
# $2 password
function update_user_password
{
    local user=$1
    local password=$2

    if [ -z "$user" ]
    then
        echo "Missing parameter user"
        return 2
    fi

    if [ -z "$password" ]
    then
        echo "Missing parameter password"
        return 2
    fi

    echo "Update user $user..."

    sendRequest ${broker_url} 'resetUser(java.lang.String,java.lang.String,java.lang.String)' "\"$user\", \"$password\", \"$user\""
    return $?
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
        return 2
    fi

    if [ -z "$queue_prefix" ]
    then
        echo "Missing parameter queue_prefix"
        return 2
    fi

    echo "Removing user $user..."

    sendRequest ${broker_url} removeUser "\"$user\""
    [ $? == 0 ] || return 1

    remove_consuming_permission_for_user ${user} ${queue_prefix}\#
    return $?
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
        return 2
    fi

    if [ -z "$pattern" ]
    then
        echo "Missing parameter pattern"
        return 2
    fi

    echo "Adding a consume permission for user $user..."

    # params :
    # addressMatch, send, consume, createDurableQueueRoles, deleteDurableQueueRoles, createNonDurableQueueRoles, deleteNonDurableQueueRoles, manage, browse
    sendRequest ${broker_url} 'addSecuritySettings(java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String,java.lang.String)' "\"$pattern\", \"amq\", \"$user, amq\", \"\", \"\", \"\", \"\", \"\", \"\""
    return $?
}

# $1 pattern
function remove_consuming_permission_for_user
{
    local pattern=$1

    if [ -z "$pattern" ]
    then
        echo "Missing parameter pattern"
        return 2
    fi

    echo "Removing the consume permission for pattern $pattern..."

    sendRequest ${broker_url} removeSecuritySettings "\"$pattern\""
    return $?
}

# $1 address
function create_queue
{
    local address=$1

    if [ -z "$address" ]
    then
        echo "Missing parameter address"
        return 2
    fi

    echo "Creating queue $address..."

    # params : address, name, durable, routing type
    sendRequest ${broker_url} 'createQueue(java.lang.String,java.lang.String,boolean,java.lang.String)' "\"$address\", \"$address\", true, \"ANYCAST\""
    return $?
}

# $1 address
function delete_queue
{
    local address=$1

    if [ -z "$address" ]
    then
        echo "Missing parameter address"
        return 2
    fi

    echo "Deleting queue $address..."

    # params : name, remove consumers, autoDeleteAddress
    sendRequest ${broker_url} 'destroyQueue' "\"$address\", true, true"
    return $?
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

result_code=0

case ${action} in
    status)
        status
        result_code=$?
        ;;
    add-user)
        add_user $*
        result_code=$?
        ;;
    rm-user)
        remove_user $*
        result_code=$?
        ;;
    update-user-password)
        update_user_password $*
        result_code=$?
        ;;
    create-queue)
        create_queue $*
        result_code=$?
        ;;
    delete-queue)
        delete_queue $*
        result_code=$?
        ;;
    *)
        echo "Unknown action : \"$action\""
        usage
        result_code=2
esac

exit $result_code