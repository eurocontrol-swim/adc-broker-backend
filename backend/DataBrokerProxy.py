import logging
import os
import threading
from django.conf import settings
from backend.amqp.AmqpsClient import AmqpsSender
from proton.reactor import Container

logger = logging.getLogger('adc')

class BrokerRequestError(Exception):
    """"Raised when a broker manager script call return an error"""
    pass


class DataBrokerProxy:
    """Allow to administrate and to connect to the broker"""

    """Amqp client"""
    __amqps_client = None
    """Thread to run the client on background"""
    __thread = None

    @staticmethod
    def startClient():
        """Start the amqp client"""
        
        if DataBrokerProxy.__amqps_client == None:
            logger.info("Starting AMQPS client")
            DataBrokerProxy.__amqps_client = AmqpsSender(settings.BROKER_AMQPS_URL, settings.AMQPS_TRUSTED_CA, settings.AMQPS_CLIENT_CERTIFICATE, settings.AMQPS_CLIENT_PRIVATE_KEY, settings.AMQPS_CLIENT_PASSWORD)
            container = Container(DataBrokerProxy.__amqps_client)
            DataBrokerProxy.__thread = threading.Thread(target=DataBrokerProxy._run_container, args=(container,), daemon=True)
            DataBrokerProxy.__thread.start()

    @staticmethod
    def _run_container(container):
        """Method used by the thread of the amqp client"""
        try:
            container.run()
        except KeyboardInterrupt:
            pass

    @staticmethod
    def generateQueuePrefix(organization_id, username):
        """Generate the first part of queue name"""
        name = DataBrokerProxy.generateBrokerUsername(username)
        return f"{organization_id}.{name}."

    @staticmethod
    def generateQueueName(prefix, suscriber_policy_id):
        """Generate a queue name"""
        return f"{prefix}{suscriber_policy_id}"

    @staticmethod
    def generateBrokerUsername(username):
        """Generate the username for the broker from the website username"""
        return username

    @staticmethod
    def publishData(data_payload, address):
        """
        Publish data on the broker
         - data_payload : body of the message
         - address address of the queue/topic
        """
        DataBrokerProxy.__amqps_client.send(data_payload, address)
        # TODO get a result to know if the message is succesfully sent or not

    @staticmethod
    def _manage_broker(command):
        """"
        Execute a given command with the broker manager script
         - command : the command to execute and the parameters
        """
        success = os.system(f"{settings.BROKER_MANAGER_SCRIPT} {settings.BROKER_MANAGER_URL} " + command) == 0

        if not success:
            logger.error(f"Command {command} failed")
            raise BrokerRequestError

    @staticmethod
    def isBrokerStarted() -> bool:
        """
        Check if the broker is started
         - return : True if the broker is started
        """
        try:
            DataBrokerProxy._manage_broker("status")
        except BrokerRequestError:
            return False

        return True

    @staticmethod
    def createUser(user_name, password, queue_prefix):
        """
        Create a user in the broker
         - user_name : username 
         - password : password
         - queue_prefix : queue prefix used to allow the user access. 
           The user will be allowed to consume messages to any queue starting with this string.
        """

        logger.info(f"Creating user {user_name} in the broker...")
        DataBrokerProxy._manage_broker(f"add-user {user_name} {password} {queue_prefix}")

    @staticmethod
    def updateUserPassword(user_name, password) -> bool:
        """
        Update the password of an user in the broker
         - user_name : username 
         - password : password
        """

        logger.info(f"Updating password of user {user_name} in the broker...")
        DataBrokerProxy._manage_broker(f"update-user-password {user_name} {password}")

    @staticmethod
    def deleteUser(user_name, queue_prefix) -> bool:
        """
        Delete a user in the broker
         - user_name : username
         - queue_prefix : queue prefix used to remove the user access. 
        """

        logger.info(f"Deleting user {user_name} in the broker...")
        DataBrokerProxy._manage_broker(f"rm-user {user_name} {queue_prefix}")

    @staticmethod
    def createQueue(name):
        """
        Create a queue in the broker and in the client
         - name : address of the queue
        """

        logger.info(f"Creating queue {name}...")
        DataBrokerProxy._manage_broker(f"create-queue {name}")

        # create the access to the queue in the amqps client
        DataBrokerProxy.__amqps_client.create_endpoint(name)

    @staticmethod
    def deleteQueue(name):
        """
        Delete a queue in the broker and in the client
         - name : address of the queue
        """

        logger.info(f"Deleting queue {name}...")
        DataBrokerProxy._manage_broker(f"delete-queue {name}")

        # remove the access to the queue in the amqps client
        DataBrokerProxy.__amqps_client.remove_endpoint(name)
