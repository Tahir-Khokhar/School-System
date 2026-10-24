"""School ERP — parents app."""
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel


class Parent(TimeStampedModel):
    class Relation(models.TextChoices):
        FATHER = "father", "Father"
        MOTHER = "mother", "Mother"
        GUARDIAN = "guardian", "Guardian"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="parent_profile",
    )
    full_name = models.CharField(max_length=200)
    relation = models.CharField(max_length=10, choices=Relation.choices, default=Relation.FATHER)
    cnic = models.CharField(max_length=20, blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["cnic"])]

    def __str__(self):
        return f"{self.full_name} ({self.get_relation_display()})"
