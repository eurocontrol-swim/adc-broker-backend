import logging
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view
# from rest_framework.schemas import AutoSchema
from django.shortcuts import render
# from django.views.generic import TemplateView
from .models import USER_INFO, ORGANIZATIONS, DATA_CATALOGUE_ELEMENT, PUBLISHER_POLICY, TRANSFORMATION_ITEM
from django.contrib.auth.models import User

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
def postUser(request):
    """View function for create or update user"""
    if request.method == "POST":
        user_email = request.data['email']
        # try if user not exist by email
        try:
            user = User.objects.get(email=user_email)
            # User exist on auth_user table
            response = {'message':'user already exist'}

        except User.DoesNotExist:
            # User does not exist on auth_user table
            # create new user
            new_user = User.objects.create(username=request.data['email'], first_name=request.data['firstname'], last_name=request.data['lastname'], email=request.data['email'])
            # new_user.set_password(request.data['password'])
            new_user.save()

            try:
                organization = ORGANIZATIONS.objects.get(name=request.data['organization_name'])
                if request.data['organization_type'] == organization.type:
                    # same organization type
                    # get organization id
                    organization_id = organization.id
                else:
                    # create new organization
                    new_organization = ORGANIZATIONS.objects.create(name=request.data['organization_name'], type=request.data['organization_type'])
                    new_organization.save()
                    # get organization id
                    organization_id = new_organization.id
            except ORGANIZATIONS.DoesNotExist:
                logger.info('organization does not exist')
                # create new organization
                new_organization = ORGANIZATIONS.objects.create(name=request.data['organization_name'], type=request.data['organization_type'])
                new_organization.save()
                # get organization id
                organization_id = new_organization.id
            #save new user info
            new_user_info = USER_INFO.objects.create(user_id = new_user.id, user_role=request.data['role'], user_organization_id=organization_id)
            new_user_info.save()
            response = {'message':'user created'}
        
        return JsonResponse(response)
    else:
        logger.info('Request method is not POST')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
@ensure_csrf_cookie
def getUsers(request):
    """View function to get all users informations"""
    user_list = []
    if request.method == "GET":
        # Get all users from database
        all_users = User.objects.values('id','first_name','last_name','email')
        for user in all_users:
            # Get user informations
            info = USER_INFO.objects.filter(user_id=user['id']).values('user_role','user_organization_id')[0]
            # Get user organization
            organization = ORGANIZATIONS.objects.filter(id=info['user_organization_id']).values('name', 'type')[0]
            # Rename keys
            organization['organization_name'] = organization.pop('name')
            organization['organization_type'] = organization.pop('type')
            # Clean dictionary without id
            info.pop('user_organization_id', None)
            user.pop('id', None)
            # Create a list with dictionaries
            user_list.append(dict(**user, **info, **organization))
        return JsonResponse({'users':user_list})
    else:
        logger.info('Request method is not GET')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['DELETE'])
@ensure_csrf_cookie
def deleteUser(request):
    """View function to delete user and informations"""
    if request.method == "DELETE":
        logger.info(request.data)
        try:
            user = User.objects.get(email=request.data['user_email'])
            user.delete()
            return JsonResponse({'message':'The user is deleted'})

        except User.DoesNotExist:
            logger.info('User does not exist')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
    else:
        logger.info('Request method is not DELETE')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
        try:
            data = DATA_CATALOGUE_ELEMENT.objects.get(id=request.data['data_id'])
            data.delete()
            return JsonResponse({'message':'The data element is deleted'})

        except DATA_CATALOGUE_ELEMENT.DoesNotExist:
            logger.info('Data element does not exist')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
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
            user = User.objects.get(email=request.data['user_email'])

            # user_organization_id = USER_INFO.objects.get(user_id = user.id).user_organization_id

            # TODO - Try if transformations available
            transformations = request.data['transformations']
            catalogue_element = DATA_CATALOGUE_ELEMENT.objects.get(id=str(request.data['catalogue_id']))

            # create new publisher policy
            new_publisher_policy = PUBLISHER_POLICY.objects.create(user_id=user.id, policy_type=request.data['policy_type'], catalogue_element_id=catalogue_element.id)
            new_publisher_policy.save()

            for index, item in enumerate(transformations):
                # create new transformation items
                new_transformation_item = TRANSFORMATION_ITEM.objects.create(item_order=index, publisher_policy_id=new_publisher_policy.id, json_path=item['json_path'], item_type=item['item_type'], item_operator=item['item_operator'], organization_name=item['organization_name'], organization_type=item['organization_type'])
                new_transformation_item.save()

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
            # Get all data catalogue elements from database
            all_policies = PUBLISHER_POLICY.objects.filter(user_id = user.id).values('id','created_at','policy_type')
            for policy in all_policies:
                if TRANSFORMATION_ITEM.objects.filter(publisher_policy_id=policy['id']):
                    transformation = TRANSFORMATION_ITEM.objects.filter(publisher_policy_id=policy['id']).values('item_order', 'item_operator', 'item_type', 'json_path', 'organization_type', 'organization_name')
                    # Create a list with dictionaries
                    publisher_policies_list.append({'policy':policy, 'transformations':list(transformation)})
            response = {'policies':publisher_policies_list}
        except User.DoesNotExist:
            response = {'message':'User does not exist'}
        
        return JsonResponse(response)
    else:
        logger.info('Request method is not GET')
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