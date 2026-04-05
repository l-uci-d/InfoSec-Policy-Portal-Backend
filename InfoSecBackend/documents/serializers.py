from rest_framework import serializers
from .models import Document, Section, SubSection
import os

class SubSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSection
        fields = ["id", "title", "content"]

class SectionSerializer(serializers.ModelSerializer):
    subsections = SubSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = ["id", "title", "description", "subsections"]

class DocumentSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    pdf_filename = serializers.SerializerMethodField()
    authorName = serializers.SerializerMethodField()
    reviewerName = serializers.SerializerMethodField()
    class Meta:
        model = Document
        #TODO: 
        # fields = ["id", "title", "details", "pdf_file", "pdf_filename", "authoredBy", "reviewedBy", "lastReviewed", "sections"]
        fields = ["id", "title", "details", "pdf_file", "pdf_filename", "authoredBy", "reviewedBy", "reviewerName", "authorName", "lastUpdated", "lastReviewed", "sections", "tags"]
    def get_pdf_filename(self, obj):
        if obj.pdf_file:
            return os.path.basename(obj.pdf_file.name)
        return None
    def get_authorName(self, obj):
        if obj.authoredBy:
            return f"{obj.authoredBy.first_name} {obj.authoredBy.last_name}"
        return None
    def get_reviewerName(self, obj):
        if obj.reviewedBy:
            return f"{obj.reviewedBy.first_name} {obj.reviewedBy.last_name}"
        return None