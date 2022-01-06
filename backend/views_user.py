from django.shortcuts import render, redirect
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.response import Response
from adc_backend.settings import REDIRECT_URL
from django.contrib.auth import authenticate, login, logout
from .models import USER_INFO, ORGANIZATIONS
from rest_framework import status
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin

import logging
logger = logging.getLogger('adc')

@api_view(['POST'])
def auth(request):
    """View function for login user"""
    if request.method == "POST":
        email = request.data['email']
        password = request.data['password']

        user = authenticate(username=email, password=password)
        if user is not None and user.is_active:
            login(request, user)
            user = getUser(user.id)
            response = {'user':user}
            return JsonResponse(response)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='Login error')
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not POST')

def logout_view(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            logout(request)
            return redirect(REDIRECT_URL)
        else:
            return redirect(REDIRECT_URL)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

def getUser(id):
    # Get user informations
    user = User.objects.filter(id=id).values('first_name','last_name','email')[0]
    info = USER_INFO.objects.filter(user_id=id).values('user_role','user_organization_id')[0]
    organization = ORGANIZATIONS.objects.filter(id=info['user_organization_id']).values('name', 'type')[0]
    # Clean dictionary without id
    info.pop('user_organization_id', None)
    user_details = dict(**user, **info, **organization)
    return user_details

@api_view(['POST'])
@ensure_csrf_cookie
def postUser(request):
    """View function for create or update user"""
    if request.method == "POST":
        try:
            organization = ORGANIZATIONS.objects.get(name=request.data['organization_name'])
            if request.data['organization_type'] == organization.type:
                # If same organization type, get organization id
                organization_id = organization.id
            else:
                # create new organization
                new_organization = ORGANIZATIONS.objects.create(name=request.data['organization_name'], type=request.data['organization_type'])
                new_organization.save()
                # get organization id
                organization_id = new_organization.id
        except ORGANIZATIONS.DoesNotExist:
            # create new organization
            new_organization = ORGANIZATIONS.objects.create(name=request.data['organization_name'], type=request.data['organization_type'])
            new_organization.save()
            # get organization id
            organization_id = new_organization.id

        user_email = request.data['email']
        # try if user exist by email
        try:
            user = User.objects.get(id=request.data['id'])
            # Check if another user already has this username
            already_username = User.objects.filter(username=user_email).exclude(id=request.data['id'])
            if already_username:
                return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Another user already has this username')
            else:
                # Update User if exist on auth_user table
                user.__dict__.update(username=user_email, first_name=request.data['firstname'], last_name=request.data['lastname'], email=user_email)
                # Update user password
                if request.data['password'] is not None:
                    user.set_password(request.data['password'])
                user.save()
                user_info = USER_INFO.objects.get(user_id=user.id)
                user_info.__dict__.update(user_role=request.data['role'], user_organization_id=organization_id)
                user_info.save()
                response = {'message':'User updated'}

        except User.DoesNotExist:
            # User does not exist on auth_user table
            # Create new user
            new_user = User.objects.create(username=user_email, first_name=request.data['firstname'], last_name=request.data['lastname'], email=user_email)
            # Create password
            if request.data['password'] is not None:
                new_user.set_password(request.data['password'])
            new_user.save()

            #save new user info
            new_user_info = USER_INFO.objects.create(user_id = new_user.id, user_role=request.data['role'], user_organization_id=organization_id)
            new_user_info.save()
            response = {'message':'User created'}
        
        return JsonResponse(response)
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not POST')

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
            # user.pop('id', None)
            # Create a list with dictionaries
            user_list.append(dict(**user, **info, **organization))
        return JsonResponse({'users':user_list})
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

@api_view(['DELETE'])
@ensure_csrf_cookie
def deleteUser(request):
    """View function to delete user and informations"""
    if request.method == "DELETE":
        # TODO - Math user authorization if role is 'administrator'
        # try:
        #     user = User.objects.get(email=request.data['user_email'], role='administration')
        try:
            user = User.objects.get(email=request.data['user_email'])
            user.delete()
            return JsonResponse({'message':'The user is deleted'})

        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='User does not exist')
        
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not DELETE')


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'main/password/password_reset.html'
    email_template_name = 'main/password/password_reset_email.html'
    subject_template_name = 'main/password/password_reset_subject.txt'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    # success_url = reverse_lazy('index', args='/') #Return to angular home page