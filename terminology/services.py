from datetime import date

from django.utils import timezone

from .models import RefBook, RefBookVersion


def get_current_version(refbook: RefBook, on_date: date | None = None):
    """Return the latest version effective on the requested date, if any."""
    effective_date = on_date or timezone.localdate()
    return (
        RefBookVersion.objects.filter(refbook=refbook, start_date__lte=effective_date)
        .order_by('-start_date', '-pk')
        .first()
    )