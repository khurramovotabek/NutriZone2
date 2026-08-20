from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared.permissions import IsAdminUser

from ..services import DashboardService
from .serializers import DashboardOverviewSerializer


class DashboardOverviewView(APIView):
    """One-request summary for the admin dashboard landing page."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        data = DashboardService.get_overview()
        return Response(DashboardOverviewSerializer(data, context={"request": request}).data)
