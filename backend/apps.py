from django.apps import AppConfig
from backend.DataBrokerProxy import *
#import backend.SubscriberPolicyManager as SubscriberPolicyManager

class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'

    def ready(self):
        DataBrokerProxy.startClient()

        # TODO cause an error for the moment (on the import line)
        #SubscriberPolicyManager.updateStaticRouting()