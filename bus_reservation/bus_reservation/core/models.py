from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        # Normalize staff flag to our model's is_admin field
        if 'is_staff' in extra_fields:
            # Accept is_staff as an alias and map it to is_admin
            is_staff_val = bool(extra_fields.pop('is_staff'))
            # Do not overwrite explicit is_admin if already provided
            extra_fields.setdefault('is_admin', is_staff_val)

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        # Ensure both flags align for compatibility
        extra_fields.setdefault('is_admin', True)
        extra_fields.pop('is_staff', None)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']
    
    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return self.is_admin
    
    @property
    def is_staff(self):
        return self.is_admin

class Bus(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    
    bus_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bus_number = models.CharField(max_length=20)
    bus_type = models.CharField(max_length=50)
    total_seats = models.IntegerField()
    origin_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    duration = models.DurationField()
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    def __str__(self):
        return f"{self.bus_number} - {self.origin_city} to {self.destination_city}"

class Seat(models.Model):
    SEAT_TYPE_CHOICES = (
        ('window', 'Window'),
        ('aisle', 'Aisle'),
        ('middle', 'Middle'),
    )
    
    SEAT_STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),
    )
    
    seat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats', null=True, blank=True)
    seat_number = models.CharField(max_length=10)
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES, default='window')
    row = models.IntegerField(default=0)
    column = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=SEAT_STATUS_CHOICES, default='available')
    is_booked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('bus', 'seat_number')
    
    def __str__(self):
        return f"{self.bus.bus_number if self.bus else 'No Bus'} - Seat {self.seat_number}"

class BusSchedule(models.Model):
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    date = models.DateField()
    
    class Meta:
        unique_together = ('bus', 'date')
    
    def __str__(self):
        return f"{self.bus.bus_number} on {self.date}"

class SeatAvailability(models.Model):
    availability_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(BusSchedule, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('schedule', 'seat')
    
    def __str__(self):
        return f"{self.schedule.bus.bus_number} - Seat {self.seat.seat_number} on {self.schedule.date}"

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pnr_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.ForeignKey(BusSchedule, on_delete=models.CASCADE, null=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return self.pnr_number

class BookingSeat(models.Model):
    booking_seat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='seats')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    passenger_name = models.CharField(max_length=100)
    passenger_age = models.IntegerField()
    passenger_gender = models.CharField(max_length=10)
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('booking', 'seat')
    
    def __str__(self):
        return f"{self.booking.pnr_number} - {self.seat.seat_number}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('razorpay', 'Razorpay'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Razorpay specific fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return self.transaction_id

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Review by {self.user.email} for {self.booking.pnr_number}"