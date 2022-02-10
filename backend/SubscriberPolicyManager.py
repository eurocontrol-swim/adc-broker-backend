import logging
from django.contrib.auth.models import User
from unidecode import unidecode
from .models import SUBSCRIBER_POLICY, PUBLISHER_POLICY, TRANSFORMATION_ITEM, DATA_CATALOGUE_ELEMENT, POLICY_ASSOCIATION
from backend.Policy import *
import backend.SubscriberPolicyManager as SubscriberPolicyManager
from backend.DataBrokerProxy import *

logger = logging.getLogger('adc')

def addPolicy(user_data, request_data) -> int:
    """Add a subscriber policy in the database"""

    if not DataBrokerProxy.isBrokerStarted():
        logger.error("Cannot create subscriber policy, the AMQP broker is not started")
        return 0

    policy_id = request_data['policy_id']
    transformations = request_data['transformations']
    # delivery_end_point=request_data['delivery_end_point'],
    catalogue_element = DATA_CATALOGUE_ELEMENT.objects.get(id=str(request_data['catalogue_id']))

    # create new subscriber policy
    subscriber_policy_data = SUBSCRIBER_POLICY.objects.create(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
    subscriber_policy_data.save()
    policy_id = subscriber_policy_data.id

    # Get user organization id
    organization_id = USER_INFO.objects.get(user_id=user_data.id).user_organization_id

    # Save the delivery end point
    queue_prefix = DataBrokerProxy.generateQueuePrefix(organization_id, user_data.username)
    queue_name = DataBrokerProxy.generateQueueName(queue_prefix, policy_id)
    end_point = f"{queue_name}"
    subscriber_policy = SUBSCRIBER_POLICY.objects.filter(id=policy_id).update(delivery_end_point=unidecode(end_point.lower()))

    logger.info(f"Creating subscriber policy {policy_id}")

    # Create the corresponding queue in the broker
    DataBrokerProxy.createQueue(queue_name)

    transformations_data = []

    for index, item in enumerate(transformations):
        # create new transformation items
        new_transformation_item = TRANSFORMATION_ITEM.objects.create(item_order=index, subscriber_policy_id=policy_id, json_path=item['json_path'], item_type=item['item_type'], item_operator=item['item_operator'], organization_name=item['organization_name'], organization_type=item['organization_type'])
        new_transformation_item.save()
        transformations_data.append(new_transformation_item)

    SubscriberPolicyManager.updateStaticRouting()

    return policy_id

def updatePolicy(user_data, request_data) -> int:
    """Update a subscriber policy in the database"""
    policy_id = request_data['policy_id']
    transformations = request_data['transformations']
    catalogue_element = DATA_CATALOGUE_ELEMENT.objects.get(id=str(request_data['catalogue_id']))

    subscriber_policy_data = SUBSCRIBER_POLICY.objects.filter(id=policy_id)
    subscriber_policy_data.update(user_id=user_data.id, policy_type=request_data['policy_type'], catalogue_element_id=catalogue_element.id)
    # Delete old transformations items
    transformation_item = TRANSFORMATION_ITEM.objects.filter(subscriber_policy_id = policy_id)
    transformation_item.delete()
    # Delete old associations items
    association_item = POLICY_ASSOCIATION.objects.filter(subscriber_policy_id = policy_id)
    association_item.delete()

    logger.info(f"Updating subscriber policy {policy_id}")

    transformations_data = []

    for index, item in enumerate(transformations):
        # create new transformation items
        new_transformation_item = TRANSFORMATION_ITEM.objects.create(item_order=index, subscriber_policy_id=policy_id, json_path=item['json_path'], item_type=item['item_type'], item_operator=item['item_operator'], organization_name=item['organization_name'], organization_type=item['organization_type'])
        new_transformation_item.save()
        transformations_data.append(new_transformation_item)

    SubscriberPolicyManager.updateStaticRouting()

    return policy_id

def deletePolicy(user_data, request_data) -> bool:
    """Delete a subscriber policy from the database"""

    if not DataBrokerProxy.isBrokerStarted():
        logger.error("Cannot delete subscriber policy, the AMQP broker is not started")
        return 0

    # Match policy with user
    policy_id = request_data['policy_id']
    subscriber_policy = SUBSCRIBER_POLICY.objects.get(id=policy_id, user_id=user_data.id)
    if subscriber_policy.user_id == user_data.id:
        subscriber_policy.delete()

        logger.info(f"Deleting subscriber policy {policy_id}")

        adc_user = ADCUser(user_data)

        # delete the corresponding queue in the broker
        queue_prefix = DataBrokerProxy.generateQueuePrefix(adc_user.getOrganizationId(), user_data.username)
        queue_name = DataBrokerProxy.generateQueueName(queue_prefix, policy_id)
        DataBrokerProxy.deleteQueue(queue_name)

        # when a subscriber is deleted all the publisher may have their endpoints modified so we update all the routes
        SubscriberPolicyManager.updateStaticRouting()
        return True
    else:
        return False

def getAllPolicies():
    """Get all the subscriber policies objects"""

    policies_data = SUBSCRIBER_POLICY.objects.all()
    result = []

    for policy_data in policies_data:
        result.append(SubscriberPolicy(policy_data))

    return result

def findStaticRouting(publisher_policy, subscriber_policies = None):
    """Find all the static endpoints for a publisher policy and store the result"""

    logger.info(f"Searching static routing for publisher policy: {str(publisher_policy.getId())}")

    # to find a static route we take all the endpoint available and remove the ones who doesn't match restrictions
    endpoints = []

    # the optional parameter subscriber_policies allow to avoid multiple calls to getAllPolicies
    if subscriber_policies is None:
        subscriber_policies = getAllPolicies()

    # create endpoints from the subscriber policies
    for subscriber_policy in subscriber_policies:
        endpoints.append(Endpoint(subscriber_policy))

    to_remove = []

    logger.debug("Search endpoints that doesn't match the publisher_policy topic")
    # find all the endpoints that doesn't match the publisher_policy topic
    for endpoint in endpoints:
        if not publisher_policy.checkTopicMatch(endpoint.subscriber_policy):
            to_remove.append(endpoint)

    # we remove them is a second time to avoid the modification of the list during the iteration
    for endpoint in to_remove:
        endpoints.remove(endpoint)

    to_remove.clear()
    
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

    to_remove.clear()

    # find all the endpoints who have an uncompatible restriction with the publisher_policy
    logger.debug("Search endpoints who have an uncompatible restriction with the publisher_policy")
    for endpoint in endpoints:
        logger.debug(f"Endpoint : {endpoint.subscriber_policy.getEndPointAddress()}")
        for transformation in endpoint.subscriber_policy.transformations:
            logger.debug(f"Transformation : {transformation.data.id}")
            if(transformation.isStatic() and
               not transformation.checkRestriction(publisher_policy)):
                to_remove.append(endpoint)
                break

    # we remove them is a second time to avoid the modification of the list during the iteration
    for endpoint in to_remove:
        endpoints.remove(endpoint)

    if len(endpoints) > 0:
        logger.info(f"Static endpoints found for policy {str(publisher_policy.getId())} :")

        for endpoint in endpoints:
            logger.info(f" - {str(endpoint.subscriber_policy.getId())} : {endpoint.subscriber_policy.getEndPointAddress()}")
    else:
        logger.info(f"No static endpoint found for policy {str(publisher_policy.getId())}")
    
    for endpoint in endpoints:
        p_policy = PUBLISHER_POLICY.objects.get(id=publisher_policy.getId())
        s_policy = SUBSCRIBER_POLICY.objects.get(id=endpoint.subscriber_policy.getId())
        try:
            policy_association = POLICY_ASSOCIATION.objects.get(publisher_policy=p_policy, subscriber_policy=s_policy)
            logger.info('POLICY_ASSOCIATION ALREADY EXIST')
            logger.info(policy_association)
        except POLICY_ASSOCIATION.DoesNotExist:
            static_routes = POLICY_ASSOCIATION.objects.create(publisher_policy=p_policy, subscriber_policy=s_policy)
            static_routes.save()

def removeStaticRoute(publisher_policy_id):
    """Remove a static route from POLICY_ASSOCIATION"""

    static_routes = POLICY_ASSOCIATION.objects.filter(publisher_policy_id=publisher_policy_id)
    static_routes.delete()

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

def retrieveStaticRouting(publisher_policy_id):
    """Static endpoint retrieval"""
    static_routes = POLICY_ASSOCIATION.objects.filter(publisher_policy_id=publisher_policy_id)
    endpoints = []
    for static_route in static_routes:
        subscriber_policy = getPolicyById(static_route.subscriber_policy_id)
        endpoints.append(Endpoint(subscriber_policy))

    return endpoints

def findDynamicRoutingForPublisherPolicy(publisher_policy, payload, endpoints, subscriber_policies = None):
    """Find all the dynamic endpoints for a publisher policy and store the result"""

    logger.info(f"Searching dynamic routing for publisher policy: {str(publisher_policy.getId())}")

    to_remove = []

    publisher_policy.processPayload(payload)
    
    # find all the endpoints that doesn't match the publisher_policy restrictions
    logger.debug("Search endpoints that doesn't match the publisher_policy restrictions")
    for transformation in publisher_policy.transformations:
        if not transformation.isStatic():
            for endpoint in endpoints:
                if not transformation.checkRestriction(endpoint.subscriber_policy):
                    to_remove.append(endpoint)
 
    # we remove them is a second time to avoid the modification of the list during the iteration
    for endpoint in to_remove:
        endpoints.remove(endpoint)

    to_remove.clear()

    if len(endpoints) > 0:
        logger.info(f"Dynamic endpoints found for policy {str(publisher_policy.getId())} :")

        for endpoint in endpoints:
            logger.info(f" - {str(endpoint.subscriber_policy.getId())} : {endpoint.subscriber_policy.getEndPointAddress()}")
    else:
        logger.info(f"No dynamic endpoint found for policy {str(publisher_policy.getId())}")

def findDynamicRoutingWithPayload(publisher_policy, payload, endpoint) -> bool:
    """Search endpoints who have an uncompatible restriction with the publisher_policy from Payload message"""
    logger.debug("Search dynamic endpoints who have an uncompatible restriction with the publisher_policy")
    logger.debug(f"Endpoint : {endpoint.subscriber_policy.getEndPointAddress()}")

    check_payload = endpoint.subscriber_policy.processPayload(payload)
    
    for transformation in endpoint.subscriber_policy.transformations:
        logger.debug(f"Transformation : {transformation.data.id}")
        if(not transformation.isStatic() and
            not transformation.checkRestriction(publisher_policy)):
            return False
    
    return check_payload

def getPolicyByUser(user_id):
    """Get the subscriber policy objects by User id"""
    policy = SUBSCRIBER_POLICY.objects.get(user_id=user_id)
    policy = SubscriberPolicy(policy)
    return policy

def getPolicyById(policy_id):
    """Get the subscriber policy objects by id"""
    policy = SUBSCRIBER_POLICY.objects.get(id=policy_id)
    policy = SubscriberPolicy(policy)
    return policy