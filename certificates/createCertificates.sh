#!/bin/sh

# https://access.redhat.com/documentation/en-us/red_hat_amq/6.2/html/client_connectivity_guide/amqppython

if [ -n "$1" ]
then
    if [ -d $1 ]
    then
        destination_dir=$1
    else
        echo "$1 is not a directory"
        exit 1
    fi
else
    destination_dir=certs
fi

echo "Using destination dir : $destination_dir"

general_passwd=secret

echo "Generate the broker certificate"
echo

# Create public and private key for the broker and store them in broker.ks store
# And create a self signed certificate with a validity of 99999 days in the store
keytool -genkey -alias broker -keyalg RSA -keystore ${destination_dir}/broker.ks \
-storepass ${general_passwd} -dname "CN=localhost" \
-keypass ${general_passwd} -validity 99999 || exit 1

echo
echo "Generate pem trust certificate for Qpid Python client"
echo

# convert broker.ks in another format (PKCS12)
keytool -importkeystore -srckeystore ${destination_dir}/broker.ks -srcalias broker \
-srcstoretype JKS -deststoretype PKCS12 -destkeystore ${destination_dir}/broker.pkcs12 \
-srcstorepass ${general_passwd} -deststorepass ${general_passwd} || exit 1

# convert broker.pkcs12 in PEM format
openssl pkcs12 -in ${destination_dir}/broker.pkcs12 -out ${destination_dir}/broker_cert.pem \
-passin pass:${general_passwd} -passout pass:${general_passwd} || exit 1

echo
echo "Generate the client certificate"
echo

# Create public and private key for the client and store them in client.ks store
# And create a self signed certificate with a validity of 99999 days in the store
keytool -genkey -alias client -keyalg RSA -keystore ${destination_dir}/client.ks \
-storepass ${general_passwd} -keypass ${general_passwd} \
-dname "CN=localhost" -validity 99999 || exit 1

# extract the certificate from the client keystore
keytool -export -alias client -keystore ${destination_dir}/client.ks -file ${destination_dir}/client_cert \
-storepass ${general_passwd} || exit 1

echo
echo "Add client certificate as trusted to the broker database"
echo

# generate the trust store
keytool -import -alias client -keystore ${destination_dir}/broker.ts -file ${destination_dir}/client_cert \
-storepass ${general_passwd} -v -trustcacerts -noprompt || exit 1

echo
echo "Set SLL to prevent the private key and the certificate to be send to output"
echo

# convert client.ks in another format (PKCS12)
keytool -importkeystore \
-srckeystore ${destination_dir}/client.ks \
-destkeystore ${destination_dir}/client.pkcs12 \
-deststoretype PKCS12 \
-srcalias client \
-srcstorepass ${general_passwd} \
-deststorepass ${general_passwd} \
-destkeypass ${general_passwd} || exit 1

# extract the client private key
openssl pkcs12 -nocerts -in ${destination_dir}/client.pkcs12 -out ${destination_dir}/client_private_key.pem \
-passin pass:${general_passwd} -passout pass:${general_passwd} || exit 1

# extract the client certificate
openssl pkcs12 -nokeys -in ${destination_dir}/client.pkcs12 -out ${destination_dir}/client_cert.pem \
-passin pass:${general_passwd} -passout pass:${general_passwd} || exit 1

echo
echo "Certificates successfully generated"
echo


