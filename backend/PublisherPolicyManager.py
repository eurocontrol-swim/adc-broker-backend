import logging
from .models import PUBLISHER_POLICY, TRANSFORMATION_ITEM, DATA_CATALOGUE_ELEMENT, POLICY_ASSOCIATION
import backend.SubscriberPolicyManager as SubscriberPolicyManager
from backend.Policy import *

logger = logging.getLogger('adc')

def addPolicy(user_data, request_data) -> int:
    """Add a publisher policy in the database"""

    transformations = request_data['transformations']
    catalogue_element = DATA_CATALOGUE_ELEMENT.objects.get(id=str(request_data['catalogue_id']))

    publisher_policy = PUBLISHER_POLICY.objects.create(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
    publisher_policy.save()

    policy_id = publisher_policy.id

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

    publisher_policy = PUBLISHER_POLICY.objects.filter(id=policy_id)
    publisher_policy.update(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
    # Delete old transformations items
    transformation_item = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id = policy_id)
    transformation_item.delete()
    # Delete old associations items
    association_item = POLICY_ASSOCIATION.objects.filter(publisher_policy_id = policy_id)
    association_item.delete()

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

def getPolicyByUser(user_id):
    """Get publisher policies id by User id"""
    policies = PUBLISHER_POLICY.objects.filter(user_id=user_id).values('id')
    return policies

def getPolicyById(policy_id):
    """Get publisher policy by id"""
    policy = PUBLISHER_POLICY.objects.get(id=policy_id)
    return policy

def getAllPolicy():
    """Get all publisher policy"""
    policies = PUBLISHER_POLICY.objects.all()
    return policies