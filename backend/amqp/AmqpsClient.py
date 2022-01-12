import logging
import queue
from proton import Message, SSLDomain
from proton.handlers import MessagingHandler
import abc

logger = logging.getLogger('adc')
logging.basicConfig(level=logging.INFO)

class AmqpsClient(MessagingHandler):
    """
    Generic class for amqps connection
    The connection must be done in child classes by specializing on_started method
    """

    def __init__(self, url, trusted_ca, client_certificate, client_private_key, client_password):
        """
        Create a AmqpsClient and set the tls parameter
         url : URL of the connection (amqps://<user>:<password>@<host>:<port>/)
         trusted_ca : broker certificate with pem format
         client_certificate : client certificate with pem format
         client_private_key : client private key with pem format
         client_password : password for the client store
        """
        super(AmqpsClient, self).__init__()
        self.url = url
        self.trusted_ca = trusted_ca
        self.client_certificate = client_certificate
        self.client_private_key = client_private_key
        self.client_password = client_password

        """True if the container is started"""
        self.started = False
        """Container running this messaging handler"""
        self.container = None

    def on_start(self, event):
        """proton callback called when the container is started. It set the TSL parameters."""
        event.container.ssl.client.set_trusted_ca_db(self.trusted_ca)
        # call requests the servers certificate to be verified as valid using the specified CA's public key.
        event.container.ssl.client.set_peer_authentication(SSLDomain.VERIFY_PEER)
        event.container.ssl.client.set_credentials(self.client_certificate, 
                                                   self.client_private_key,
                                                   self.client_password)

        self.container = event.container
        self.started = True
        self.on_started(event)

    @abc.abstractmethod
    def on_started(self):
        """Need to be implemented in child classes. The purpose of this method is to create connections."""
        return

class AmqpsSender(AmqpsClient):
    """
    This class allow to send messages to multiples targets. An endpoint must be created in order to prepare a target.
    """
    def __init__(self, url, trusted_ca, client_certificate, client_private_key, client_password, auto_create_endpoints=True):
        """
        Create a AmqpsSender
         url : URL of the connection (amqps://<user>:<password>@<host>:<port>/)
         trusted_ca : broker certificate with pem format
         client_certificate : client certificate with pem format
         client_private_key : client private key with pem format
         client_password : password for the client store
         auto_create_endpoints : True if the client need to create missing endpoints on send
        """
        super().__init__(url, trusted_ca, client_certificate, client_private_key, client_password)

        """Stores messages when the client is not started. The messages will be sent when the client is ready."""
        self.__queue = queue.Queue()
        """Senders stored by queue"""
        self.__endpoints = {}
        """Stores endpoints created before the connection. These endpoints will be created when the connection is established"""
        self.__endpoints_to_create = []

        self.auto_create_endpoints = auto_create_endpoints

    def on_started(self, event):
        """create the amqps connection"""

        # we need to create the connection dicrectly instead of using create_sender
        self.connection = self.container.connect(url=self.url)

        # create all the endpoint which have been created before the start
        for address in self.__endpoints_to_create:
            self.create_endpoint(address)

        self.__endpoints_to_create.clear()

    def create_endpoint(self, address):
        """
        Create an endpoint to send messages
         address : address of the endpoint (eg. my.beautiful.queue)
         return : the sender
        """
        sender = None

        # if the client is started we create the endpoint
        if self.started:
            # we don't create the endpoint if it already exists
            if address not in self.__endpoints:
                logger.info(f"Create endpoint {self.url + address}")
                sender = self.container.create_sender(self.connection, address)
                self.__endpoints[address] = sender
            else:
                logger.info(f"The endpoint {address} already exists")

        # if the client is not started we store the address to create the endpoint at start
        else:
            self.__endpoints_to_create.append(address)

        return sender

    def remove_endpoint(self, address):
        """Remove an endpoint"""
        if self.started:
            try:
                self.__endpoints.pop(address)
            except KeyError:
                logger.warn(f"Endpoint to remove not found {address}")
        else:
            try:
                self.__endpoints_to_create.remove(address)
            except ValueError:
                logger.warn(f"Endpoint to remove not found {address}")

    def send(self, message_body, address):
        """
        Send a message to an endpoint
         message_body : content of the message
         address : address of the endpoint
        """

        # if the client is not started we postpone the sent
        if self.started:
            sender = self.__endpoints.get(address)

            # create the missing endpoint if auto_create_endpoints is True 
            if sender == None and self.auto_create_endpoints:
                sender = self.create_endpoint(address)

            if sender != None:
                logger.info(f"Send message {message_body} to {address}")
                msg = Message(body=message_body)
                sender.send(msg)
            else:
                logger.warn(f"Endpoint {address} not found")
        else:
            logger.info(f"Postponed message {message_body} to {address}")
            self.__queue.put((message_body, address))

    def on_sendable(self, event):
        """proton callback called when the client is ready to send messages"""

        # we send all the messages postponed
        while self.__queue.not_empty:
            try:
                # non blocking call to Queue.get so we can exit the method if the queue is empty (with the Empty except)
                message_body, address = self.__queue.get(False)
                self.send(message_body, address)
                self.__queue.task_done()
            except queue.Empty:
                return

class AmqpsReceiver(AmqpsClient):
    """This class allow to receive messages. The url parameter must contains url and address."""
    def on_started(self, event):
        """Create the receiver"""
        event.container.create_receiver(self.url)

    def on_message(self, event):
        """proton callback called when a message is received. Log the body of the message."""
        logger.info(f"Message received : {event.message.body}")