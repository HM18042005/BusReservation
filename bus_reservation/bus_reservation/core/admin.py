from django.contrib import admin
from .models import User, Bus, Booking, Seat, BookingSeat, Payment, Review, BusSchedule, SeatAvailability

class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_id', 'bus_number', 'bus_type', 'total_seats', 'origin_city', 'destination_city', 'departure_time', 'arrival_time', 'duration', 'distance', 'fare', 'status')
    search_fields = ('bus_number', 'bus_type', 'origin_city', 'destination_city')
    list_filter = ('bus_type', 'status')

class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'pnr_number', 'user', 'get_bus', 'get_travel_date', 'booking_date', 'total_amount', 'status')
    search_fields = ('pnr_number', 'user__email')
    list_filter = ('status', 'schedule__date')
    
    def get_bus(self, obj):
        return obj.schedule.bus
    get_bus.short_description = 'Bus'
    
    def get_travel_date(self, obj):
        return obj.schedule.date
    get_travel_date.short_description = 'Travel Date'

class BusScheduleAdmin(admin.ModelAdmin):
    list_display = ('schedule_id', 'bus', 'date')
    search_fields = ('bus__bus_number',)
    list_filter = ('date',)

class SeatAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('availability_id', 'schedule', 'seat', 'is_available')
    search_fields = ('schedule__bus__bus_number', 'seat__seat_number')
    list_filter = ('is_available',)

class BookingSeatAdmin(admin.ModelAdmin):
    list_display = ('booking_seat_id', 'booking', 'seat', 'passenger_name', 'passenger_age', 'passenger_gender', 'fare')
    search_fields = ('booking__pnr_number', 'passenger_name')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'booking', 'amount', 'payment_method', 'transaction_id', 'payment_date', 'status')
    search_fields = ('transaction_id', 'booking__pnr_number')
    list_filter = ('payment_method', 'status')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('review_id', 'user', 'booking', 'rating', 'created_at')
    search_fields = ('user__email', 'booking__pnr_number')
    list_filter = ('rating', 'created_at')

class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_id', 'bus', 'seat_number', 'seat_type', 'row', 'column', 'status', 'is_booked')
    search_fields = ('bus__bus_number', 'seat_number')
    list_filter = ('seat_type', 'status', 'is_booked')

admin.site.register(User)
admin.site.register(Bus, BusAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Seat, SeatAdmin)
admin.site.register(BookingSeat, BookingSeatAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(BusSchedule, BusScheduleAdmin)
admin.site.register(SeatAvailability, SeatAvailabilityAdmin)