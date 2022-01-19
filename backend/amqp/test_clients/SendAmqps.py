import os.path
import optparse
import threading
import logging
from proton.reactor import Container
from backend.amqp.AmqpsClient import *

import time

def run_container(container):
    container.run()

parser = optparse.OptionParser(usage="usage: %prog [options]",
                               description="Send messages to the supplied url and address.")

parser.add_option("-u", "--url", default="amqps://admin:admin@localhost:5771/",
                  help="url to which messages are sent (default %default)")

parser.add_option("-a", "--address", default="default",
                  help="queue or topic where the messages are sent (default %default)")

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
    sender = AmqpsSender(opts.url, trusted_ca, client_certificate, client_private_key, client_password)
    container = Container(sender)
    thread = threading.Thread(target=run_container, args=(container,), daemon=True)

    sender.create_endpoint(opts.address)

    thread.start()

    time.sleep(1)

    while True:
        sender.send('test', opts.address)
        time.sleep(1)
    
    #thread.join()
except KeyboardInterrupt:
    pass