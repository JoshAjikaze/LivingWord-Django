from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("paypal/create/<slug:slug>/", views.create_paypal_order, name="paypal_create"),
    path("paypal/capture/<str:paypal_order_id>/", views.capture_paypal_order, name="paypal_capture"),
    path("paypal/webhook/", views.paypal_webhook, name="paypal_webhook"),
]
