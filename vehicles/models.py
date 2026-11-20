from django.db import models

from core.models import AuditedModel


class Make(AuditedModel):
    name = models.CharField(max_length=100, unique=True)
    founded_at = models.DateField()
    logo = models.ImageField(upload_to='make_logos/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Vehicle(AuditedModel):
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name='vehicles')
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    engine = models.PositiveIntegerField(help_text='Engine displacement in cc')
    image = models.ImageField(upload_to='vehicle_images/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.make.name} {self.name} {self.model}'
