import logging
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
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin

import backend.UserManager as UserManager

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
        if request.data['id'] is not None:
            # try if user exist by email
            try:
                user = User.objects.get(email=request.data['email'])
                # Check if another user already has this username
                already_username = User.objects.filter(username=request.data['email']).exclude(id=request.data['id'])
                if already_username:
                    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Another user already has this username')
                else:
                    if UserManager.updateUser(request.data):
                        response = {'message':'User updated'}
                        return JsonResponse(response)
                    else:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data='User does not exist')

            except User.DoesNotExist:
                if UserManager.addUser(request.data):
                    response = {'message':'User created'}
                    return JsonResponse(response)
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data='User already exist')
        else:
            if UserManager.addUser(request.data):
                response = {'message':'User created'}
                return JsonResponse(response)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data='User already exist')

    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not POST')

@api_view(['GET'])
@ensure_csrf_cookie
def getUsers(request):
    """View function to get all users informations"""
    if request.method == "GET":
        user_list = UserManager.getuserList()
        return JsonResponse({'users':user_list})
    else:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Request method is not GET')

@api_view(['DELETE'])
@ensure_csrf_cookie
def deleteUser(request):
    """View function to delete user and informations"""
    if request.method == "DELETE":
        # Math user authorization if role is 'administrator'
        try:
            user_admin = User.objects.get(email=request.data['user'])
            user_to_delete = User.objects.get(email=request.data['email'])
            if UserManager.checkUserRole(user_admin.id, 'administrator'):
                UserManager.deleteUser(user_to_delete)
                return JsonResponse({'message':'The user is deleted'})
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data='The user does not have the ADMINISTRATOR role')
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
