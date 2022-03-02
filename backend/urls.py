#from django.conf.urls import url
from django.urls import re_path
from django.urls import path, include
from backend import views, views_user
from django.contrib.auth.views import LogoutView
from rest_framework_swagger.views import get_swagger_view
from adc_backend.settings import REDIRECT_URL
from django.contrib.auth import views as auth_views
from rest_framework.schemas import get_schema_view
from rest_framework.authtoken.views import obtain_auth_token, ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

schema_view = get_swagger_view(title='ADC Swagger API')

class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
          #   'user_id': user.pk,
          #   'email': user.email
        })

urlpatterns = [
    re_path(r'api/swagger/', schema_view),

    re_path(r'api/schema/', get_schema_view(
     title="EuroControl Aviation Data Corridor - API",
     description="Broker API",
     version="1.0.0"
    ), name='schema'),

    re_path(r'api/publish/', views.publishMessage, name='publish'),
    re_path(r'api/test/', views.Test, name='Test'),
    #re_path(r'api/test/', views.TestView.as_view(), name='TestView'),
#     re_path(r'api/token/', obtain_auth_token, name='obtain_auth_token'),
    re_path(r'api/token/', CustomAuthToken.as_view(), name='obtain_auth_token'),

    re_path(r'auth$', views_user.auth, name='auth'),
    re_path(r'logout$', views_user.logout_view, name='logout_view'),


    # re_path(r'accounts/', include('django.contrib.auth.urls')),
    re_path(r'^password_reset/$', views_user.ResetPasswordView.as_view(), name="password_reset"),
    re_path(r'^password-reset-done/',
         auth_views.PasswordResetDoneView.as_view(template_name='main/password/password_reset_done.html'),
         name='password_reset_done'),
    re_path(r'^password-reset-confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
         auth_views.PasswordResetConfirmView.as_view(template_name='main/password/password_reset_confirm.html'),
         name='password_reset_confirm'),
    re_path(r'^password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='main/password/password_reset_complete.html'),
         name='password_reset_complete'),

    re_path(r'api/postUser', views_user.postUser, name='postUser'),
    re_path(r'api/getUsers', views_user.getUsers, name='getUsers'),
    re_path(r'api/deleteUser', views_user.deleteUser, name='deleteUser'),

    re_path(r'api/postDataCatalogue', views.postDataCatalogue, name='postDataCatalogue'),
    re_path(r'api/getDataCatalogue', views.getDataCatalogue, name='getDataCatalogue'),
    re_path(r'api/deleteDataElement', views.deleteDataElement, name='deleteDataElement'),

    re_path(r'api/postPublisherPolicy', views.postPublisherPolicy, name='postPublisherPolicy'),
    re_path(r'api/getPublisherPolicy', views.getPublisherPolicy, name='getPublisherPolicy'),
    re_path(r'api/deletePublisherPolicy', views.deletePublisherPolicy, name='deletePublisherPolicy'),
    
    re_path(r'api/postSubscriberPolicy', views.postSubscriberPolicy, name='postSubscriberPolicy'),
    re_path(r'api/getSubscriberPolicy', views.getSubscriberPolicy, name='getSubscriberPolicy'),
    re_path(r'api/deleteSubscriberPolicy', views.deleteSubscriberPolicy, name='deleteSubscriberPolicy'),

    re_path(r'api/getOrganizationsName', views.getOrganizationsName, name='getOrganizationsName'),
    re_path(r'api/getOrganizationsType', views.getOrganizationsType, name='getOrganizationsType'),

    # catch-all pattern for compatibility with the Angular routes. This must be last in the list.
    re_path(r'^(?P<path>.*)$', views.index, name='index'),
]