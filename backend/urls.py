from django.conf.urls import url
from django.urls import path, include
from backend import views

urlpatterns = [
    # url(r'accounts/', include('django.contrib.auth.urls')),
    # url(r'login$', views.auth, name='auth'),
    url(r'api/postUser', views.postUser, name='postUser'),
    url(r'api/getUsers', views.getUsers, name='getUsers'),
    url(r'api/deleteUser', views.deleteUser, name='deleteUser'),

    url(r'api/postDataCatalogue', views.postDataCatalogue, name='postDataCatalogue'),
    url(r'api/getDataCatalogue', views.getDataCatalogue, name='getDataCatalogue'),
    url(r'api/deleteDataElement', views.deleteDataElement, name='deleteDataElement'),

    url(r'api/postPublisherPolicy', views.postPublisherPolicy, name='postPublisherPolicy'),
    url(r'api/getPublisherPolicy', views.getPublisherPolicy, name='getPublisherPolicy'),

    url(r'api/getOrganizationsName', views.getOrganizationsName, name='getOrganizationsName'),
    url(r'api/getOrganizationsType', views.getOrganizationsType, name='getOrganizationsType'),

    # catch-all pattern for compatibility with the Angular routes. This must be last in the list.
    url(r'^(?P<path>.*)$', views.index, name='index'),
]