"""Permission classes for the accounts domain.

Auth endpoints (register/login/me) use DRF's built-in AllowAny/IsAuthenticated
directly since there's no accounts-specific rule yet. Phase 2 (OTP auth) is
the natural place to add e.g. an "IsPhoneVerified" permission.
"""
