"""Notifications service + model."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Type(models.TextChoices):
        FEE_PAYMENT = "fee_payment", "Fee Payment"
        FEE_DUE = "fee_due", "Fee Due"
        HOMEWORK = "homework", "Homework"
        TEST_RESULT = "test_result", "Test Result"
        TERM_RESULT = "term_result", "Term Result"
        DATE_SHEET = "date_sheet", "Date Sheet"
        ANNOUNCEMENT = "announcement", "Announcement"
        ACTIVITY = "activity", "Activity"
        SYLLABUS = "syllabus", "Syllabus Update"
        ADMIN = "admin", "Administrative"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=Type.choices, default=Type.ADMIN)
    title = models.CharField(max_length=200)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [models.Index(fields=["user", "is_read"])]


class NotificationService:
    @staticmethod
    def notify(user, title, message, notification_type="admin", url=""):
        return Notification.objects.create(
            user=user, title=title, message=message,
            notification_type=notification_type, url=url,
        )

    @staticmethod
    def notify_role(role, title, message, notification_type="admin", url=""):
        from apps.accounts.models import User
        for u in User.objects.filter(role=role, is_active=True):
            NotificationService.notify(u, title, message, notification_type, url)

    @staticmethod
    def notify_user_queryset(users_qs, title, message, notification_type="admin", url=""):
        for u in users_qs:
            NotificationService.notify(u, title, message, notification_type, url)
