from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

class ORGANIZATIONS(models.Model):
    name = models.CharField(max_length=255)
    airport_operator = 'Airport operator'
    airspace_user = 'Airspace user'
    ground_handler = 'Ground handler'
    network_manager = 'Network manager'
    meteorological_service_provider = 'Meteorological service provider'
    TYPES = (
        (airport_operator, _('Airport operator')),
        (airspace_user, _('Airspace user')),
        (ground_handler, _('Ground handler')),
        (network_manager, _('Network manager')),
        (meteorological_service_provider, _('Meteorological service provider')),
    )
    type = models.CharField(_('type'), default=airport_operator, choices=TYPES, max_length=255)

class USER_INFO(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_organization = models.ForeignKey(ORGANIZATIONS, on_delete=models.CASCADE)
    
    admin = 'Administrator'
    publisher = 'Publisher'
    subscriber = 'Subscriber'
    ROLES = (
        (admin, _('Administrator')),
        (publisher, _('Publisher')),
        (subscriber, _('Subscriber')),
    )
    user_role = models.CharField(_('user_role'), default=subscriber, choices=ROLES, max_length=255)

class DATA_CATALOGUE_ELEMENT(models.Model):
    data_path = models.CharField(max_length=500)
    data_schema = models.CharField(max_length=500)
    topic_element = 'TOPIC ELEMENT'
    data_element = 'DATA ELEMENT'
    DATA_TYPES = (
        (topic_element, _('topic_element')),
        (data_element, _('data_element')),
    )
    data_type = models.CharField(_('data_type'), default=topic_element, choices=DATA_TYPES, max_length=255)

class PUBLISHER_POLICY(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    topic_based = 'TOPIC BASED'
    data_structure_based = 'DATA STRUCTURE BASED'
    POLICY_TYPES = (
        (topic_based, _('topic_based')),
        (data_structure_based, _('data_structure_based')),
    )
    policy_type = models.CharField(_('policy_type'), default=topic_based, choices=POLICY_TYPES, max_length=255)
    catalogue_element = models.ForeignKey(DATA_CATALOGUE_ELEMENT, on_delete=models.CASCADE)

class SUBSCRIBER_POLICY(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    policy = models.ForeignKey(PUBLISHER_POLICY, on_delete=models.CASCADE)
    delivery_end_point = models.CharField(max_length=255)
    catalogue_element = models.ForeignKey(DATA_CATALOGUE_ELEMENT, on_delete=models.CASCADE)

class TRANSFORMATION_ITEM(models.Model):
    policy = models.ForeignKey(PUBLISHER_POLICY, on_delete=models.CASCADE)
    organization = models.ForeignKey(ORGANIZATIONS, on_delete=models.CASCADE)
    data_schema = models.CharField(max_length=500)
    data_path = models.CharField(max_length=500)

    organization_type = 'Organization type'
    organization_name = 'Organization name'
    data_based = 'Data based'
    ITEM_TYPES = (
        (organization_type, _('organization_type')),
        (organization_name, _('organization_name')),
        (data_based, _('data_based')),
    )
    item_type = models.CharField(_('item_type'), default=organization_type, choices=ITEM_TYPES, max_length=255)

    endpoint_restriction = 'Endpoint restriction'
    payload_extraction = 'Payload extraction'
    ITEM_OPERATORS = (
        (endpoint_restriction, _('endpoint_restriction')),
        (payload_extraction, _('payload_extraction')),
    )
    item_operator = models.CharField(_('item_operator'), default=endpoint_restriction, choices=ITEM_OPERATORS, max_length=255)


class TOPIC_POLICY_ITEM(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    publisher_policy = models.ForeignKey(PUBLISHER_POLICY, on_delete=models.CASCADE)
    subscriber_policy = models.ForeignKey(SUBSCRIBER_POLICY, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    path = models.CharField(max_length=500)

class DATA_ELEMENT_POLICY_ITEM(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    publisher_policy = models.ForeignKey(PUBLISHER_POLICY, on_delete=models.CASCADE)
    subscriber_policy = models.ForeignKey(SUBSCRIBER_POLICY, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    path = models.CharField(max_length=500)