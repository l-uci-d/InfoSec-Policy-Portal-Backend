from django.db import models
from django.conf import settings
import uuid

# TODO: author and reviewer fields
# Create your models here.

class Tag(models.Model):
    tag_content = models.CharField(max_length=255)

    def __str__(self):
        return self.tag_content
class Document(models.Model):
    def document_pdf_path(instance, filename): 
        return f"documents/pdfs/{uuid.uuid4() }_{filename}"
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    pdf_file = models.FileField(upload_to=document_pdf_path)
    # no author or reviewer for now until login is done
    authoredBy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='authored_documents', on_delete=models.CASCADE, null=True)
    reviewedBy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviewed_documents', on_delete=models.CASCADE, null=True)
    lastReviewed = models.DateTimeField(auto_now_add=True)
    lastUpdated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title
    
class Section(models.Model):
    parent = models.ForeignKey(Document, related_name='sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.parent.title} - {self.title}"

class SubSection(models.Model):
    parent = models.ForeignKey(Section, related_name='subsections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    def __str__(self):
        return f"{self.parent.parent.title} - {self.parent.title} - {self.title}"
    
