"""Read-query helpers backing DashboardService.get_overview.

Kept thin on purpose -- the interesting logic is *combining* several
queries into one overview payload, which is what services.py does. This
file exists for structural consistency and for any dashboard-specific query
that doesn't belong to another domain.
"""
