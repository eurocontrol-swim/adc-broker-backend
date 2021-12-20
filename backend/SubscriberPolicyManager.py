import logging
from django.contrib.auth.models import User
from unidecode import unidecode
from .models import SUBSCRIBER_POLICY, PUBLISHER_POLICY, TRANSFORMATION_ITEM, DATA_CATALOGUE_ELEMENT
from adc_backend.settings import BROKER_AMQP_URL
from backend.Policy import *
import backend.SubscriberPolicyManager as SubscriberPolicyManager

logger = logging.getLogger('adc')
_static_routes = {}

def addPolicy(user_data, request_data):
    """Add or update a subscriber policy in the database"""
    policy_id = request_data['policy_id']
    transformations = request_data['transformations']
    # delivery_end_point=request_data['delivery_end_point'],
    catalogue_element = DATA_CATALOGUE_ELEMENT.objects.get(id=str(request_data['catalogue_id']))

    # Try if subscriber policy exist for update
    try:
        subscriber_policy_data = SUBSCRIBER_POLICY.objects.get(id=policy_id)
        subscriber_policy_data.__dict__.update(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
        transformation_item = TRANSFORMATION_ITEM.objects.filter(subscriber_policy_id = policy_id)
        transformation_item.delete()

        logger.info("Updating subscriber policy %s" % policy_id)

    except SUBSCRIBER_POLICY.DoesNotExist:
        # create new subscriber policy
        subscriber_policy_data = SUBSCRIBER_POLICY.objects.create(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
        subscriber_policy_data.save()
        policy_id = subscriber_policy_data.id

        # Get user organization id
        organization_id = USER_INFO.objects.get(user_id=user_data.id).user_organization_id

        # Save the delivery end point
        end_point = f"{BROKER_AMQP_URL}{organization_id}.{user_data.first_name}.{user_data.last_name}.{policy_id}"
        subscriber_policy = SUBSCRIBER_POLICY.objects.filter(id=policy_id).update(delivery_end_point=unidecode(end_point.lower()))

        logger.info("Creating subscriber policy %s" % policy_id)

    transformations_data = []

    for index, item in enumerate(transformations):
        # create new transformation items
        new_transformation_item = TRANSFORMATION_ITEM.objects.create(item_order=index, subscriber_policy_id=policy_id, json_path=item['json_path'], item_type=item['item_type'], item_operator=item['item_operator'], organization_name=item['organization_name'], organization_type=item['organization_type'])
        new_transformation_item.save()
        transformations_data.append(new_transformation_item)

    SubscriberPolicyManager.updateStaticRouting()

def deletePolicy(user_data, request_data) -> None:
    """Delete a subscriber policy from the database"""
    # Match policy with user
    policy_id = request_data['policy_id']
    subscriber_policy = SUBSCRIBER_POLICY.objects.get(id=policy_id, user_id=user_data.id)
    subscriber_policy.delete()

    logger.info("Deleting subscriber policy %s" % policy_id)

    # when a subscriber is deleted all the publisher may have their endpoints modified so we update all the routes
    SubscriberPolicyManager.updateStaticRouting()

def getAllPolicies():
    """Get all the subscriber policies objects"""

    policies_data = SUBSCRIBER_POLICY.objects.all()
    result = []

    for policy_data in policies_data:
        result.append(SubscriberPolicy(policy_data))

    return result

def findStaticRouting(publisher_policy, subscriber_policies = None):
    """Find all the static endpoints for a publisher policy and store the result"""

    logger.info("Searching static routing for policy %s" % str(publisher_policy.getId()))

    # to find a static route we take all the endpoint available and remove the ones who doesn't match restrictions
    endpoints = []

    # the optional parameter subscriber_policies allow to avoid multiple calls to getAllPolicies
    if subscriber_policies is None:
        subscriber_policies = getAllPolicies()

    # create endpoints from the subscriber policies
    for subscriber_policy in subscriber_policies:
        endpoints.append(Endpoint(subscriber_policy))

    to_remove = []

    # find all the endpoints that doesn't match the publisher_policy restrictions
    logger.debug("Search endpoints that doesn't match the publisher_policy restrictions")
    for transformation in publisher_policy.transformations:
        if(transformation.isStatic()):
            for endpoint in endpoints:
                if not transformation.checkRestriction(endpoint.subscriber_policy):
                    to_remove.append(endpoint)

    # we remove them is a second time to avoid the modification of the list during the iteration
    for endpoint in to_remove:
        endpoints.remove(endpoint)

    to_remove = []

    # find all the endpoints who have an uncompatible restriction with the publisher_policy
    logger.debug("Search endpoints who have an uncompatible restriction with the publisher_policy")
    for endpoint in endpoints:
        logger.debug("Endpoint : %s" % endpoint.subscriber_policy.getEndPointAddress())
        for transformation in endpoint.subscriber_policy.transformations:
            logger.debug("Transformation : %s" % transformation.data.id)
            if(transformation.isStatic() and
               not transformation.checkRestriction(publisher_policy)):
                to_remove.append(endpoint)
                break

    # we remove them is a second time to avoid the modification of the list during the iteration
    for endpoint in to_remove:
        endpoints.remove(endpoint)

    if len(endpoints) > 0:
        logger.info("Static endpoints found for policy %s :" % str(publisher_policy.getId()))

        for endpoint in endpoints:
            logger.info(" - %s : %s" % (str(endpoint.subscriber_policy.getId()), endpoint.subscriber_policy.getEndPointAddress()))
    else:
        logger.info("No static endpoint found for policy %s" % str(publisher_policy.getId()))
    
    _static_routes[publisher_policy.getId()] = endpoints

def removeStaticRoute(publisher_policy_id):
    """Remove a static route"""

    if publisher_policy_id in _static_routes:
        _static_routes.pop(publisher_policy_id)

def updateStaticRouting():
    """Update the routes for all the publishers"""

    logger.info("Updating static routing...")

    publisher_policies_data = PUBLISHER_POLICY.objects.all()
    subscriber_policies = getAllPolicies()

    # find the static route for all of the publisher policies
    for publisher_policy_data in publisher_policies_data:
        user_data = User.objects.get(id=publisher_policy_data.user_id)
        transformations_data = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id = publisher_policy_data.id)

        policy = PublisherPolicy(publisher_policy_data, transformations_data, user_data)

        findStaticRouting(policy, subscriber_policies)

