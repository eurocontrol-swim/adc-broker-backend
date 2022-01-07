import logging
import os
from adc_backend.settings import BROKER_MANAGER_SCRIPT

logger = logging.getLogger('adc')

def generateQueuePrefix(organization_id, user_first_name, user_last_name):
    """Generate the first part of queue name"""
    return f"{organization_id}.{user_first_name}.{user_last_name}."

def generateQueueName(prefix, suscriber_policy_id):
    """Generate a queue name"""
    return f"{prefix}{suscriber_policy_id}"

def generateBrokerUsername(user_first_name, user_last_name):
    """Generate the username for the broker"""
    return f"{user_first_name}.{user_last_name}"

def publishData(data_payload, endpoint):
    pass # TODO

def createUser(user_name, password, queue_prefix):
    logger.info(f"Creating user {user_name} in the broker...")
    result_code = os.system(f"{BROKER_MANAGER_SCRIPT} add-user {user_name} {password} {queue_prefix}")

    if result_code != 0:
        logger.error("Failed to create user {user_name}")

def deleteUser(user_name):
    logger.info(f"Deleting user {user_name} in the broker...")
    result_code = os.system(f"{BROKER_MANAGER_SCRIPT} remove-user {user_name}")

    if result_code != 0:
        logger.error(f"Failed to delete user {user_name}")

def createQueue(name):
    logger.info(f"Creating queue {name} in the broker...")
    result_code = os.system(f"{BROKER_MANAGER_SCRIPT} create-queue {name}")

    if result_code != 0:
        logger.error("Failed to create queue {name}")

def deleteQueue(name):
    logger.info(f"Deleting queue {name} in the broker...")
    result_code = os.system(f"{BROKER_MANAGER_SCRIPT} delete-queue {name}")

    if result_code != 0:
        logger.error(f"Failed to delete queue {name}")
