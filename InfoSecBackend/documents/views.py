from .serializers import DocumentSerializer
from .models import Document, Section, SubSection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.http import FileResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.conf import settings
from django.contrib.auth import get_user_model
import json

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

@api_view(['GET'])
def get_users(request):
    users = get_user_model().objects.values("id", "first_name", "last_name")
    return Response(users)

@api_view(['POST'])
def create_update_document(request):
    print("(debug) request.data:")
    print(request.data)

    User = get_user_model()

    sections = json.loads(request.data.get('sections'))
    tags = json.loads(request.data.get('tags'))
    pdf_file = request.data.get('pdf_file', None)
    
    #handle Document
    new_doc = None
    if str(request.data.get('id'))[:3] == 'new':
        new_doc = Document()
    else:
        new_doc = Document.objects.get(id=int(request.data.get('id')))

    new_doc.title = request.data.get('title')
    new_doc.details = request.data.get('details')
    new_doc.authoredBy = User.objects.get(id=int(request.data.get('authoredBy')))
    new_doc.reviewedBy = User.objects.get(id=int(request.data.get('reviewedBy')))
    if pdf_file:
        new_doc.pdf_file = pdf_file
    new_doc.lastReviewed = request.data.get('lastReviewed')
    new_doc.tags = tags
    new_doc.save()

    #handle Section
    for sect in sections:
        new_sect = None
        if str(sect.get('id'))[:3] == 'new':
            new_sect = Section()
        else:
            new_sect = Section.objects.get(id=int(sect.get('id')))
        
        new_sect.parent = new_doc
        new_sect.title = sect.get('title')
        new_sect.description = sect.get('description')
        new_sect.save()

        #handle SubSection
        for subsect in sect.get('subsections'):
            new_subsect = None
            if str(subsect.get('id'))[:3] == 'new':
                new_subsect = SubSection()
            else:
                new_subsect = SubSection.objects.get(id=int(subsect.get('id')))

            new_subsect.parent = new_sect
            new_subsect.title = subsect.get('title')
            new_subsect.content = subsect.get('content')
            new_subsect.save()

    return Response(status=status.HTTP_200_OK)

@xframe_options_exempt
@api_view(['GET'])
def get_pdf(request, filename):
    print("(debug) getting pdf: " + filename)
    filepath = os.path.join(settings.MEDIA_ROOT, "documents/pdfs", filename)
    return FileResponse(open(filepath, "rb"), content_type="application/pdf")
