import logging
from backend.Policy import *
from django.contrib.auth.models import User
from .models import DATA_CATALOGUE_ELEMENT
import backend.DataBrokerProxy as DataBrokerProxy

logger = logging.getLogger('adc')

def addCatalogueElement(request_data):
    """Add catalogue element in the database"""
    new_data_element = DATA_CATALOGUE_ELEMENT.objects.create(data_type=request_data['type'], data_path=request_data['path'], data_schema=request_data['schema'])
    new_data_element.save()
    logger.info('Data saved')

def updateCatalogueElement(request_data):
    """Update catalogue element in the database"""
    data_element = DATA_CATALOGUE_ELEMENT.objects.get(id=request_data['id'])
    data_element.__dict__.update(data_type=request_data['type'], data_path=request_data['path'], data_schema=request_data['schema'])
    data_element.save()
    logger.info('Data updated')

def getCatalogueElementList():
    """Get catalogue element list from database"""
    data_catalogue = DATA_CATALOGUE_ELEMENT.objects.values()
    return data_catalogue
    