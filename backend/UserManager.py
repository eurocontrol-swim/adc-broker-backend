import logging
from backend.Policy import *
from django.contrib.auth.models import User
from .models import USER_INFO, ORGANIZATIONS
import backend.DataBrokerProxy as DataBrokerProxy
from rest_framework.authtoken.models import Token

logger = logging.getLogger('adc')

def addUser(request_data):
    """Add user in the database"""
    try:
        organizations = ORGANIZATIONS.objects.filter(name=request_data['organization_name'])
        organization_id = None
        for organization in organizations:
            if request_data['organization_type'] == organization.type:
                # If same organization type, get organization id
                organization_id = organization.id
        if organization_id is None:
            # create new organization
            new_organization = ORGANIZATIONS.objects.create(name=request_data['organization_name'], type=request_data['organization_type'])
            new_organization.save()
            # get organization id
            organization_id = new_organization.id
    except ORGANIZATIONS.DoesNotExist:
        # create new organization
        new_organization = ORGANIZATIONS.objects.create(name=request_data['organization_name'], type=request_data['organization_type'])
        new_organization.save()
        # get organization id
        organization_id = new_organization.id

    user_email = request_data['email']
    # try if user exist by email
    try:
        user = User.objects.get(id=request_data['id'])
        logger.info("User already exist")

    except User.DoesNotExist:
        # User does not exist on auth_user table
        # Create new user
        new_user = User.objects.create(username=user_email, first_name=request_data['firstname'], last_name=request_data['lastname'], email=user_email)
        # Create password
        if request_data['password'] is not None:
            new_user.set_password(request_data['password'])
        new_user.save()

        # Generate API auth token for user
        user_token = Token.objects.create(user=new_user)
        user_token.save()

        #save new user info
        new_user_info = USER_INFO.objects.create(user_id = new_user.id, user_role=request_data['role'], user_organization_id=organization_id)
        new_user_info.save()
        logger.info("User created")
    
        if new_user_info.user_role == 'subscriber':
            # create user in the broker
            queue_prefix = DataBrokerProxy.generateQueuePrefix(organization_id, new_user.first_name, new_user.last_name)
            broker_user_name = DataBrokerProxy.generateBrokerUsername(new_user.first_name, new_user.last_name)
            # TODO handle password
            DataBrokerProxy.createUser(broker_user_name, broker_user_name, queue_prefix)


def updateUser(request_data):
    """Update a user in the database"""
    try:
        organizations = ORGANIZATIONS.objects.filter(name=request_data['organization_name'])
        organization_id = None
        for organization in organizations:
            if request_data['organization_type'] == organization.type:
                # If same organization type, get organization id
                organization_id = organization.id
        if organization_id is None:
            # create new organization
            new_organization = ORGANIZATIONS.objects.create(name=request_data['organization_name'], type=request_data['organization_type'])
            new_organization.save()
            # get organization id
            organization_id = new_organization.id
    except ORGANIZATIONS.DoesNotExist:
        # create new organization
        new_organization = ORGANIZATIONS.objects.create(name=request_data['organization_name'], type=request_data['organization_type'])
        new_organization.save()
        # get organization id
        organization_id = new_organization.id

    user_email = request_data['email']
    # try if user exist by email
    try:
        user = User.objects.get(id=request_data['id'])
        # Check if another user already has this username
        already_username = User.objects.filter(username=user_email).exclude(id=request_data['id'])
        if already_username:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data='Another user already has this username')
        else:
            # Update User if exist on auth_user table
            user.__dict__.update(username=user_email, first_name=request_data['firstname'], last_name=request_data['lastname'], email=user_email)
            # Update user password
            if request_data['password'] is not None:
                user.set_password(request_data['password'])
            user.save()
            user_info = USER_INFO.objects.get(user_id=user.id)
            user_info.__dict__.update(user_role=request_data['role'], user_organization_id=organization_id)
            user_info.save()
            logger.info("User updated")

    except User.DoesNotExist:
        logger.info("User does not exist")

def getuserList():
    """Retrieve the whole user list"""
    user_list = []
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
    return user_list

def deleteUser(user_data):
    """Delete user"""
    # TODO - Math user authorization if role is 'administrator'
    # try:
    #     user = User.objects.get(email=ruser_data['user_email'], role='administration')
    
    if USER_INFO.objects.get(user_id=user_data.id).user_role == 'subscriber':
        # delete user in the broker
        broker_user_name = DataBrokerProxy.generateBrokerUsername(user_data.first_name, user_data.last_name)
        DataBrokerProxy.deleteUser(broker_user_name)

    user_data.delete()
    logger.info("The user is deleted")
