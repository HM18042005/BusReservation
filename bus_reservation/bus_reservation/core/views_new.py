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
from django.db.models import Max

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
        seat_availability = SeatAvailability.objects.filter(
            schedule=schedule,
            seat__in=seats,
            is_available=False
        )
        
        if seat_availability.exists():
            messages.error(request, 'Some selected seats are no longer available.')
            return redirect('select_seats', bus_id=bus_id)
        
        # Create booking
        booking = Booking.objects.create(
            pnr_number=f"PNR{uuid.uuid4().hex[:8].upper()}",
            user=request.user,
            schedule=schedule,
            total_amount=bus.fare * len(selected_seats)
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
        if request.method == 'POST':
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_amount,
                payment_method=request.POST.get('payment_method'),
                transaction_id=f"TXN{uuid.uuid4().hex[:8].upper()}",
                status='completed'
            )
            
            booking.status = 'confirmed'
            booking.save()
            
            return redirect('confirmation', booking_id=booking.booking_id)
            
        return render(request, 'payment.html', {'booking': booking})
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
            Review.objects.create(
                user=request.user,
                booking=booking,
                rating=request.POST.get('rating'),
                review_text=request.POST.get('review_text')
            )
            messages.success(request, 'Review submitted successfully.')
            return redirect('dashboard')
        return render(request, 'review.html', {'booking': booking})
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('dashboard')
    
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Message sent successfully.')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def about_us(request):
    return render(request, 'about.html')

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send email logic here
            send_mail(
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
                from_email=form.cleaned_data['email'],
                recipient_list=['supportbus123@gmail.com'],
            )
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out.')
    return redirect('home') 