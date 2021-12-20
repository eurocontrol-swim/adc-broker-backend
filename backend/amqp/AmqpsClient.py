import logging
import random
from proton import Message, SSLDomain
from proton.handlers import MessagingHandler
import abc

logger = logging.getLogger('adc')
logging.basicConfig(level=logging.INFO)

class AmqpsClient(MessagingHandler):
    def __init__(self, url, trusted_ca, client_certificate, client_private_key, client_password):
        super(AmqpsClient, self).__init__()
        self.url = url
        self.trusted_ca = trusted_ca
        self.client_certificate = client_certificate
        self.client_private_key = client_private_key
        self.client_password = client_password

    def on_start(self, event):
        print("Starting...")
        event.container.ssl.client.set_trusted_ca_db(self.trusted_ca)
        # call requests the servers certificate to be verified as valid using the specified CA's public key. 
        event.container.ssl.client.set_peer_authentication(SSLDomain.VERIFY_PEER)
        event.container.ssl.client.set_credentials(self.client_certificate, 
                                                   self.client_private_key,
                                                   self.client_password)
        print("Started")
        self.on_started(event)

    @abc.abstractmethod
    def on_started(self):
        return

class AmqpsSender(AmqpsClient):
    def on_started(self, event):
        print("Create sender")
        event.container.create_sender(self.url)

    def on_sendable(self, event):
        print("Send message")
        if event.sender.credit:
            id = random.randrange(10000000)
            msg = Message(id=id, body={'sequence':(id)})
            event.sender.send(msg)

    def on_accepted(self, event):
        print("Accepted")
        event.connection.close()

class AmqpsReceiver(AmqpsClient):
    def on_started(self, event):
        event.container.create_receiver(self.url)

    def on_message(self, event):
        print("Message received")