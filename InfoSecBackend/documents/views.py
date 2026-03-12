from .serializers import DocumentSerializer
from .models import Document
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import FileResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings

import os
# Create your views here

@api_view(['GET'])
def get_documents(request):
    # add request after for specific documents
    print("(debug) test")
    documents = Document.objects.all()
    serializer = DocumentSerializer(documents, many=True)
    print("(debug) documents: ")
    print(documents)
    print("(debug) serializer: ")
    print(serializer.data)
    return Response(serializer.data)

@xframe_options_exempt
@api_view(['GET'])
def get_pdf(request, filename):
    print("(debug) getting pdf: " + filename)
    filepath = os.path.join(settings.MEDIA_ROOT, "documents/pdfs", filename)
    return FileResponse(open(filepath, "rb"), content_type="application/pdf")