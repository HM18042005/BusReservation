from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import SignUpForm, LoginForm, BusSearchForm, ContactForm
from .models import User, Bus, Booking, BookingSeat, Payment, Review, Seat, BusSchedule, SeatAvailability
import uuid
from django.utils import timezone
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
import json
from django.db.models import Max, Avg
import razorpay
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.views.generic import ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta, datetime
import random
import string
from django.db import models

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def home(request):
    form = BusSearchForm()
    buses = None
    search_params = {}
    
    if request.method == 'POST':
        form = BusSearchForm(request.POST)
        if form.is_valid():
            origin = form.cleaned_data.get('origin').strip()
            destination = form.cleaned_data.get('destination').strip()
            travel_date = form.cleaned_data.get('travel_date')
            passengers = form.cleaned_data.get('passengers')
            
            # Get all buses first
            buses = Bus.objects.all()
            
            # Filter by status (case insensitive)
            buses = buses.filter(status__iexact='Active')
            
            # Filter by origin and destination (case insensitive)
            if origin:
                buses = buses.filter(origin_city__iexact=origin)
            if destination:
                buses = buses.filter(destination_city__iexact=destination)
            
            # If no exact matches found, try partial matches
            if not buses.exists() and origin:
                buses = Bus.objects.filter(
                    status__iexact='Active',
                    origin_city__iexact=origin
                )
            
            search_params = {
                'origin': origin,
                'destination': destination,
                'travel_date': travel_date,
                'passengers': passengers
            }
            
            # Print debug info
            print(f"Search for - Origin: {origin}, Destination: {destination}")
            print(f"Found buses: {buses.values('bus_number', 'origin_city', 'destination_city', 'status')}")
    
    return render(request, 'index.html', {
        'form': form,
        'buses': buses,
        'search_params': search_params
    })

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Successfully logged in.')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def search_buses(request):
    if request.method == 'POST':
        form = BusSearchForm(request.POST)
        if form.is_valid():
            origin = form.cleaned_data.get('origin').strip()
            destination = form.cleaned_data.get('destination').strip()
            travel_date = form.cleaned_data.get('travel_date')
            passengers = form.cleaned_data.get('passengers')
            
            # Get all active buses
            buses = Bus.objects.filter(status='Active')
            
            # Filter by origin and destination
            if origin:
                buses = buses.filter(origin_city__iexact=origin)
            if destination:
                buses = buses.filter(destination_city__iexact=destination)
            
            return render(request, 'search.html', {
                'form': form,
                'buses': buses,
                'search_date': travel_date,
                'passengers': passengers
            })
    else:
        form = BusSearchForm()
    
    return render(request, 'search.html', {'form': form})

@login_required
def select_seats(request, bus_id):
    try:
        bus = Bus.objects.get(bus_id=bus_id)
        travel_date = request.GET.get('date')
        passengers = int(request.GET.get('passengers', 1))
        
        if not travel_date:
            messages.error(request, 'Please select a travel date.')
            return redirect('search_buses')
        
        # Get or create bus schedule
        schedule, _ = BusSchedule.objects.get_or_create(
            bus=bus,
            date=travel_date
        )
        
        # Get all seats for this bus
        seats = Seat.objects.filter(bus=bus).order_by('row', 'column')
        
        # Get seat availability for this schedule
        seat_availability = SeatAvailability.objects.filter(schedule=schedule)
        available_seats = {sa.seat_id: sa.is_available for sa in seat_availability}
        
        # Create seat layout matrix
        max_row = seats.aggregate(Max('row'))['row__max'] or 0
        max_col = seats.aggregate(Max('column'))['column__max'] or 0
        seat_layout = [[None for _ in range(max_col + 1)] for _ in range(max_row + 1)]
        
        for seat in seats:
            status = 'available'
            if seat.seat_id in available_seats:
                if not available_seats[seat.seat_id]:
                    status = 'booked'
            seat_layout[seat.row][seat.column] = {
                'seat_id': seat.seat_id,
                'seat_number': seat.seat_number,
                'seat_type': seat.seat_type,
                'status': status
            }
        
        return render(request, 'seats.html', {
            'bus': bus,
            'travel_date': travel_date,
            'passengers': passengers,
            'seat_layout': seat_layout
        })
        
    except Bus.DoesNotExist:
        messages.error(request, 'Bus not found.')
        return redirect('search_buses')

@login_required
def book_ticket(request, bus_id):
    try:
        bus = Bus.objects.get(bus_id=bus_id)
        travel_date = request.POST.get('travel_date')
        selected_seats = json.loads(request.POST.get('selected_seats', '[]'))
        
        if not travel_date or not selected_seats:
            messages.error(request, 'Please select seats and travel date.')
            return redirect('select_seats', bus_id=bus_id)
        
        # Get or create schedule
        schedule, _ = BusSchedule.objects.get_or_create(
            bus=bus,
            date=travel_date
        )
        
        # Verify seat availability
        seats = Seat.objects.filter(seat_id__in=selected_seats)
        if seats.count() != len(selected_seats):
            messages.error(request, 'Some selected seats were not found.')
            return redirect('select_seats', bus_id=bus_id)
            
        seat_availability = SeatAvailability.objects.filter(
            schedule=schedule,
            seat__in=seats,
            is_available=False
        )
        
        if seat_availability.exists():
            messages.error(request, 'Some selected seats are no longer available.')
            return redirect('select_seats', bus_id=bus_id)
        
        # Calculate total amount
        total_amount = bus.fare * seats.count()
        
        # Create booking
        booking = Booking.objects.create(
            pnr_number=f"PNR{uuid.uuid4().hex[:8].upper()}",
            user=request.user,
            schedule=schedule,
            total_amount=total_amount,
            status='pending'
        )
        
        # Create booking seats and update availability
        for seat in seats:
            BookingSeat.objects.create(
                booking=booking,
                seat=seat,
                passenger_name='',  # Will be filled in next step
                passenger_age=0,    # Will be filled in next step
                passenger_gender='', # Will be filled in next step
                fare=bus.fare
            )
            
            # Update seat availability
            SeatAvailability.objects.update_or_create(
                schedule=schedule,
                seat=seat,
                defaults={'is_available': False}
            )
        
        return render(request, 'bookings.html', {
            'booking': booking,
            'seats': seats,
            'travel_date': travel_date
        })
        
    except Bus.DoesNotExist:
        messages.error(request, 'Bus not found.')
        return redirect('search_buses')
    except json.JSONDecodeError:
        messages.error(request, 'Invalid seat selection.')
        return redirect('select_seats', bus_id=bus_id)

@login_required
def confirm_booking(request, bus_id):
    if request.method == 'POST':
        try:
            bus = Bus.objects.get(bus_id=bus_id)
            travel_date = request.POST.get('travel_date')
            passengers = int(request.POST.get('passengers', 1))
            
            # Create booking
            booking = Booking.objects.create(
                pnr_number=f"PNR{uuid.uuid4().hex[:8].upper()}",
                user=request.user,
                bus=bus,
                travel_date=travel_date,
                total_amount=bus.fare * passengers,
                status='pending'
            )
            
            # Create booking seats
            for i in range(passengers):
                BookingSeat.objects.create(
                    booking=booking,
                    seat=Seat.objects.get(seat_number=f"{i+1}"),
                    passenger_name=request.POST.get(f'passenger_name_{i}'),
                    passenger_age=request.POST.get(f'passenger_age_{i}'),
                    passenger_gender=request.POST.get(f'passenger_gender_{i}'),
                    fare=bus.fare
                )
            
            return redirect('payment', booking_id=booking.booking_id)
            
        except Exception as e:
            messages.error(request, f'Error creating booking: {str(e)}')
            return redirect('search_buses')
    
    return redirect('search_buses')

@login_required
def payment(request, booking_id):
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        
        # If payment is already completed, redirect to confirmation
        if booking.status == 'confirmed':
            return redirect('confirmation', booking_id=booking.booking_id)
        
        # Calculate amount in paisa (Razorpay uses smallest currency unit)
        amount_in_paise = int(float(booking.total_amount) * 100)
        
        # Create Razorpay order if not already created
        if not hasattr(booking, 'payment') or not booking.payment.razorpay_order_id:
            order_data = {
                'amount': amount_in_paise,
                'currency': settings.RAZORPAY_CURRENCY,
                'receipt': str(booking.booking_id),
            }
            razorpay_order = razorpay_client.order.create(data=order_data)
            
            # Create or update payment record
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': booking.total_amount,
                    'payment_method': 'razorpay',
                    'transaction_id': f"TXN{uuid.uuid4().hex[:8].upper()}",
                    'razorpay_order_id': razorpay_order['id'],
                }
            )
            
            if not created:
                payment.razorpay_order_id = razorpay_order['id']
                payment.save()
        else:
            payment = booking.payment
        
        # Prepare context for the template
        context = {
            'booking': booking,
            'payment': payment,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': payment.razorpay_order_id,
            'amount_in_paise': amount_in_paise,
            'currency': settings.RAZORPAY_CURRENCY,
            'company_name': settings.RAZORPAY_COMPANY_NAME,
            'description': settings.RAZORPAY_DESCRIPTION,
            'user_email': request.user.email,
            'user_name': f"{request.user.first_name} {request.user.last_name}",
            'callback_url': request.build_absolute_uri(reverse('payment_callback')),
        }
        
        return render(request, 'payment.html', context)
        
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('dashboard')

@csrf_exempt
def payment_callback(request):
    """Handle Razorpay payment callback"""
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')
        
        # Verify the payment signature
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            # Verify signature
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Find payment by order ID
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                
                # Update payment details
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.status = 'completed'
                payment.save()
                
                # Update booking status
                booking = payment.booking
                booking.status = 'confirmed'
                booking.save()
                
                # Redirect to confirmation page
                return redirect('confirmation', booking_id=booking.booking_id)
                
            except Payment.DoesNotExist:
                return HttpResponse("Payment not found", status=400)
                
        except razorpay.errors.SignatureVerificationError:
            # Signature verification failed
            return HttpResponse("Payment verification failed", status=400)
    
    return HttpResponse("Invalid request", status=400)

@login_required
def payment_success(request, booking_id):
    """Handle successful payment redirection"""
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        if booking.status == 'confirmed':
            return redirect('confirmation', booking_id=booking.booking_id)
        else:
            messages.error(request, 'Payment not completed.')
            return redirect('payment', booking_id=booking.booking_id)
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('dashboard')

@login_required
def confirmation(request, booking_id):
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        return render(request, 'confirmation.html', {'booking': booking})
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('dashboard')

@login_required
def dashboard(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-booking_date')
    context = {
        'user': user,
        'bookings': bookings,
        'total_bookings': bookings.count(),
        'active_bookings': bookings.filter(status='confirmed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
    }
    return render(request, 'dashboard.html', context)

@login_required
def review(request, booking_id):
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        if request.method == 'POST':
            # Check if a review already exists for this booking
            existing_review = Review.objects.filter(booking=booking).first()
            
            # Extract form data
            rating = request.POST.get('rating')
            review_text = request.POST.get('review_text')
            
            # Debug info
            print(f"Review submission - Booking ID: {booking_id}, Rating: {rating}, Text length: {len(review_text)}")
            
            if existing_review:
                # Update existing review
                existing_review.rating = rating
                existing_review.review_text = review_text
                existing_review.save()
                messages.success(request, 'Review updated successfully.')
                print("Updated existing review")
            else:
                # Create new review
                new_review = Review.objects.create(
                    user=request.user,
                    booking=booking,
                    rating=rating,
                    review_text=review_text
                )
                messages.success(request, 'Review submitted successfully.')
                print(f"Created new review with ID: {new_review.review_id}")
            
            # Use HttpResponseRedirect for more reliable redirects
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse('dashboard'))
            
        return render(request, 'review.html', {'booking': booking})
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('dashboard')
    
def about_us(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Prepare email content
            email_content = f"""
            New Contact Form Submission
            
            Name: {name}
            Email: {email}
            Subject: {subject}
            
            Message:
            {message}
            """
            
            try:
                # Send email
                send_mail(
                    subject=f'Contact Form: {subject}',
                    message=email_content,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for your message. We will get back to you soon!')
            except Exception as e:
                messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
                print(f"Email error: {str(e)}")  # For debugging
            
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out.')
    return redirect('home')

@login_required
def update_passenger_details(request, booking_id):
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        
        if request.method == 'POST':
            # Update passenger details for each booked seat
            booking_seats = BookingSeat.objects.filter(booking=booking)
            
            for i, booking_seat in enumerate(booking_seats):
                booking_seat.passenger_name = request.POST.get(f'passenger_name_{i}', '')
                booking_seat.passenger_age = int(request.POST.get(f'passenger_age_{i}', 0))
                booking_seat.passenger_gender = request.POST.get(f'passenger_gender_{i}', '')
                booking_seat.save()
            
            # Redirect to payment page
            return redirect('payment', booking_id=booking.booking_id)
        
        return redirect('dashboard')
        
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('dashboard')

def all_reviews(request):
    """View to display all reviews with pagination"""
    reviews_list = Review.objects.select_related('user', 'booking', 'booking__schedule', 'booking__schedule__bus').order_by('-created_at')
    
    paginator = Paginator(reviews_list, 8)  # Show 8 reviews per page
    page = request.GET.get('page')
    
    try:
        reviews = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        reviews = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page
        reviews = paginator.page(paginator.num_pages)
    
    return render(request, 'all_reviews.html', {
        'reviews': reviews,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': reviews
    })

def bus_reviews(request, bus_id):
    bus = get_object_or_404(Bus, bus_id=bus_id)
    reviews = Review.objects.filter(booking__schedule__bus=bus, is_visible=True).order_by('-created_at')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    total_reviews = reviews.count()
    
    # Pagination
    page = request.GET.get('page')
    paginator = Paginator(reviews, 5)  # Show 5 reviews per page
    try:
        reviews = paginator.page(page)
    except PageNotAnInteger:
        reviews = paginator.page(1)
    except EmptyPage:
        reviews = paginator.page(paginator.num_pages)
    
    # Get search parameters from request
    search_params = {
        'origin': request.GET.get('origin', ''),
        'destination': request.GET.get('destination', ''),
        'travel_date': request.GET.get('travel_date', timezone.now().date()),
        'passengers': request.GET.get('passengers', 1)
    }
    
    context = {
        'bus': bus,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
        'today': timezone.now().date(),
        'search_params': search_params
    }
    return render(request, 'bus_reviews.html', context) 