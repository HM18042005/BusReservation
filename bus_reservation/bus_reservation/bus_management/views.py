from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum
from datetime import datetime, timedelta
import json
from core.models import Bus, Booking, Review
from django.conf import settings
from .models import AdminLog, Report, AdminSettings
from django.contrib.admin.views.decorators import staff_member_required

def is_admin(user):
    return user.is_authenticated and user.is_staff

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('bus_management:admin_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please provide both email and password')
            return render(request, 'bus_management/login.html')
            
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_staff:
                login(request, user)
                messages.success(request, 'Successfully logged in')
                return redirect('bus_management:admin_dashboard')
            else:
                messages.error(request, 'This account does not have admin privileges')
        else:
            messages.error(request, 'Invalid email or password')
            
    return render(request, 'bus_management/login.html')

def admin_signup(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('bus_management:admin_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'bus_management/signup.html')
            
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'bus_management/signup.html')
            
        user = User.objects.create_user(
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_staff=True
        )
        
        login(request, user)
        messages.success(request, 'Admin account created successfully')
        return redirect('bus_management:admin_dashboard')
        
    return render(request, 'bus_management/signup.html')

@staff_member_required(login_url='bus_management:admin_login')
def admin_dashboard(request):
    User = get_user_model()
    context = {
        'total_buses': Bus.objects.count(),
        'total_bookings': Booking.objects.count(),
        'total_users': User.objects.count(),
        'total_reviews': Review.objects.count(),
        'recent_bookings': Booking.objects.order_by('-booking_date')[:5],
        'recent_reviews': Review.objects.order_by('-created_at')[:5],
    }
    return render(request, 'bus_management/dashboard.html', context)

@staff_member_required
def manage_buses(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            try:
                # Parse duration string to timedelta
                duration_str = request.POST.get('duration')
                hours, minutes = map(int, duration_str.split(':'))
                duration = timedelta(hours=hours, minutes=minutes)
                
                Bus.objects.create(
                    bus_number=request.POST.get('bus_number'),
                    bus_type=request.POST.get('bus_type'),
                    total_seats=request.POST.get('total_seats'),
                    origin_city=request.POST.get('origin_city'),
                    destination_city=request.POST.get('destination_city'),
                    departure_time=request.POST.get('departure_time'),
                    arrival_time=request.POST.get('arrival_time'),
                    duration=duration,
                    distance=request.POST.get('distance'),
                    fare=request.POST.get('fare'),
                    status=request.POST.get('status')
                )
                messages.success(request, 'Bus added successfully.')
            except Exception as e:
                messages.error(request, f'Error adding bus: {str(e)}')
                
        elif action == 'edit':
            try:
                bus = Bus.objects.get(bus_id=request.POST.get('bus_id'))
                
                # Parse duration string to timedelta
                duration_str = request.POST.get('duration')
                hours, minutes = map(int, duration_str.split(':'))
                duration = timedelta(hours=hours, minutes=minutes)
                
                bus.bus_number = request.POST.get('bus_number')
                bus.bus_type = request.POST.get('bus_type')
                bus.total_seats = request.POST.get('total_seats')
                bus.origin_city = request.POST.get('origin_city')
                bus.destination_city = request.POST.get('destination_city')
                bus.departure_time = request.POST.get('departure_time')
                bus.arrival_time = request.POST.get('arrival_time')
                bus.duration = duration
                bus.distance = request.POST.get('distance')
                bus.fare = request.POST.get('fare')
                bus.status = request.POST.get('status')
                bus.save()
                
                messages.success(request, 'Bus updated successfully.')
            except Bus.DoesNotExist:
                messages.error(request, 'Bus not found.')
            except Exception as e:
                messages.error(request, f'Error updating bus: {str(e)}')
                
        elif action == 'delete':
            try:
                bus = Bus.objects.get(bus_id=request.POST.get('bus_id'))
                bus.delete()
                messages.success(request, 'Bus deleted successfully.')
            except Bus.DoesNotExist:
                messages.error(request, 'Bus not found.')
            except Exception as e:
                messages.error(request, f'Error deleting bus: {str(e)}')
        
        return redirect('bus_management:manage_buses')
    
    buses = Bus.objects.all().order_by('bus_number')
    return render(request, 'bus_management/manage_buses.html', {'buses': buses})

@staff_member_required
def manage_bookings(request):
    if request.method == 'POST':
        try:
            booking = Booking.objects.get(booking_id=request.POST.get('booking_id'))
            action = request.POST.get('action')
            
            if action == 'confirm':
                booking.status = 'confirmed'
                messages.success(request, 'Booking confirmed successfully.')
                # Add logging
                AdminLog.objects.create(
                    admin=request.user,
                    action=f"Confirmed booking {booking.pnr_number}",
                    details=f"Booking ID: {booking.booking_id}"
                )
            elif action == 'cancel':
                booking.status = 'cancelled'
                messages.success(request, 'Booking cancelled successfully.')
                # Add logging
                AdminLog.objects.create(
                    admin=request.user,
                    action=f"Cancelled booking {booking.pnr_number}",
                    details=f"Booking ID: {booking.booking_id}"
                )
            
            booking.save()
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
        except Exception as e:
            messages.error(request, f'Error updating booking: {str(e)}')
        
        return redirect('bus_management:manage_bookings')
    
    bookings = Booking.objects.all().order_by('-booking_date')
    return render(request, 'bus_management/manage_bookings.html', {'bookings': bookings})

@staff_member_required
def generate_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        data = {}
        report_headers = []
        report_data = []
        
        if report_type == 'booking':
            bookings = Booking.objects.filter(
                booking_date__range=[start_date, end_date]
            ).values('status').annotate(count=Count('booking_id'))
            report_headers = ['Status', 'Count']
            report_data = [[b['status'], b['count']] for b in bookings]
        
        elif report_type == 'revenue':
            revenue = Booking.objects.filter(
                booking_date__range=[start_date, end_date],
                status='confirmed'
            ).aggregate(total=Sum('total_amount'))
            report_headers = ['Period', 'Total Revenue']
            report_data = [[f"{start_date} to {end_date}", revenue['total'] or 0]]
        
        elif report_type == 'user':
            User = get_user_model()
            users = User.objects.annotate(
                booking_count=Count('booking')
            ).values('email', 'booking_count')
            report_headers = ['Email', 'Total Bookings']
            report_data = [[u['email'], u['booking_count']] for u in users]
            
        # Create report record
        report = Report.objects.create(
            report_type=report_type.upper(),
            generated_by=request.user,
            data={'headers': report_headers, 'data': report_data}
        )
        
        # Return HTML response
        context = {
            'report_headers': report_headers,
            'report_data': report_data,
            'report': report
        }
        return render(request, 'bus_management/generate_report.html', context)
        
    return render(request, 'bus_management/generate_report.html')

@staff_member_required
def manage_users(request):
    User = get_user_model()
    users = User.objects.all()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            user = User.objects.get(user_id=user_id)
            
            if action == 'deactivate':
                user.is_active = False
                user.save()
                messages.success(request, f'User {user.email} has been deactivated successfully')
            elif action == 'activate':
                user.is_active = True
                user.save()
                messages.success(request, f'User {user.email} has been activated successfully')
            elif action == 'edit':
                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.phone = request.POST.get('phone')
                user.save()
                messages.success(request, f'User {user.email} has been updated successfully')
                
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
        return redirect('bus_management:manage_users')
        
    return render(request, 'bus_management/manage_users.html', {'users': users})

@staff_member_required
def manage_reviews(request):
    reviews = Review.objects.all().order_by('-created_at')
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        action = request.POST.get('action')
        review = get_object_or_404(Review, review_id=review_id)
        
        if action == 'delete':
            review.delete()
            messages.success(request, 'Review deleted successfully')
        elif action == 'hide':
            review.is_visible = False
            review.save()
            messages.success(request, 'Review hidden successfully')
        elif action == 'show':
            review.is_visible = True
            review.save()
            messages.success(request, 'Review shown successfully')
            
        return redirect('bus_management:manage_reviews')
    return render(request, 'bus_management/manage_reviews.html', {'reviews': reviews})

def admin_logout(request):
    logout(request)
    messages.success(request, 'Successfully logged out')
    return redirect('bus_management:admin_login')
