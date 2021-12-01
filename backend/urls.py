from django.conf.urls import url
from django.urls import path, include
from backend import views

urlpatterns = [
    # url(r'accounts/', include('django.contrib.auth.urls')),
    # url(r'login$', views.auth, name='auth'),
    url(r'api/postUser', views.postUser, name='postUser'),
    url(r'api/getUsers', views.getUsers, name='getUsers'),

    # catch-all pattern for compatibility with the Angular routes. This must be last in the list.
    url(r'^(?P<path>.*)$', views.index, name='index'),
]