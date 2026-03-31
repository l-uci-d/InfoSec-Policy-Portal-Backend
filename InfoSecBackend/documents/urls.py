from django.urls import path
from .views import get_documents, get_pdf

urlpatterns = [
    path('get-documents/', get_documents, name='get_documents'),
    path('get-pdf/<str:filename>/', get_pdf, name='get_pdf')
]