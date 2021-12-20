import logging
import os
from adc_backend.settings import BROKER_MANAGER_SCRIPT

logger = logging.getLogger('adc')

def publishData(data_payload, endpoint):
    pass # TODO

def createUser(user_name, password):
    logger.info("Creating user {user_name} in the broker...")
    result_code = os.system("{BROKER_MANAGER_SCRIPT} add-user {user_name} {password}")

    if result_code != 0:
        logger.error("Failed to create user {user_name}")

def deleteUser(user_name):
    logger.info("Deleting user {user_name} in the broker...")
    result_code = os.system("{BROKER_MANAGER_SCRIPT} remove-user {user_name}")

    if result_code != 0:
        logger.error("Failed to delete user {user_name}")

def createQueue(address):
    logger.info("Creating queue {address} in the broker...")
    result_code = os.system("{BROKER_MANAGER_SCRIPT} create-queue {address}")

    if result_code != 0:
        logger.error("Failed to create queue {address}")

def deleteQueue(address):
    logger.info("Deleting queue {address} in the broker...")
    result_code = os.system("{BROKER_MANAGER_SCRIPT} delete-queue {address}")

    if result_code != 0:
        logger.error("Failed to delete queue {address}")
