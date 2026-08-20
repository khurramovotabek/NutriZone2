from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .forms import SendNotificationForm
from .models import Notification
from .services import NotificationService

User = get_user_model()


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "recipient", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
    search_fields = ["title", "recipient__username"]
    autocomplete_fields = ["recipient"]
    readonly_fields = ["read_at"]
    change_list_template = "admin/notifications/notification_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("send/", self.admin_site.admin_view(self.send_notification_view), name="notifications_send"),
        ]
        return custom + urls

    def send_notification_view(self, request):
        if request.method == "POST":
            form = SendNotificationForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                kwargs = {
                    "notification_type": data["notification_type"],
                    "title": data["title"],
                    "body": data["body"],
                    "link_path": data["link_path"],
                }
                if data["scope"] == SendNotificationForm.SCOPE_ALL:
                    count = NotificationService.broadcast_to_all(**kwargs)
                else:
                    usernames = [u.strip() for u in data["usernames"].split(",") if u.strip()]
                    users = User.objects.filter(username__in=usernames)
                    count = NotificationService.notify_users(users, **kwargs)
                self.message_user(request, f"Sent {count} notification(s).", level=messages.SUCCESS)
                return redirect(reverse("admin:notifications_notification_changelist"))
        else:
            form = SendNotificationForm()

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "title": "Send Notification",
            "opts": self.model._meta,
        }
        return render(request, "admin/notifications/send_notification.html", context)
