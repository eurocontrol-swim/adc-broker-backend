import logging
from django.db import connection
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
# from rest_framework.schemas import AutoSchema
from django.shortcuts import render
# from django.views.generic import TemplateView
from .models import USER_INFO, ORGANIZATIONS, DATA_CATALOGUE_ELEMENT, PUBLISHER_POLICY, SUBSCRIBER_POLICY, TRANSFORMATION_ITEM
from django.contrib.auth.models import User
from unidecode import unidecode

import backend.PublisherPolicyManager as PublisherPolicyManager
import backend.SubscriberPolicyManager as SubscriberPolicyManager
import backend.CatalogueManager as CatalogueManager
import backend.UserManager as UserManager
from backend.DataBrokerProxy import *
from backend.views_user import getUser
from backend.Policy import *

logger = logging.getLogger('adc')

# Error codes
# HTTP_200_OK
# HTTP_400_BAD_REQUEST
# HTTP_401_UNAUTHORIZED
# HTTP_404_NOT_FOUND
# HTTP_405_METHOD_NOT_ALLOWED
# HTTP_500_INTERNAL_SERVER_ERROR


def index(request, path = ''):
    """View function for home page of site"""
    index = "index.html"
    context = {}
    if request.user.is_authenticated:
        user = getUser(request.user.id)
        context={'user': user}
    return render(request, index, context)

@api_view(['POST'])
@ensure_csrf_cookie
def postDataCatalogue(request):
    """View function for create or update data catalogue element"""
    if request.method == "POST":
        try:
            # Math user authorization if role is 'administrator'
            user_data = User.objects.get(email=request.data['user_email'])
            if UserManager.checkUserRole(user_data.id, 'administrator'):
                try:
                    # Check if data element already exist
                    data_element = DATA_CATALOGUE_ELEMENT.objects.get(id=request.data['id'])
                    CatalogueManager.updateCatalogueElement(request.data)
                    return JsonResponse({'message':'Data updated'})
                except DATA_CATALOGUE_ELEMENT.DoesNotExist:
                    CatalogueManager.addCatalogueElement(request.data)
                    return JsonResponse({'message':'Data saved'})
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user does not have the ADMINISTRATOR role')
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='The user does not exist')
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not POST')

@api_view(['GET'])
@ensure_csrf_cookie
def getDataCatalogue(request):
    """View function to get all data catalogue elements"""
    if request.method == "GET":
        policy_type = request.GET.get('policy_type', '')
        user_email = request.GET.get('email', '')
        try:
            # Math user authorization if role is 'administrator'
            user_data = User.objects.get(email=user_email)
            # TODO - Check user role ??
            # if UserManager.checkUserRole(user_data.id, 'administrator'):
            if policy_type != '':
                # Filter Data Catalogue Element if data_type contains 'type' or 'data' string
                data_catalogue = DATA_CATALOGUE_ELEMENT.objects.filter(data_type__contains=policy_type.split('_')[0]).values()
            else:
                # Get all data catalogue elements from database
                data_catalogue = CatalogueManager.getCatalogueElementList()
            return JsonResponse({'data':list(data_catalogue)})
            # else:
            #     return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user does not have the ADMINISTRATOR role')
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='The user does not exist')
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

@api_view(['DELETE'])
@ensure_csrf_cookie
def deleteDataElement(request):
    """View function to delete user and informations"""
    if request.method == "DELETE":
        try:
            # Math user authorization if role is 'administrator'
            user_data = User.objects.get(email=request.data['user_email'])
            if UserManager.checkUserRole(user_data.id, 'administrator'):
                try:
                    data = DATA_CATALOGUE_ELEMENT.objects.get(id=request.data['data_id'])
                    data.delete()
                    return JsonResponse({'message':'The data element is deleted'})

                except DATA_CATALOGUE_ELEMENT.DoesNotExist:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data='Data element does not exist')
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user does not have the ADMINISTRATOR role')
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='The user does not exist')
        
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not DELETE')
    
@api_view(['POST'])
@ensure_csrf_cookie
def postPublisherPolicy(request):
    """View function for create or update Publisher Policy"""
    if request.method == "POST":
        # try if user not exist by email
        try:
            user_data = User.objects.get(email=request.data['user_email'])
            try:
                # Check if user manages only its own policies
                publisher_policy = PUBLISHER_POLICY.objects.get(id=request.data['policy_id'])
                if publisher_policy.user_id == user_data.id:
                    policy_id = PublisherPolicyManager.updatePolicy(user_data, request.data)
                    SubscriberPolicyManager.findStaticRouting(PublisherPolicy.createById(policy_id))
                    response = {'message':'Publisher policy updated'}
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user is not authorized')

            except PUBLISHER_POLICY.DoesNotExist:
                policy_id = PublisherPolicyManager.addPolicy(user_data, request.data)
                if policy_id != 0:
                    SubscriberPolicyManager.findStaticRouting(PublisherPolicy.createById(policy_id))
                    response = {'message':'Publisher policy created'}
                else:
                    response = {'message':'Failed to create the publisher policy'}
            
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='The user does not exist')

        return JsonResponse(response)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not POST')

@api_view(['GET'])
@ensure_csrf_cookie
def getPublisherPolicy(request):
    """View function to get all data catalogue elements"""
    if request.method == "GET":
        # try if user exist by email
        try:
            user = User.objects.get(email=request.GET.get('user_mail', ''))
            publisher_policies_list = []
            # Check if user manages only its own policies
            # Get all data catalogue elements from database that match with the user
            publisher_policies = PUBLISHER_POLICY.objects.filter(user_id = user.id).values()
            for policy in publisher_policies:
                catalogue = DATA_CATALOGUE_ELEMENT.objects.filter(id=policy['catalogue_element_id']).values()

                if TRANSFORMATION_ITEM.objects.filter(publisher_policy_id=policy['id']):
                    transformation = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id=policy['id']).values('item_order', 'item_operator', 'item_type', 'json_path', 'organization_type', 'organization_name')
                else:
                    transformation = {}
                # Clean dictionnaries
                policy.pop('user_id', None)
                policy.pop('catalogue_element_id', None)
                # Create a list with dictionaries
                publisher_policies_list.append({'policy':policy, 'catalogue':list(catalogue), 'transformations':list(transformation)})
            
            response = {'policies':publisher_policies_list}
        except User.DoesNotExist:
            response = {'message':'User does not exist'}
        
        return JsonResponse(response)

    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

@api_view(['DELETE'])
@ensure_csrf_cookie
def deletePublisherPolicy(request):
    """View function to delete publisher policy and transformations"""
    if request.method == "DELETE":
        try:
            user = User.objects.get(email=request.data['user_email'])
            try:
                # Check if user manages only its own policies
                if PublisherPolicyManager.deletePolicy(user, request.data):
                    return JsonResponse({'message':'The publisher policy is deleted'})
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user is not authorized')

            except PUBLISHER_POLICY.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST, data='Publisher policy does not exist')

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='User does not exist')
        
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not DELETE')

@api_view(['GET'])
@ensure_csrf_cookie
def getOrganizationsName(request):
    """View function to get all orgnizations name"""
    if request.method == "GET":
        # try if user exist by email
        try:
            organizations_name = ORGANIZATIONS.objects.values_list('name', flat=True).distinct()
            response = {'organizations_name':list(organizations_name)}

        except ORGANIZATIONS.DoesNotExist:
            response = {'message':'No organizations name found'}
        
        return JsonResponse(response)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

@api_view(['GET'])
@ensure_csrf_cookie
def getOrganizationsType(request):
    """View function to get all orgnizations type"""
    if request.method == "GET":
        # try if user exist by email
        try:
            organizations_type = ORGANIZATIONS.objects.values_list('type', flat=True).distinct()
            response = {'organizations_type':list(organizations_type)}

        except ORGANIZATIONS.DoesNotExist:
            response = {'message':'No organizations type found'}
        
        return JsonResponse(response)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

@api_view(['POST'])
@ensure_csrf_cookie
def postSubscriberPolicy(request):
    """View function for create or update data catalogue element"""
    if request.method == "POST":
        # try if user not exist by email
        try:
            user_data = User.objects.get(email=request.data['user_email'])

            try:
                subscriber_policy = SUBSCRIBER_POLICY.objects.get(id=request.data['policy_id'])
                if subscriber_policy.user_id == user_data.id:
                    policy_id = SubscriberPolicyManager.updatePolicy(user_data, request.data)
                    response = {'message':'Subscriber policy updated'}
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user is not authorized')

            except SUBSCRIBER_POLICY.DoesNotExist:
                policy_id = SubscriberPolicyManager.addPolicy(user_data, request.data)
                response = {'message':'Subscriber policy created'}
            
        except User.DoesNotExist:
            response = {'message':'User does not exist'}

        return JsonResponse(response)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not POST')

@api_view(['GET'])
@ensure_csrf_cookie
def getSubscriberPolicy(request):
    """View function to get all data catalogue elements"""
    if request.method == "GET":
        # try if user exist by email
        try:
            user = User.objects.get(email=request.GET.get('user_mail', ''))
            subscriber_policies_list = []
            # Check if user manages only its own policies
            # Get all data catalogue elements from database that match with the user
            subscriber_policies = SUBSCRIBER_POLICY.objects.filter(user_id = user.id).values()
            for policy in subscriber_policies:
                catalogue = DATA_CATALOGUE_ELEMENT.objects.filter(id=policy['catalogue_element_id']).values()

                if TRANSFORMATION_ITEM.objects.filter(subscriber_policy_id=policy['id']):
                    transformation = TRANSFORMATION_ITEM.objects.filter(subscriber_policy_id=policy['id']).values('item_order', 'item_operator', 'item_type', 'json_path', 'organization_type', 'organization_name')
                else:
                    transformation = {}
                # Clean dictionnaries
                policy.pop('user_id', None)
                policy.pop('catalogue_element_id', None)
                # Create a list with dictionaries
                subscriber_policies_list.append({'policy':policy, 'catalogue':list(catalogue), 'transformations':list(transformation)})
            
            response = {'policies':subscriber_policies_list}

        except User.DoesNotExist:
            response = {'message':'User does not exist'}
        
        return JsonResponse(response)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

@api_view(['DELETE'])
@ensure_csrf_cookie
def deleteSubscriberPolicy(request):
    """View function to delete publisher policy and transformations"""
    if request.method == "DELETE":
        try:
            user = User.objects.get(email=request.data['user_email'])
            try:
                # Check if user manages only its own policies
                if SubscriberPolicyManager.deletePolicy(user, request.data):
                    return JsonResponse({'message':'The subscriber policy is deleted'})
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user is not authorized')

            except SUBSCRIBER_POLICY.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST, data='Subscriber policy does not exist')

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='User does not exist')
        
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not DELETE')

@api_view(['POST'])
# @ensure_csrf_cookie
# User authentication required
# If the user is not authenticated, return error 401
@permission_classes([IsAuthenticated])
def publishMessage(request):
    if request.method == "POST":
        try:
            # TODO We need to update the static routes at the start of the application
            # SubscriberPolicyManager.updateStaticRouting()
            
            # Check if the user who sent this request have access to the policy
            user_id = request.user.id
            policy_id = int(request.data['policy_id'])
            user_policies = PublisherPolicyManager.getPolicyByUser(user_id)

            if len(user_policies) > 0:
                for policy in user_policies:
                    if policy['id'] == policy_id:
                        # If payload is a FILE
                        if request.FILES.get('message'):
                            # Decode this file to string
                            message_body = request.FILES.get('message').read()
                        else:
                            message_body = request.data['message']

                        payload = Payload(message_body)
                        # Static routing
                        endpoints = SubscriberPolicyManager.retrieveStaticRouting(policy_id)

                        # Dynamic routing
                        SubscriberPolicyManager.findDynamicRoutingForPublisherPolicy(PublisherPolicy.createById(policy_id), payload, endpoints)

                        if endpoints and endpoints != None:
                            for endpoint in endpoints:
                                if len(endpoint.subscriber_orgname_filtering) > 0:     
                                    copy_payload = Payload(endpoint.subscriber_orgname_filtering)
                                elif len(endpoint.subscriber_orgtype_filtering) > 0:     
                                    copy_payload = Payload(endpoint.subscriber_orgtype_filtering)
                                else:    
                                    copy_payload = Payload(payload.body)
                                if SubscriberPolicyManager.findDynamicRoutingWithPayload(PublisherPolicy.createById(policy_id), copy_payload, endpoint):                                    
                                    # Publish data with payload
                                    DataBrokerProxy.publishData(copy_payload.body, endpoint.subscriber_policy.getEndPointAddress())
                            return Response('Your message is published')
                        else:
                            logger.info(f"No endpoint found for policy {policy_id}.")
                            response= Response(status=status.HTTP_404_NOT_FOUND, data=f'The Publisher Policy {policy_id} does not generate any routing for the message')
                    else:
                        response= Response(status=status.HTTP_401_UNAUTHORIZED, data='You are not allowed to publish here')

                return response
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=f'The Publisher has no policies available')
            
        except any:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=f'The Publisher policy {policy_id} does not exist')
        
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not POST')

class TestView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        content = {'message': 'This is a test from GET!'}
        return Response(content)

@api_view(['POST'])
# If the user is not authenticated, return error 401
@permission_classes([IsAuthenticated])
def Test(request):
    content = {'message': 'This is a test from POST!'}
    logger.info(request.user.id)
    return Response(content)
