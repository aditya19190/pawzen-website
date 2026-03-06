from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# District choices
DISTRICT_CHOICES = [
    ('Ernakulam', 'Ernakulam'),
    ('Thrissur', 'Thrissur'),
]

ANIMAL_TYPE_CHOICES = [
    ('Dog', 'Dog'),
    ('Cat', 'Cat'),
]

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Completed', 'Completed'),
]

HEALTH_STATUS_CHOICES = [
    ('Reported', 'Reported'),
    ('Under Care', 'Under Care'),
    ('Healthy', 'Healthy'),
    ('Adopted', 'Adopted'),
]


# Custom User Model
class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Username can contain letters, numbers, spaces, and @/./+/-/_ characters.',
        validators=[],  # Remove default validators to allow spaces
        error_messages={
            'unique': "A user with that username already exists.",
        },
    ) 
    USER_TYPE_CHOICES = [
        ('user', 'User'),
        ('care_center', 'Care Center'),
        ('veterinarian', 'Veterinarian'),
        ('admin', 'Admin'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    # Care Center specific fields
    care_center_name = models.CharField(max_length=200, null=True, blank=True)
    license_number = models.CharField(max_length=100, null=True, blank=True)
    
    # Veterinarian specific fields
    veterinarian_name = models.CharField(max_length=200, null=True, blank=True)
    qualification = models.CharField(max_length=200, null=True, blank=True)
    specialization = models.CharField(max_length=200, null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"


# Stray Animal Report Model
class StrayAnimalReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_animals')
    animal_type = models.CharField(max_length=20, choices=ANIMAL_TYPE_CHOICES)
    location = models.TextField()
    description = models.TextField()
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES)
    care_center_notified = models.BooleanField(default=False)
    
    # Status tracking
    status = models.CharField(max_length=20, default='Reported', choices=HEALTH_STATUS_CHOICES)
    taken_by_care_center = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='taken_animals',
        limit_choices_to={'user_type': 'care_center'}
    )
    
    reported_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notification_seen = models.BooleanField(default=False)
    reported_image = models.ImageField(upload_to='reported_animals/', null=True, blank=True)
    healthy_image = models.ImageField(upload_to='healthy_animals/', null=True, blank=True)

    def __str__(self):
        return f"{self.animal_type} - {self.location[:50]}"
    
    class Meta:
        ordering = ['-reported_date']


class VeterinaryConsultation(models.Model):
    CONSULTATION_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]
    
    ANIMAL_TYPE_CHOICES = [
        ('Dog', 'Dog'),
        ('Cat', 'Cat'),
    ]
    
    # For care center consultations - link to reported animal
    animal = models.ForeignKey(
        StrayAnimalReport, 
        on_delete=models.CASCADE, 
        related_name='consultations',
        null=True,
        blank=True
    )
    
    # For user direct consultations - just animal type
    animal_type = models.CharField(
        max_length=50, 
        choices=ANIMAL_TYPE_CHOICES,
        null=True,
        blank=True
    )
    
    # Description for user consultations
    animal_description = models.TextField(null=True, blank=True)

    consultation_image = models.ImageField(upload_to='consultation_images/', null=True, blank=True)
    
    veterinarian = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='consultations_as_vet',
        limit_choices_to={'user_type': 'veterinarian'}
    )
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='consultation_requests'
    )
    request_description = models.TextField()
    treatment_details = models.TextField(blank=True, null=True)
    consultation_status = models.CharField(
        max_length=20, 
        choices=CONSULTATION_STATUS_CHOICES, 
        default='Pending'
    )
    requested_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.animal:
            return f"Consultation for {self.animal.animal_type} - {self.consultation_status}"
        else:
            return f"Direct Consultation for {self.animal_type} - {self.consultation_status}"

    class Meta:
        ordering = ['-requested_date']


# Animal Adoption Model
class AnimalAdoption(models.Model):
    animal = models.ForeignKey(StrayAnimalReport, on_delete=models.CASCADE, related_name='adoption_requests')
    adopter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='adopted_animals')
    care_center = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='animals_given_for_adoption',
        limit_choices_to={'user_type': 'care_center'}
    )
    
    adoption_status = models.CharField(max_length=20, default='Pending', choices=STATUS_CHOICES)
    adoption_date = models.DateTimeField(null=True, blank=True)
    adopter_reason = models.TextField()
    notification_seen = models.BooleanField(default=False)
    
    requested_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.animal.animal_type} - {self.adopter.username}"
    
    class Meta:
        ordering = ['-requested_date']


# Login History Model
class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
    
    class Meta:
        ordering = ['-login_time']