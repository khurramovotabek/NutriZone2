from django import forms

from .models import Notification


class SendNotificationForm(forms.Form):
    SCOPE_ALL = "all"
    SCOPE_USERS = "users"
    SCOPE_CHOICES = [(SCOPE_ALL, "All active users"), (SCOPE_USERS, "Specific usernames")]

    scope = forms.ChoiceField(choices=SCOPE_CHOICES, widget=forms.RadioSelect, initial=SCOPE_ALL)
    usernames = forms.CharField(
        required=False,
        help_text="Comma-separated usernames. Only used when scope is 'Specific usernames'.",
        widget=forms.TextInput(attrs={"placeholder": "johndoe, janedoe"}),
    )
    notification_type = forms.ChoiceField(choices=Notification.NotificationType.choices)
    title = forms.CharField(max_length=255)
    body = forms.CharField(required=False, widget=forms.Textarea)
    link_path = forms.CharField(
        required=False, help_text="Optional frontend-relative path, e.g. /products/whey-protein"
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("scope") == self.SCOPE_USERS and not cleaned.get("usernames", "").strip():
            raise forms.ValidationError("Enter at least one username, or choose 'All active users'.")
        return cleaned
