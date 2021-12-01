import logging
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view
# from rest_framework.schemas import AutoSchema
from django.shortcuts import render
# from django.views.generic import TemplateView
from .models import USER_INFO, ORGANIZATIONS
from django.contrib.auth.models import User

logger = logging.getLogger('adc')

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
            response = {'user' : 'new_user', 'new_user_info': 'new_user_info'}
        
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