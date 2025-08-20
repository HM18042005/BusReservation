from django.urls import path
from . import views

app_name = 'bus_management'

urlpatterns = [
    # Make login the default page for non-authenticated users
    path('', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('signup/', views.admin_signup, name='admin_signup'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('buses/', views.manage_buses, name='manage_buses'),
    path('bookings/', views.manage_bookings, name='manage_bookings'),
    path('reports/', views.generate_report, name='generate_report'),
    path('users/', views.manage_users, name='manage_users'),
    path('reviews/', views.manage_reviews, name='manage_reviews'),
]