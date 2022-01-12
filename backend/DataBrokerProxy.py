import logging
import os
import threading
from django.conf import settings
from backend.amqp.AmqpsClient import AmqpsSender
from proton.reactor import Container

logger = logging.getLogger('adc')

class DataBrokerProxy:
    __amqps_client = None
    __thread = None

    @staticmethod
    def startClient():
        if DataBrokerProxy.__amqps_client == None:
            logger.info("Starting AMQPS client")
            DataBrokerProxy.__amqps_client = AmqpsSender(settings.BROKER_AMQPS_URL, settings.AMQPS_TRUSTED_CA, settings.AMQPS_CLIENT_CERTIFICATE, settings.AMQPS_CLIENT_PRIVATE_KEY, settings.AMQPS_CLIENT_PASSWORD)
            container = Container(DataBrokerProxy.__amqps_client)
            DataBrokerProxy.__thread = threading.Thread(target=DataBrokerProxy._run_container, args=(container,), daemon=True)
            DataBrokerProxy.__thread.start()

    @staticmethod
    def _run_container(container):
        try:
            container.run()
        except KeyboardInterrupt:
            logger.info("Exit")

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
    def publishData(data_payload, endpoint):
        DataBrokerProxy.__amqps_client.send(data_payload, endpoint)

    @staticmethod
    def createUser(user_name, password, queue_prefix):
        logger.info(f"Creating user {user_name} in the broker...")
        result_code = os.system(f"{settings.BROKER_MANAGER_SCRIPT} add-user {user_name} {password} {queue_prefix}")

        if result_code != 0:
            logger.error("Failed to create user {user_name}")

    @staticmethod
    def deleteUser(user_name):
        logger.info(f"Deleting user {user_name} in the broker...")
        result_code = os.system(f"{settings.BROKER_MANAGER_SCRIPT} remove-user {user_name}")

        if result_code != 0:
            logger.error(f"Failed to delete user {user_name}")

    @staticmethod
    def createQueue(name):
        logger.info(f"Creating queue {name}...")
        result_code = os.system(f"{settings.BROKER_MANAGER_SCRIPT} create-queue {name}")

        if result_code != 0:
            logger.error("Failed to create queue {name}")
        else:
            # create the access to the queue in the amqps client
            DataBrokerProxy.__amqps_client.create_endpoint(name)
        
    @staticmethod
    def deleteQueue(name):
        logger.info(f"Deleting queue {name}...")
        result_code = os.system(f"{settings.BROKER_MANAGER_SCRIPT} delete-queue {name}")

        if result_code != 0:
            logger.error(f"Failed to delete queue {name}")
        else:
            # remove the access to the queue in the amqps client
            DataBrokerProxy.__amqps_client.remove_endpoint(name)
