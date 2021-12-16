from django.conf.urls import url
from django.urls import path, include
from backend import views, views_user

urlpatterns = [
    # url(r'accounts/', include('django.contrib.auth.urls')),
    url(r'auth$', views_user.auth, name='auth'),
    url(r'logout$', views_user.logout, name='login'),

    url(r'accounts/', include('django.contrib.auth.urls')),
    url(r'password_reset', views_user.password_reset_request, name="password_reset"),

    url(r'api/postUser', views_user.postUser, name='postUser'),
    url(r'api/getUsers', views_user.getUsers, name='getUsers'),
    url(r'api/deleteUser', views_user.deleteUser, name='deleteUser'),

    url(r'api/postDataCatalogue', views.postDataCatalogue, name='postDataCatalogue'),
    url(r'api/getDataCatalogue', views.getDataCatalogue, name='getDataCatalogue'),
    url(r'api/deleteDataElement', views.deleteDataElement, name='deleteDataElement'),

    url(r'api/postPublisherPolicy', views.postPublisherPolicy, name='postPublisherPolicy'),
    url(r'api/getPublisherPolicy', views.getPublisherPolicy, name='getPublisherPolicy'),
    url(r'api/deletePublisherPolicy', views.deletePublisherPolicy, name='deletePublisherPolicy'),
    
    url(r'api/postSubscriberPolicy', views.postSubscriberPolicy, name='postSubscriberPolicy'),
    url(r'api/getSubscriberPolicy', views.getSubscriberPolicy, name='getSubscriberPolicy'),
    url(r'api/deleteSubscriberPolicy', views.deleteSubscriberPolicy, name='deleteSubscriberPolicy'),

    url(r'api/getOrganizationsName', views.getOrganizationsName, name='getOrganizationsName'),
    url(r'api/getOrganizationsType', views.getOrganizationsType, name='getOrganizationsType'),

    # catch-all pattern for compatibility with the Angular routes. This must be last in the list.
    url(r'^(?P<path>.*)$', views.index, name='index'),
]