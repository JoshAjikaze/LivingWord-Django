from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import CreateView

from .forms import SubscriberForm


class SubscribeView(CreateView):
    form_class = SubscriberForm
    http_method_names = ["post"]

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "You're on the list — thanks for joining.")
        return redirect(self.request.META.get("HTTP_REFERER", "core:home"))

    def form_invalid(self, form):
        messages.error(self.request, "That didn't look like a valid email — mind trying again?")
        return redirect(self.request.META.get("HTTP_REFERER", "core:home"))
