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
from adc_backend.settings import LOGIN_REDIRECT_URL
from django.contrib.auth import authenticate, login, logout
from .models import USER_INFO, ORGANIZATIONS
from rest_framework import status
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie

import backend.DataBrokerProxy as DataBrokerProxy

logger = logging.getLogger('adc')

@api_view(['POST'])
def auth(request):
    """View function for login user"""
    if request.method == "POST":
        username = request.data['username']
        password = request.data['password']

        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_active:
            login(request, user)
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)
    else:
        logger.info('Request method is not POST')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

def logout(request):
	if request.method == "GET":
		logout(request)
		return HttpResponseRedirect(LOGIN_REDIRECT_URL)
	else:
		logger.info('Request method is not GET')
		return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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

            organization_id = 0

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

            if new_user_info.user_role == 'subscriber':
                # create user in the broker
                queue_prefix = DataBrokerProxy.generateQueuePrefix(organization_id, new_user.first_name, new_user.last_name)
                broker_user_name = DataBrokerProxy.generateBrokerUsername(new_user.first_name, new_user.last_name)
                # TODO handle password
                DataBrokerProxy.createUser(broker_user_name, broker_user_name, queue_prefix)
        
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
        # TODO - Math user authorization if role is 'administrator'
        # try:
        #     user = User.objects.get(email=request.data['user_email'], role='administration')
        try:
            user = User.objects.get(email=request.data['user_email'])

            if USER_INFO.objects.get(user_id=user.id).user_role == 'subscriber':
                # delete user in the broker
                broker_user_name = DataBrokerProxy.generateBrokerUsername(user.first_name, user.last_name)
                DataBrokerProxy.deleteUser(broker_user_name)

            user.delete()

            return JsonResponse({'message':'The user is deleted'})

        except User.DoesNotExist:
            logger.info('User does not exist')
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # except User.DoesNotExist:
        #     logger.info('User does not exist are wrong access')
        #     return Response(status=status.HTTP_400_BAD_REQUEST)
        
    else:
        logger.info('Request method is not DELETE')
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


def password_reset_request(request):
	if request.method == "POST":
		password_reset_form = PasswordResetForm(request.POST)
		if password_reset_form.is_valid():
			data = password_reset_form.cleaned_data['email']
			associated_users = User.objects.filter(Q(email=data))
			if associated_users.exists():
				for user in associated_users:
					subject = "Password Reset Requested"
					email_template_name = "main/password/password_reset_email.txt"
					c = {
					"email":user.email,
					'domain':'127.0.0.1:8000',
					'site_name': 'Website',
					"uid": urlsafe_base64_encode(force_bytes(user.pk)),
					"user": user,
					'token': default_token_generator.make_token(user),
					'protocol': 'http',
					}
					email = render_to_string(email_template_name, c)
					try:
						send_mail(subject, email, 'admin@example.com' , [user.email], fail_silently=False)
					except BadHeaderError:
						return HttpResponse('Invalid header found.')
					return redirect ("/password_reset/done/")
	password_reset_form = PasswordResetForm()
	return render(request=request, template_name="main/password/password_reset.html", context={"password_reset_form":password_reset_form})