from django.urls import path
from . import views

urlpatterns = [
    path('momo/initiate/', views.initiate_payment, name='initiate-payment'),
    path('momo/status/<str:transaction_id>/', views.check_payment_status, name='check-payment-status'),
]
