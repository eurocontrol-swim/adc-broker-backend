from django.shortcuts import render
from django.views.generic import TemplateView
from .models import USER_INFO

class index(TemplateView):
    # new_user = USER_INFO.objects.create(user_id = 1, user_role='Administrator', user_organization_id=1)
    # new_user.save()
    template_name = "index.html"

def auth():
    return

def getPublisherPolicies():
    return
