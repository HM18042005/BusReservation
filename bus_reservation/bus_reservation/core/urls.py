from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_buses, name='search_buses'),
    path('select-seats/<uuid:bus_id>/', views.select_seats, name='select_seats'),
    path('book/<uuid:bus_id>/', views.book_ticket, name='book_ticket'),
    path('confirm/<uuid:bus_id>/', views.confirm_booking, name='confirm_booking'),
    path('payment/<uuid:booking_id>/', views.payment, name='payment'),
    path('update-passenger-details/<uuid:booking_id>/', views.update_passenger_details, name='update_passenger_details'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('payment-success/<uuid:booking_id>/', views.payment_success, name='payment_success'),
    path('confirmation/<uuid:booking_id>/', views.confirmation, name='confirmation'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('review/<uuid:booking_id>/', views.review, name='review'),
    path('reviews/', views.all_reviews, name='all_reviews'),
    path('bus/<uuid:bus_id>/reviews/', views.bus_reviews, name='bus_reviews'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about_us, name='about'),
]