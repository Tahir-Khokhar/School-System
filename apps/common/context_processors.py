"""Context processor exposing school-wide context to all templates."""
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from .models import AcademicYear, School


def school_context(request):
    """Available as {{ school_name }}, {{ school_address }}, etc. in every template."""
    active_year = None
    school_obj = None
    if request.user.is_authenticated:
        active_year = AcademicYear.objects.get_active()
        school_obj = School.objects.first()

    unread_notifications = 0
    if request.user.is_authenticated:
        # lazy import to avoid circulars
        from apps.notifications.models import Notification
        unread_notifications = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

    return {
        "school_name": settings.SCHOOL_NAME,
        "school_tagline": settings.SCHOOL_TAGLINE,
        "school_address": settings.SCHOOL_ADDRESS,
        "school_phone": settings.SCHOOL_PHONE,
        "school_email": settings.SCHOOL_EMAIL,
        "currency_symbol": settings.SCHOOL_CURRENCY_SYMBOL,
        "active_academic_year": active_year,
        "school_obj": school_obj,
        "unread_notifications_count": unread_notifications,
    }
