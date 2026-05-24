from rest_framework import serializers
from .models import Document, Section, SubSection, Tag
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

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "tag_content"]

class DocumentSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    pdf_filename = serializers.SerializerMethodField()
    pretty_pdf_filename = serializers.SerializerMethodField()
    authorName = serializers.SerializerMethodField()
    reviewerName = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    class Meta:
        model = Document
        fields = ["id", "title", "details", "pdf_file", "pretty_pdf_filename", "pdf_filename", "authoredBy", "reviewedBy", "reviewerName", "authorName", "lastUpdated", "lastReviewed", "sections", "tags"]
    def get_pdf_filename(self, obj):
        if obj.pdf_file:
            return os.path.basename(obj.pdf_file.name)
        return None
    def get_pretty_pdf_filename(self, obj):
        if obj.pdf_file:
            return os.path.basename(obj.pdf_file.name).split("_", 1)[1]
        return None
    def get_authorName(self, obj):
        if obj.authoredBy:
            return f"{obj.authoredBy.first_name} {obj.authoredBy.last_name}"
        return None
    def get_reviewerName(self, obj):
        if obj.reviewedBy:
            return f"{obj.reviewedBy.first_name} {obj.reviewedBy.last_name}"
        return None
    
