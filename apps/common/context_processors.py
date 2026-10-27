"""Context processor exposing school-wide context to all templates.

The school_object + active_year queries are cached for 5 minutes per request
batch (using Django's per-process cache) so that this context processor doesn't
hit the database 3 times per HTTP request on a busy page (e.g. dashboard with
4 sub-panels each rendering the school context).
"""
from django.conf import settings
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject


_SCHOOL_CACHE_KEY = "school_context:school_obj"
_YEAR_CACHE_KEY = "school_context:active_year"
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _cached_school_obj():
    """Cache the (singleton) School row for 5 minutes — saves a DB query
    on every request that calls this context processor."""
    obj = cache.get(_SCHOOL_CACHE_KEY)
    if obj is None:
        from .models import School
        obj = School.objects.first()
        cache.set(_SCHOOL_CACHE_KEY, obj, _CACHE_TTL_SECONDS)
    return obj


def _cached_active_year():
    """Cache the active AcademicYear object for 5 minutes — saves a DB query
    AND a cache miss pattern (the model's get_active() method already caches
    the pk, but it returns a fresh query for the object each call)."""
    obj = cache.get(_YEAR_CACHE_KEY)
    if obj is None:
        from .models import AcademicYear
        obj = AcademicYear.objects.get_active()
        cache.set(_YEAR_CACHE_KEY, obj, _CACHE_TTL_SECONDS)
    return obj


def school_context(request):
    """Available as {{ school_name }}, {{ school_address }}, etc. in every template."""
    active_year = None
    school_obj = None
    if request.user.is_authenticated:
        # Lazy-evaluate so unauthenticated requests (landing page, login page)
        # don't even touch the cache.
        active_year = SimpleLazyObject(_cached_active_year)
        school_obj = SimpleLazyObject(_cached_school_obj)

    unread_notifications = 0
    if request.user.is_authenticated:
        # Per-user unread count is NOT cacheable across users — but it IS
        # already an indexed COUNT(*) query so the cost is one indexed lookup.
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
