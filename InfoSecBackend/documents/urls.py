from django.urls import path
from .views import get_documents, get_pdf, create_update_document, get_users

urlpatterns = [
    path('get-documents/', get_documents, name='get_documents'),
    path('get-pdf/<str:filename>/', get_pdf, name='get_pdf'),
    path('create-update-doc/', create_update_document, name='create_update_doc'),
    path('get-users/', get_users, name="get_users") 
]