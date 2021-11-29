from django.conf.urls import url
from backend import views

urlpatterns = [
    url(r'^(?P<path>.*)$', views.index.as_view(), name='index'),
    url(r'login$', views.auth, name='auth'),
    url(r'getPublisherPolicies$', views.getPublisherPolicies, name='getPublisherPolicies'),
]