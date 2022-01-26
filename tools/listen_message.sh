#!/bin/sh

cd $(dirname $0)
cd ..

host='localhost'
username=''
password=''
queue=''

function usage
{
    echo
    echo "Usage :"
    echo "-------"
    echo "./listen_message.sh [--host <host>] --username <username> --password <password> --queue <queue>"
    echo
}

while [ -n "$1" ]
do
    if [ $1 == "--host" ]
    then
        shift
        if [ -n "$1" ]
        then
            host=$1
            shift
        else
            echo "Missing host after --host"
            usage
            exit 1
        fi
    elif [ $1 == "--username" ]
    then
        shift
        if [ -n "$1" ]
        then
            username=$1
            shift
        else
            echo "Missing username after --user"
            usage
            exit 1
        fi
    elif [ $1 == "--password" ]
    then
        shift
        if [ -n "$1" ]
        then
            password=$1
            shift
        else
            echo "Missing password after --password"
            usage
            exit 1
        fi
    elif [ $1 == "--queue" ]
    then
        shift
        if [ -n "$1" ]
        then
            queue=$1
            shift
        else
            echo "Missing queue after --queue"
            usage
            exit 1
        fi
    else
        echo "Unknown parameter : $1"
        usage
        exit 1
    fi
done

if [ -z "$host" ] || [ -z "$username" ] || [ -z "$password" ] || [ -z "$queue" ]
then
    echo "Missing parameter"
    usage
    exit 1
fi

export PYTHONPATH=$(pwd)

cd backend/amqp/test_clients

python3 ReceiveAmqps.py -u amqps://${username}:${password}@${host}:5771/ -a ${queue}