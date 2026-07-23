from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ContactForm


class ContactView(CreateView):
    form_class = ContactForm
    template_name = "contact/contact.html"
    success_url = reverse_lazy("contact:contact")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Message sent — we'll be in touch soon.")
        return response
