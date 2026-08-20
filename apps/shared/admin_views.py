from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from apps.dashboard.services import DashboardService


@staff_member_required
def nutrizone_dashboard_view(request):
    """A premium stats dashboard linked from the Jazzmin sidebar.

    Deliberately reuses apps.dashboard.services.DashboardService (the same
    aggregation already powering GET /api/v1/dashboard/overview/) rather
    than writing a second, parallel set of queries -- one tested source of
    truth for "what does the admin overview actually show."
    """
    overview = DashboardService.get_overview()
    return render(request, "admin/nutrizone_dashboard.html", {"overview": overview, "title": "Dashboard"})
