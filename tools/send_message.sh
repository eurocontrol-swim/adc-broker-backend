#!/bin/sh

url='http://localhost'
username=''
password=''
policy=''
message='default message'

function usage
{
    echo
    echo "Usage :"
    echo "-------"
    echo "./send_message.sh [--url <url>] --username <username> --password <password> --policy <policy id> [--message <message>]"
    echo
}

while [ -n "$1" ]
do
    if [ $1 == "--url" ]
    then
        shift
        if [ -n "$1" ]
        then
            url=$1
            shift
        else
            echo "Missing url after --url"
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
    elif [ $1 == "--policy" ]
    then
        shift
        if [ -n "$1" ]
        then
            policy=$1
            shift
        else
            echo "Missing policy id after --policy"
            usage
            exit 1
        fi
    elif [ $1 == "--message" ]
    then
        shift
        if [ -n "$1" ]
        then
            message=$1
            shift
        else
            echo "Missing message after --message"
            usage
            exit 1
        fi
    else
        echo "Unknown parameter : $1"
        usage
        exit 1
    fi
done

if [ -z "$url" ] || [ -z "$username" ] || [ -z "$password" ] || [ -z "$policy" ] || [ -z "$message" ]
then
    echo "Missing parameter"
    usage
    exit 1
fi

request_result=$(curl --no-progress-meter --location --request POST ${url}'/api/token/' --form 'username="'${username}'"' --form 'password="'${password}'"')
[ $? == 0 ] || exit 1

token=$(echo $request_result | grep -o -E '"token":".*"' | cut -f2 -d: | sed 's/"//g')

if [ -z "$token" ]
then
    echo "Failed to get token"
    exit 1
fi

curl --location --request POST ${url}'/api/publish/' --header "Authorization: Token $token" --form 'policy_id="'$policy'"' --form "message=\"$message\""
echo


