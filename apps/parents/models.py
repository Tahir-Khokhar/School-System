"""School ERP — parents app."""
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator
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
    # CNIC: validated format (xxxxx-xxxxxxx-x) + UNIQUE only when non-empty.
    # Blank CNICs (e.g. on draft admissions) are allowed until the school
    # office enters the real one; the admission service uses a unique
    # fallback like "TEMP-<pk>" to avoid attaching all blank-CNIC parents
    # to one shared record.
    cnic = models.CharField(
        max_length=20, blank=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^\d{5}-\d{7}-\d$",
                message="CNIC must be in the format XXXXX-XXXXXXX-X (5-7-1 digits).",
            ),
        ],
        help_text="Format: XXXXX-XXXXXXX-X (Pakistani CNIC). Unique per parent when non-empty.",
    )
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["cnic"])]
        constraints = [
            # Unique only when CNIC is provided. Multiple blank CNICs are
            # allowed (admissions creates the parent record first; the school
            # office enters the real CNIC at verification time).
            models.UniqueConstraint(
                fields=["cnic"],
                condition=~models.Q(cnic=""),
                name="unique_parent_cnic_when_nonempty",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.get_relation_display()})"
