from django.contrib import admin
from .models import User, StrayAnimalReport, VeterinaryConsultation, AnimalAdoption, LoginHistory

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'user_type', 'district', 'is_active', 'created_at']
    list_filter = ['user_type', 'district', 'is_active']
    search_fields = ['username', 'email']

@admin.register(StrayAnimalReport)
class StrayAnimalReportAdmin(admin.ModelAdmin):
    list_display = ['animal_type', 'location', 'status', 'district', 'reporter', 'reported_date']
    list_filter = ['animal_type', 'status', 'district']
    search_fields = ['location', 'description']

@admin.register(VeterinaryConsultation)
class VeterinaryConsultationAdmin(admin.ModelAdmin):
    list_display = ['animal', 'requested_by', 'veterinarian', 'consultation_status', 'requested_date']
    list_filter = ['consultation_status', 'requested_date']

@admin.register(AnimalAdoption)
class AnimalAdoptionAdmin(admin.ModelAdmin):
    list_display = ['animal', 'adopter', 'care_center', 'adoption_status', 'requested_date']
    list_filter = ['adoption_status', 'requested_date']

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'ip_address']
    list_filter = ['login_time']
    search_fields = ['user__username']