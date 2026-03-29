from .serializers import DocumentSerializer
from .models import Document
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.http import FileResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings

import os
# Create your views here

@api_view(['GET'])
def get_documents(request):
    documents = Document.objects.all()
    serializer = DocumentSerializer(instance=documents, many=True)
    print("(debug) documents: ")
    print(documents)
    print("(debug) serializer: ")
    print(serializer.data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def create_document(request):
    doc_serializer = DocumentSerializer(data=request.data)
    if doc_serializer.is_valid():
        doc_serializer.save()
        return Response(doc_serializer.data, status=status.HTTP_201_CREATED)

    return Response(doc_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@xframe_options_exempt
@api_view(['GET'])
def get_pdf(request, filename):
    print("(debug) getting pdf: " + filename)
    filepath = os.path.join(settings.MEDIA_ROOT, "documents/pdfs", filename)
    return FileResponse(open(filepath, "rb"), content_type="application/pdf")
