import logging
import os
import threading
from django.conf import settings
from backend.amqp.AmqpsClient import AmqpsSender
from proton.reactor import Container

logger = logging.getLogger('adc')

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
        name = username.split('@')[0]
        return f"{organization_id}.{name}."

    @staticmethod
    def generateQueueName(prefix, suscriber_policy_id):
        """Generate a queue name"""
        return f"{prefix}{suscriber_policy_id}"

    @staticmethod
    def generateBrokerUsername(user_first_name, user_last_name):
        """Generate the username for the broker"""
        return f"{user_first_name}.{user_last_name}"

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
    def _manage_broker(command) -> int:
        return os.system(f"{settings.BROKER_MANAGER_SCRIPT} {settings.BROKER_MANAGER_URL} " + command)

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
        result_code = DataBrokerProxy._manage_broker(f"add-user {user_name} {password} {queue_prefix}")

        if result_code != 0:
            logger.error("Failed to create user {user_name}")

    @staticmethod
    def deleteUser(user_name):
        """
        Delete a user in the broker
         - user_name : username 
        """

        logger.info(f"Deleting user {user_name} in the broker...")
        result_code = DataBrokerProxy._manage_broker(f"remove-user {user_name}")

        if result_code != 0:
            logger.error(f"Failed to delete user {user_name}")

    @staticmethod
    def createQueue(name):
        """
        Create a queue in the broker and in the client
         - name : address of the queue
        """

        logger.info(f"Creating queue {name}...")
        result_code = DataBrokerProxy._manage_broker(f"create-queue {name}")

        if result_code != 0:
            logger.error("Failed to create queue {name}")
        else:
            # create the access to the queue in the amqps client
            DataBrokerProxy.__amqps_client.create_endpoint(name)
        
    @staticmethod
    def deleteQueue(name):
        """
        Delete a queue in the broker and in the client
         - name : address of the queue
        """

        logger.info(f"Deleting queue {name}...")
        result_code = DataBrokerProxy._manage_broker(f"delete-queue {name}")

        if result_code != 0:
            logger.error(f"Failed to delete queue {name}")
        else:
            # remove the access to the queue in the amqps client
            DataBrokerProxy.__amqps_client.remove_endpoint(name)
