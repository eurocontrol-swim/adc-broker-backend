import logging
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view
# from rest_framework.schemas import AutoSchema
from django.shortcuts import render
# from django.views.generic import TemplateView
from .models import USER_INFO, ORGANIZATIONS, DATA_CATALOGUE_ELEMENT, PUBLISHER_POLICY, SUBSCRIBER_POLICY, TRANSFORMATION_ITEM
from django.contrib.auth.models import User
from adc_backend.settings import BROKER_AMQP_URL
from unidecode import unidecode

import backend.PublisherPolicyManager as PublisherPolicyManager
import backend.SubscriberPolicyManager as SubscriberPolicyManager
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
    template_name = "index.html"
    context = {}
    return render(request, template_name,context=context)

@api_view(['POST'])
@ensure_csrf_cookie
def postDataCatalogue(request):
    """View function for create or update data catalogue element"""
    if request.method == "POST":
        logger.info('***postDataCatalogue***')
        logger.info(request.data['type'])
        # create new data catalogue element
        new_data_element = DATA_CATALOGUE_ELEMENT.objects.create(data_type=request.data['type'], data_path=request.data['path'], data_schema=request.data['schema'])
        new_data_element.save()
        return JsonResponse({'message':'data saved'})
    else:
        logger.info('Request method is not POST')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@ensure_csrf_cookie
def getDataCatalogue(request):
    """View function to get all data catalogue elements"""
    if request.method == "GET":
        policy_type = request.GET.get('policy_type', '')
        if policy_type != '':
            # Filter Data Catalogue Element if data_type contains 'type' or 'data' string
            data_catalogue = DATA_CATALOGUE_ELEMENT.objects.filter(data_type__contains=policy_type.split('_')[0]).values()
        else:
            # Get all data catalogue elements from database
            data_catalogue = DATA_CATALOGUE_ELEMENT.objects.values()
        return JsonResponse({'data':list(data_catalogue)})
    else:
        logger.info('Request method is not GET')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
@ensure_csrf_cookie
def deleteDataElement(request):
    """View function to delete user and informations"""
    if request.method == "DELETE":
        logger.info(request.data)
        # TODO - Math user authorization if role is 'administrator'
        # try:
        #     user = User.objects.get(email=request.data['user_email'], role='administration')
        try:
            data = DATA_CATALOGUE_ELEMENT.objects.get(id=request.data['data_id'])
            data.delete()
            return JsonResponse({'message':'The data element is deleted'})

        except DATA_CATALOGUE_ELEMENT.DoesNotExist:
            logger.info('Data element does not exist')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # except User.DoesNotExist:
        #     logger.info('User does not exist are wrong access')
        #     return Response(status=status.HTTP_400_BAD_REQUEST)
        
    else:
        logger.info('Request method is not DELETE')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
@api_view(['POST'])
@ensure_csrf_cookie
def postPublisherPolicy(request):
    """View function for create or update data catalogue element"""
    if request.method == "POST":
        # try if user not exist by email
        try:
            user_data = User.objects.get(email=request.data['user_email'])

            policy_id = PublisherPolicyManager.addPolicy(user_data, request.data)
            SubscriberPolicyManager.findStaticRouting(PublisherPolicy.createById(policy_id))

            response = {'message':'Publisher policy saved'}
        except User.DoesNotExist:
            response = {'message':'User does not exist'}

        return JsonResponse(response)
    else:
        logger.info('Request method is not POST')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@ensure_csrf_cookie
def getPublisherPolicy(request):
    """View function to get all data catalogue elements"""
    if request.method == "GET":
        # try if user exist by email
        try:
            user = User.objects.get(email=request.GET.get('user_mail', ''))
            publisher_policies_list = []
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
        logger.info('Request method is not GET')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
@ensure_csrf_cookie
def deletePublisherPolicy(request):
    """View function to delete publisher policy and transformations"""
    if request.method == "DELETE":
        logger.info(request.data)
        try:
            user = User.objects.get(email=request.data['user_email'])
            try:
                PublisherPolicyManager.deletePolicy(user, request.data)
                SubscriberPolicyManager.removeStaticRoute(request.data['policy_id'])

                return JsonResponse({'message':'The publisher policy is deleted'})

            except PUBLISHER_POLICY.DoesNotExist:
                logger.info('Publisher policy does not exist')
                return Response(status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            logger.info('User does not exist')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
    else:
        logger.info('Request method is not DELETE')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
        logger.info('Request method is not GET')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
        logger.info('Request method is not GET')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@ensure_csrf_cookie
def postSubscriberPolicy(request):
    """View function for create or update data catalogue element"""
    if request.method == "POST":
        # try if user not exist by email
        try:
            user_data = User.objects.get(email=request.data['user_email'])

            SubscriberPolicyManager.addPolicy(user_data, request.data)

            response = {'message':'Subscriber policy saved'}

        except User.DoesNotExist:
            response = {'message':'User does not exist'}

        return JsonResponse(response)
    else:
        logger.info('Request method is not POST')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@ensure_csrf_cookie
def getSubscriberPolicy(request):
    """View function to get all data catalogue elements"""
    if request.method == "GET":
        # try if user exist by email
        try:
            user = User.objects.get(email=request.GET.get('user_mail', ''))
            subscriber_policies_list = []
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
        logger.info('Request method is not GET')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
@ensure_csrf_cookie
def deleteSubscriberPolicy(request):
    """View function to delete publisher policy and transformations"""
    if request.method == "DELETE":
        logger.info(request.data)
        try:
            user = User.objects.get(email=request.data['user_email'])
            try:
                SubscriberPolicyManager.deletePolicy(user, request.data)

                return JsonResponse({'message':'The subscriber policy is deleted'})

            except SUBSCRIBER_POLICY.DoesNotExist:
                logger.info('Subscriber policy does not exist')
                return Response(status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            logger.info('User does not exist')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
    else:
        logger.info('Request method is not DELETE')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)