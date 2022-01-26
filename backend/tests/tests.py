import os
from django.test import TestCase, override_settings
from django.conf import settings
from backend.models import *
from backend.Policy import *
from backend.DataBrokerProxy import *
import backend.PublisherPolicyManager as PublisherPolicyManager
import backend.SubscriberPolicyManager as SubscriberPolicyManager

# use the stubbed manage_artemis to avoid modifying the broker conf
@override_settings(BROKER_MANAGER_SCRIPT=os.path.join(settings.BASE_DIR, 'backend', 'tests', 'manage_artemis_stub.sh'))
class BackendTestCase(TestCase):
    """General backend testing"""

    def setUp(self):
        """Populate the database with users, organizations, catalogue elements and policies"""

        # organization Airport oprator
        new_organization = ORGANIZATIONS.objects.create(name='easyJet', type='airline')
        new_organization.save()
        organization_id1 = new_organization.id

        # organization Airspace user
        new_organization = ORGANIZATIONS.objects.create(name='orga2', type='Airspace user')
        new_organization.save()
        organization_id2 = new_organization.id

        # Create Users

        # publisher 1
        new_first_publisher = User.objects.create(username="publisher.1@mail.com", first_name="publisher", last_name="1", email="publisher.1@mail.com")
        new_first_publisher.set_password("password")
        new_first_publisher.save()

        new_user_info = USER_INFO.objects.create(user_id = new_first_publisher.id, user_role="publisher", user_organization_id=organization_id1)
        new_user_info.save()

        # publisher 2
        new_publisher = User.objects.create(username="publisher.2@mail.com", first_name="publisher", last_name="2", email="publisher.2@mail.com")
        new_publisher.set_password("password")
        new_publisher.save()

        new_user_info = USER_INFO.objects.create(user_id = new_publisher.id, user_role="publisher", user_organization_id=organization_id2)
        new_user_info.save()

        # subscriber 1
        new_first_subscriber = User.objects.create(username="subscriber.1@mail.com", first_name="subscriber", last_name="1", email="subscriber.1@mail.com")
        new_first_subscriber.set_password("password")
        new_first_subscriber.save()

        new_user_info = USER_INFO.objects.create(user_id = new_first_subscriber.id, user_role="subscriber", user_organization_id=organization_id1)
        new_user_info.save()

        # subscriber 2
        new_subscriber = User.objects.create(username="subscriber.2@mail.com", first_name="subscriber", last_name="1", email="subscriber.2@mail.com")
        new_subscriber.set_password("password")
        new_subscriber.save()

        new_user_info = USER_INFO.objects.create(user_id = new_subscriber.id, user_role="subscriber", user_organization_id=organization_id2)
        new_user_info.save()
        
        # create catalogue elements
        new_data_element1 = DATA_CATALOGUE_ELEMENT.objects.create(data_type='topic_element', data_path='all.topic1', data_schema='')
        new_data_element1.save()
        new_data_element2 = DATA_CATALOGUE_ELEMENT.objects.create(data_type='topic_element', data_path='all.topic2', data_schema='')
        new_data_element2.save()
        new_data_element3 = DATA_CATALOGUE_ELEMENT.objects.create(data_type='data_element', data_path='all.data1', data_schema='')
        new_data_element3.save()
        new_data_element4 = DATA_CATALOGUE_ELEMENT.objects.create(data_type='data_element', data_path='all.data2', data_schema='')
        new_data_element4.save()

Test the static route and the policies management

    def test_static_routing(self):
        """
        General test of the static routing and policy management.
        It tests :
            subscriber policy add/delete
            publisher policy add/delete
            topics
            static restrictions (single/multiples)
        """

        publisher = User.objects.get(username='publisher.1@mail.com')
        subscriber = User.objects.get(username='subscriber.1@mail.com')

        # create publisher policy
        transformations = []
        # match with organization type : Airport operator
        transformations.append({'json_path':'', 'item_type':'organization_type', 'item_operator':'organization_type_endpoint_restriction', 'organization_name':'', 'organization_type':'Airport operator'})

        policy_data = {}
        policy_data['policy_id'] = '0' # 0 to force creation
        policy_data['transformations'] = transformations
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic1').id
        policy_data['policy_type'] = 'topic_based'
        
        publisher_policy_id1 = PublisherPolicyManager.addPolicy(publisher, policy_data)
       
        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 0)

        # create subscriber policy
        transformations.clear()
        transformations.append({'json_path':'', 'item_type':'organization_name', 'item_operator':'organization_type_endpoint_restriction', 'organization_name':'orga1', 'organization_type':''})
        policy_data['transformations'] = transformations

        subscriber_policy_id1 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # add a new policy whitch doesn't match because of the different topic
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic2').id

        subscriber_policy_id2 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # add a new publisher which match the second subscriber with the same topic
        publisher_policy_id2 = PublisherPolicyManager.addPolicy(publisher, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        # add a subscriber policy with multiples restrictions that match
        transformations.clear()
        transformations.append({'json_path':'', 'item_type':'organization_name', 'item_operator':'organization_name_endpoint_restriction', 'organization_name':'orga1', 'organization_type':''})
        transformations.append({'json_path':'', 'item_type':'organization_type', 'item_operator':'organization_type_endpoint_restriction', 'organization_name':'', 'organization_type':'Airport operator'})
        policy_data['transformations'] = transformations
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic1').id

        subscriber_policy_id3 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 2)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)
        self.assertEqual(endpoints[1].subscriber_policy.getId(), subscriber_policy_id3)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        # add a publisher policy with multiples restrictions that match
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic2').id

        publisher_policy_id3 = PublisherPolicyManager.addPolicy(publisher, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 2)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)
        self.assertEqual(endpoints[1].subscriber_policy.getId(), subscriber_policy_id3)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id3)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        # add a subscriber policy with multiples restrictions that doesn't match
        transformations.clear()
        transformations.append({'json_path':'', 'item_type':'organization_name', 'item_operator':'organization_name_endpoint_restriction', 'organization_name':'orga2', 'organization_type':''})
        transformations.append({'json_path':'', 'item_type':'organization_type', 'item_operator':'organization_type_endpoint_restriction', 'organization_name':'', 'organization_type':'Airport operator'})
        policy_data['transformations'] = transformations
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic1').id

        subscriber_policy_id4 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 2)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)
        self.assertEqual(endpoints[1].subscriber_policy.getId(), subscriber_policy_id3)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id3)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        # add a publisher policy with multiples restrictions that doesn't match
        publisher_policy_id4 = PublisherPolicyManager.addPolicy(publisher, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 2)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)
        self.assertEqual(endpoints[1].subscriber_policy.getId(), subscriber_policy_id3)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id3)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id4)
        self.assertEqual(len(endpoints), 0)


    def test_topic_only(self):
        """Test of the topics without restrictions in the static routing"""

        publisher = User.objects.get(username='publisher.1@mail.com')
        publisher2 = User.objects.get(username='publisher.2@mail.com')
        subscriber = User.objects.get(username='subscriber.1@mail.com')
        subscriber2 = User.objects.get(username='subscriber.2@mail.com')

        # create publisher policy
        policy_data = {}
        policy_data['policy_id'] = '0' # 0 to force creation
        policy_data['transformations'] = []
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic1').id
        policy_data['policy_type'] = 'topic_based'

        publisher_policy_id1 = PublisherPolicyManager.addPolicy(publisher, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 0)

        # create non matching subscriber policy
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic2').id
        subscriber_policy_id1 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 0)

        # create matching subscriber policy
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic1').id
        subscriber_policy_id2 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        # create a new match with another user
        subscriber_policy_id3 = SubscriberPolicyManager.addPolicy(subscriber2, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 2)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)
        self.assertEqual(endpoints[1].subscriber_policy.getId(), subscriber_policy_id3)

        # create a new publisher matching policy
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic2').id
        publisher_policy_id2 = PublisherPolicyManager.addPolicy(publisher2, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 2)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)
        self.assertEqual(endpoints[1].subscriber_policy.getId(), subscriber_policy_id3)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # delete a policy
        delete_data = {'policy_id':subscriber_policy_id3}

        SubscriberPolicyManager.deletePolicy(subscriber2, delete_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # delete another
        delete_data = {'policy_id':subscriber_policy_id2}

        SubscriberPolicyManager.deletePolicy(subscriber, delete_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 0)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # delete a publisher
        delete_data = {'policy_id':publisher_policy_id2}
        
        PublisherPolicyManager.deletePolicy(publisher2, delete_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 0)
        
        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)
        self.assertTrue(endpoints is None)

        # delete the last subscriber
        delete_data = {'policy_id':subscriber_policy_id1}

        SubscriberPolicyManager.deletePolicy(subscriber, delete_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 0)

    def test_mixing_with_dynamic_elements(self):
        """Tests if the static routings algorithm ignores the dynamic elements"""

        publisher = User.objects.get(username='publisher.1@mail.com')
        subscriber = User.objects.get(username='subscriber.1@mail.com')

        # create publisher policy
        transformations = []
        # match with organization type : Airport operator
        transformations.append({'json_path':'', 'item_type':'organization_type', 'item_operator':'organization_type_endpoint_restriction', 'organization_name':'', 'organization_type':'Airport operator'})
        transformations.append({'json_path':'dummy', 'item_type':'data_based', 'item_operator':'organization_name_endpoint_restriction', 'organization_name':'', 'organization_type':''})
        transformations.append({'json_path':'dummy', 'item_type':'data_based', 'item_operator':'payload_extraction', 'organization_name':'', 'organization_type':''})

        policy_data = {}
        policy_data['policy_id'] = '0' # 0 to force creation
        policy_data['transformations'] = transformations
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.topic1').id
        policy_data['policy_type'] = 'topic_based'
        
        publisher_policy_id1 = PublisherPolicyManager.addPolicy(publisher, policy_data)
        
        # create subscriber policy
        subscriber_policy_id1 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)

        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # create data based subscriber policy
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.data1').id
        policy_data['policy_type'] = 'data_structure_based'

        subscriber_policy_id2 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)

        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # create data based publisher policy
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.data2').id

        publisher_policy_id2 = PublisherPolicyManager.addPolicy(publisher, policy_data)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)

        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id2)

        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id2)

    def test_payload_extraction(self):
        """
        General test of the payload extraction.
        It tests :
            subscriber policy add
            publisher policy add
            if no topics
            static restrictions (single/multiples)
            dynamic restrictions (single/multiples)
            publishData with extracted data
        """

        publisher = User.objects.get(username='publisher.1@mail.com')
        subscriber = User.objects.get(username='subscriber.1@mail.com')

        transformations = []
        policy_data = {}

        # Create a Subscriber policy
        # Extract payload to match with JsonPath, Only for easyJet company
        transformations.append({'json_path':'$.FlightLeg[?(@.LegIdentifier.Airline=="easyJet")]', 'item_type':'data_based', 'item_operator':'payload_extraction', 'organization_name':None, 'organization_type':None})
        
        policy_data['policy_id'] = '0' # 0 to force creation
        policy_data['transformations'] = transformations
        policy_data['catalogue_id'] = DATA_CATALOGUE_ELEMENT.objects.get(data_path='all.data1').id
        policy_data['policy_type'] = 'data_structure_based'

        subscriber_policy_id1 = SubscriberPolicyManager.addPolicy(subscriber, policy_data)

        # Reset transformations
        transformations.clear()

        # Create Publisher policy
        # match with organization type : airline
        transformations.append({'json_path':None, 'item_type':'organization_type', 'item_operator':'organization_type_endpoint_restriction', 'organization_name':None, 'organization_type':'airline'})
        policy_data['transformations'] = transformations

        publisher_policy_id1 = PublisherPolicyManager.addPolicy(publisher, policy_data)

        # Get Static Endpoints
        endpoints = SubscriberPolicyManager.retrieveStaticRouting(publisher_policy_id1)
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].subscriber_policy.getId(), subscriber_policy_id1)

        # Publish message with Json Payload
        message_body = '{"@TimeStamp": "2014-07-09T14:39:34","@Target": "Test","FlightLeg":[{"LegIdentifier": { "Airline": "easyJet", "FlightNumber": "8998", "OperationalSuffix": "A", "DepartureAirport": "LGW", "ArrivalAirport": "ALC","OriginDate": "2014-07-09"}}]}'
        payload = Payload(message_body)
        
        # Apply dynamic routing with json payload
        SubscriberPolicyManager.findDynamicRoutingForPublisherPolicy(PublisherPolicy.createById(publisher_policy_id1), payload, endpoints)

        if endpoints and endpoints != None:
            for endpoint in endpoints:
                logger.info('ORIGINAL:')
                logger.info(payload.body)
                copy_payload = Payload(payload.body)
                if SubscriberPolicyManager.findDynamicRoutingWithPayload(PublisherPolicy.createById(publisher_policy_id1), copy_payload, endpoint):
                    logger.info('EXTRACT PAYLOAD:')
                    logger.info(copy_payload.body)
                    DataBrokerProxy.publishData(copy_payload.body, endpoint.subscriber_policy.getEndPointAddress())