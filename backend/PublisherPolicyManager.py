import logging
from .models import PUBLISHER_POLICY, TRANSFORMATION_ITEM, DATA_CATALOGUE_ELEMENT
import backend.SubscriberPolicyManager as SubscriberPolicyManager
from backend.Policy import *

logger = logging.getLogger('adc')

def addPolicy(user_data, request_data) -> int:
    """Add or update a publisher policy in the database"""

    policy_id = request_data['policy_id']
    transformations = request_data['transformations']
    catalogue_element = DATA_CATALOGUE_ELEMENT.objects.get(id=str(request_data['catalogue_id']))

    publisher_policy = PUBLISHER_POLICY.objects.get(id=policy_id)
    publisher_policy.__dict__.update(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
    transformation_item = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id = policy_id)
    transformation_item.delete()

    logger.info("Updating publisher policy %s" % policy_id)

    for index, item in enumerate(transformations):
        # create new transformation items
        new_transformation_item = TRANSFORMATION_ITEM.objects.create(item_order=index, publisher_policy_id=policy_id, json_path=item['json_path'], item_type=item['item_type'], item_operator=item['item_operator'], organization_name=item['organization_name'], organization_type=item['organization_type'])
        new_transformation_item.save()

    return policy_id

def updatePolicy(user_data, request_data) -> int:
    """Update a publisher policy in the database"""
    policy_id = request_data['policy_id']
    transformations = request_data['transformations']
    catalogue_element = DATA_CATALOGUE_ELEMENT.objects.get(id=str(request_data['catalogue_id']))

    publisher_policy = PUBLISHER_POLICY.objects.get(id=policy_id)
    publisher_policy.__dict__.update(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
    transformation_item = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id = policy_id)
    transformation_item.delete()

    logger.info("Updating publisher policy %s" % policy_id)

    for index, item in enumerate(transformations):
        # create new transformation items
        new_transformation_item = TRANSFORMATION_ITEM.objects.create(item_order=index, publisher_policy_id=policy_id, json_path=item['json_path'], item_type=item['item_type'], item_operator=item['item_operator'], organization_name=item['organization_name'], organization_type=item['organization_type'])
        new_transformation_item.save()

    # TODO try to build the policy with the database datas instead of re-requesting with the id
    SubscriberPolicyManager.findStaticRouting(PublisherPolicy.createById(policy_id))

    return policy_id

def deletePolicy(user_data, request_data):
    """Delete a publisher policy from the database"""
    policy_id = request_data['policy_id']
    # Match policy with user
    publisher_policy = PUBLISHER_POLICY.objects.get(id=policy_id, user_id=user_data.id)
    publisher_policy.delete()

    SubscriberPolicyManager.removeStaticRoute(policy_id)

    logger.info("Deleting publisher policy %s" % policy_id)