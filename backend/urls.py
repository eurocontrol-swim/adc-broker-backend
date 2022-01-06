from django.conf.urls import url
from django.urls import path, include
from backend import views, views_user
from django.contrib.auth.views import LogoutView
from rest_framework_swagger.views import get_swagger_view
from adc_backend.settings import REDIRECT_URL
from django.contrib.auth import views as auth_views

schema_view = get_swagger_view(title='ADC Swagger API')

urlpatterns = [
    url(r'api/swagger/', schema_view),

    url(r'auth$', views_user.auth, name='auth'),
    url(r'logout$', views_user.logout_view, name='logout_view'),

    # url(r'accounts/', include('django.contrib.auth.urls')),
    url(r'^password_reset/$', views_user.ResetPasswordView.as_view(), name="password_reset"),
    url(r'^password-reset-done/',
         auth_views.PasswordResetDoneView.as_view(template_name='main/password/password_reset_done.html'),
         name='password_reset_done'),
    url(r'^password-reset-confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
         auth_views.PasswordResetConfirmView.as_view(template_name='main/password/password_reset_confirm.html'),
         name='password_reset_confirm'),
    url(r'^password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='main/password/password_reset_complete.html'),
         name='password_reset_complete'),

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