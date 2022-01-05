import logging
from .models import SUBSCRIBER_POLICY, PUBLISHER_POLICY, TRANSFORMATION_ITEM, USER_INFO, ORGANIZATIONS
from django.contrib.auth.models import User

logger = logging.getLogger('adc')

class ADCUser:
    """User"""
    def __init__(self, user_data):
        """
        Construct the ADCUser by requesting the database
          user_data : data from the table Users
        """
        self.__data = user_data
        self.__info_data = USER_INFO.objects.get(user_id=user_data.id)
        self.__organization_data = self.__info_data.user_organization

    def getOrganizationType(self) -> str:
        """Get the organization type of the user"""
        return self.__organization_data.type

    def getOrganizationName(self) -> str:
        """Get the organization name of the user"""
        return self.__organization_data.name

    def getOrganizationId(self) -> int:
        """Get the organization id of the user"""
        return self.__organization_data.id

class Endpoint:
    """Endpoint of a message"""
    def __init__(self, subscriber_policy):
        """
        Construct the Endpoint
          subscriber_policy : SubscriberPolicy data
        """
        self.subscriber_policy = subscriber_policy

class RoutingObject:
    """Contains all the data needed to find endpoints for a message and the payload"""
    def __init__(self, publisher_policy, data_payload, endpoints) -> None:
        """
        Construct a Routing object
          publisher_policy : PublisherPolicy used to publish the message
          data_payload : the payload of the message
          endpoints : list of endpoints for the message. This list will be reduced to keep only the matching endpoint.
        """
        self.publisher_policy = publisher_policy
        self.data_payload = data_payload
        self.endpoints = endpoints

class TransformationItem:
    """Represent a transformation that can be applied to a data payload or a restriction to find endpoints for a message"""
    def __init__(self, transformation_data):
        """
        Construct the TransformationItem
          transformation_data : data from table TRANSFORMATION_ITEM
        """
        self.data = transformation_data

    def isStatic(self) -> bool:
        """Return true if the transformation can be applied staticaly"""
        return self.data.item_type == 'organization_type' or self.data.item_type == 'organization_name'

    def checkRestriction(self, policy) -> bool:
        """
        Return true if a restriction match a policy
          policy : Policy object to check
        """
        if self.data.item_type == "organization_type":
            logger.debug(f"organization_type : {self.data.organization_type} == {policy.user.getOrganizationType()}")
            return self.data.organization_type == policy.user.getOrganizationType()
        elif self.data.item_type == "organization_name":
            logger.debug(f"organization_name : {self.data.organization_name}, {policy.user.getOrganizationName()}")
            return self.data.organization_name == policy.user.getOrganizationName()
        elif self.data.item_type == "data_based":
            logger.warn(f"Unhandled case : {self.data.item_type}")
        else:
            logger.warn(f"Unhandled case : {self.data.item_type}")

        return False

    def doesItMatchValue(routing_object):
        # TODO
        pass

class Policy:
    """Generic class to represent a policy"""
    def __init__(self, policy_data, transformations_data, user_data = None) -> None:
        """
        Construct a Policy by requesting the database if some optional parameters are missing
          policy_data : data from the PUBLISHER_POLICY or SUBSCRIBER_POLICY table
          transformations_data : list of data from the TRANSFORMATION_ITEM table
          user_data (optional) : data from the Users table
        """
        self._policy_data = policy_data

        self.transformations = []
        for transformation_data in transformations_data:
            self.transformations.append(TransformationItem(transformation_data))

        if user_data is None:
            user_data = User.objects.get(id=policy_data.user_id)

        self.user = ADCUser(user_data)

    def getId(self) -> int:
        return self._policy_data.id

    def checkRestriction(self, transformation_item) -> bool:
        """Return true if the policy match a restriction"""
        return transformation_item.checkRestriction(self)

class PublisherPolicy(Policy):
    """Publisher policy"""
    def __init__(self, policy_data, transformations_data=None, user_data=None) -> None:
        """Call the constructor of Policy"""
        if transformations_data is None:
            transformations_data = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id = policy_data.id)

        super().__init__(policy_data, transformations_data, user_data)

    @staticmethod
    def createById(id):
        """
        Create a PublisherPolicy by requesting the database with an id
          id : id of the policy
          result : If the policy exists return a PublisherPolicy object else return None
        """
        try:
            policy_data =  PUBLISHER_POLICY.objects.get(id=id)
            transformations_data = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id=id)
            return Policy(policy_data, transformations_data)
        except PUBLISHER_POLICY.DoesNotExist:
            return None

class SubscriberPolicy(Policy):
    """Subscriber policy"""
    def __init__(self, policy_data, transformations_data=None, user_data=None) -> None:
        """Call the constructor of Policy"""
        if transformations_data is None:
            transformations_data = TRANSFORMATION_ITEM.objects.filter(subscriber_policy_id = policy_data.id)

        super().__init__(policy_data, transformations_data, user_data)

    @staticmethod
    def createById(id):
        """
        Create a SubscriberPolicy by requesting the database with an id
          id : id of the policy
          result : If the policy exists return a SubscriberPolicy object else return None
        """
        try:
            policy_data =  SUBSCRIBER_POLICY.objects.get(id=id)
            transformations_data = TRANSFORMATION_ITEM.objects.filter(subscriber_policy_id=id)
            return Policy(policy_data, transformations_data)
        except SUBSCRIBER_POLICY.DoesNotExist:
            return None

    def getEndPointAddress(self) -> str:
        """Return the address of the subscriber endpoint"""
        return self._policy_data.delivery_end_point
