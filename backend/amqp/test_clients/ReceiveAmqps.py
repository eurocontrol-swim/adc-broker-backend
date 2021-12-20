import os.path
import optparse
from proton.reactor import Container
from backend.amqp.AmqpsClient import *

parser = optparse.OptionParser(usage="usage: %prog [options]",
                               description="Send messages to the supplied address.")

parser.add_option("-a", "--address", default="amqps://admin:admin@localhost:5771/default",
                  help="address to which messages are received (default %default)")

parser.add_option("-c", "--certificates", default="../../../certificates/certs/",
                  help="directory containing the SSL certificates (default %default)")

opts, args = parser.parse_args()

trusted_ca = opts.certificates + "broker_cert.pem"
client_certificate = opts.certificates + "client_cert.pem"
client_private_key = opts.certificates + "client_private_key.pem"
client_password = "secret"

if(not os.path.isfile(trusted_ca) or 
   not os.path.isfile(client_certificate) or
   not os.path.isfile(client_private_key)):
   print("File doesn't exist")
   exit()

try:
    Container(AmqpsReceiver(opts.address, trusted_ca, client_certificate, client_private_key, client_password)).run()
except KeyboardInterrupt:
    pass