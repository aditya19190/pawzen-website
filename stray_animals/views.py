from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .models import (
    User, StrayAnimalReport, VeterinaryConsultation,
    AnimalAdoption, LoginHistory
)
from .forms import (
    CareCenterRegistrationForm,
    VeterinarianRegistrationForm,
    VeterinarianProfileUpdateForm,
    RegistrationForm, 
    ReportAnimalForm,
    TreatmentDetailsForm,
    RequestConsultationForm,
    HealthyImageForm,
    CustomLoginForm,
    AnimalAdoptionForm,
)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def home(request):
    return render(request, 'home.html')


# ==================== USER MODULE ====================

def user_register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('user_login')
    else:
        form = RegistrationForm()
    return render(request, 'user/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'user/login.html', {'form': CustomLoginForm()})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.user_type == 'user':
                login(request, user)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('user_dashboard')
            else:
                messages.error(request, 'This account is not a user account.')
        else:
            messages.error(request, 'Invalid username or password.')

    form = CustomLoginForm()
    return render(request, 'user/login.html', {'form': form})


@login_required
def user_dashboard(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    reported_animals = StrayAnimalReport.objects.filter(reporter=request.user)
    consultation_requests = VeterinaryConsultation.objects.filter(requested_by=request.user)
    adopted_animals = AnimalAdoption.objects.filter(adopter=request.user)
    
    # Count UNREAD notifications only
    animal_unread = StrayAnimalReport.objects.filter(
        reporter=request.user,
        status__in=['Under Care', 'Healthy'],
        notification_seen=False
    ).count()
    
    adoption_unread = AnimalAdoption.objects.filter(
        adopter=request.user,
        adoption_status__in=['Approved', 'Rejected'],
        notification_seen=False
    ).count()
    
    unread_notifications = animal_unread + adoption_unread
    
    context = {
        'reported_animals': reported_animals,
        'consultation_requests': consultation_requests,
        'adopted_animals': adopted_animals,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'user/dashboard.html', context)


@login_required
def report_stray_animal(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ReportAnimalForm(request.POST, request.FILES)  # ADD request.FILES
        if form.is_valid():
            animal = form.save(commit=False)
            animal.reporter = request.user
            animal.save()
            messages.success(request, 'Animal reported successfully!')
            return redirect('user_dashboard')
    else:
        form = ReportAnimalForm()
    
    return render(request, 'user/report_animal.html', {'form': form})


@login_required
def view_adoption_animals(request):
    if request.user.user_type != 'user':
        return redirect('home')
    
    animals = StrayAnimalReport.objects.filter(
        status='Healthy',
        district=request.user.district
    ).exclude(adoption_requests__adoption_status='Completed')
    
    return render(request, 'user/adoption_list.html', {'animals': animals})


@login_required
def request_adoption(request, animal_id):
    if request.user.user_type != 'user':
        return redirect('home')
    
    animal = get_object_or_404(StrayAnimalReport, id=animal_id, status='Healthy')
    
    if AnimalAdoption.objects.filter(animal=animal, adoption_status='Completed').exists():
        messages.error(request, 'Already adopted.')
        return redirect('view_adoption_animals')
    
    if AnimalAdoption.objects.filter(animal=animal, adopter=request.user).exists():
        messages.error(request, 'You already requested this animal.')
        return redirect('view_adoption_animals')
    
    if request.method == 'POST':
        form = AnimalAdoptionForm(request.POST)
        if form.is_valid():
            adoption = form.save(commit=False)
            adoption.animal = animal
            adoption.adopter = request.user
            adoption.care_center = animal.taken_by_care_center
            adoption.save()
            messages.success(request, 'Adoption request submitted!')
            return redirect('user_dashboard')
    else:
        form = AnimalAdoptionForm()
    
    return render(request, 'user/request_adoption.html', {'form': form, 'animal': animal})


@login_required
def request_consultation_user(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    veterinarians = User.objects.filter(
        user_type='veterinarian',
        district=request.user.district
    )
    
    if request.method == 'POST':
        animal_type = request.POST.get('animal_type')
        animal_description = request.POST.get('animal_description')
        veterinarian_id = request.POST.get('veterinarian')
        request_description = request.POST.get('request_description')
        consultation_image = request.FILES.get('consultation_image')  # ADD THIS
        
        if not all([animal_type, animal_description, veterinarian_id, request_description]):
            messages.error(request, 'All fields except image are required.')
            return render(request, 'user/request_consultation.html', {'veterinarians': veterinarians})
        
        veterinarian = get_object_or_404(User, id=veterinarian_id, user_type='veterinarian')
        
        consultation = VeterinaryConsultation.objects.create(
            animal_type=animal_type,
            animal_description=animal_description,
            veterinarian=veterinarian,
            requested_by=request.user,
            request_description=request_description,
            consultation_image=consultation_image,  # ADD THIS
            consultation_status='Pending'
        )
        
        messages.success(request, f'Consultation request sent to Dr. {veterinarian.veterinarian_name}')
        return redirect('user_dashboard')
    
    context = {
        'veterinarians': veterinarians,
    }
    return render(request, 'user/request_consultation.html', context)


@login_required
def delete_user_account(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm')
        if confirm == 'DELETE':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Please type DELETE to confirm account deletion.')
            return redirect('user_dashboard')
    
    return render(request, 'user/delete_account.html')


# ==================== CARE CENTER MODULE ====================

def care_center_register(request):
    if request.method == 'POST':
        form = CareCenterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful!')
            return redirect('care_center_login')
    else:
        form = CareCenterRegistrationForm()
    return render(request, 'care_center/register.html', {'form': form})


def care_center_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'care_center/login.html', {'form': CustomLoginForm()})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.user_type == 'care_center':
                login(request, user)
                # Log login history
                LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.success(request, f'Welcome back, {user.care_center_name}!')
                return redirect('care_center_dashboard')
            else:
                messages.error(request, 'This account is not a care center account.')
        else:
            messages.error(request, 'Invalid username or password.')

    form = CustomLoginForm()
    return render(request, 'care_center/login.html', {'form': form})


@login_required
def care_center_dashboard(request):
    if request.user.user_type != 'care_center':
        return redirect('home')
    
    reported_animals = StrayAnimalReport.objects.filter(
        district=request.user.district, status='Reported'
    )
    taken_animals = StrayAnimalReport.objects.filter(taken_by_care_center=request.user)
    consultation_requests = VeterinaryConsultation.objects.filter(
        animal__taken_by_care_center=request.user
    )
    
    context = {
        'reported_animals': reported_animals,
        'taken_animals': taken_animals,
        'consultation_requests': consultation_requests,
    }
    return render(request, 'care_center/dashboard.html', context)


@login_required
def take_animal(request, animal_id):
    if request.user.user_type != 'care_center':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    animal = get_object_or_404(StrayAnimalReport, id=animal_id)
    
    if animal.district != request.user.district:
        messages.error(request, 'You can only take animals from your district.')
        return redirect('care_center_dashboard')
    
    if animal.status != 'Reported':
        messages.error(request, 'This animal has already been taken.')
        return redirect('care_center_dashboard')
    
    # Update animal status and assign to care center
    animal.status = 'Under Care'
    animal.taken_by_care_center = request.user
    animal.save()
    
    # Notification is automatic - user will see it when they check notifications
    # The animal record itself IS the notification
    
    messages.success(request, f'You have taken the {animal.animal_type}. The reporter will be notified.')
    return redirect('care_center_dashboard')


@login_required
def request_consultation_care_center(request, animal_id):
    if request.user.user_type != 'care_center':
        return redirect('home')
    
    animal = get_object_or_404(StrayAnimalReport, id=animal_id, taken_by_care_center=request.user)
    
    if request.method == 'POST':
        form = RequestConsultationForm(request.POST, district=request.user.district)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.animal = animal
            consultation.requested_by = request.user
            consultation.save()
            messages.success(request, 'Consultation requested!')
            return redirect('care_center_dashboard')
    else:
        form = RequestConsultationForm(district=request.user.district)
    
    return render(request, 'care_center/request_consultation.html', {'form': form, 'animal': animal})


@login_required
def view_veterinarians(request):
    if request.user.user_type != 'care_center':
        return redirect('home')
    
    veterinarians = User.objects.filter(
        user_type='veterinarian',
        district=request.user.district,
        is_active=True
    )
    
    return render(request, 'care_center/veterinarians.html', {'veterinarians': veterinarians})


@login_required
def manage_adoption_requests(request):
    if request.user.user_type != 'care_center':
        return redirect('home')
    
    adoption_requests = AnimalAdoption.objects.filter(care_center=request.user)
    
    return render(request, 'care_center/adoption_requests.html', {'adoption_requests': adoption_requests})


@login_required
def approve_adoption(request, adoption_id):
    if request.user.user_type != 'care_center':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    adoption = get_object_or_404(AnimalAdoption, id=adoption_id)
    
    if adoption.animal.taken_by_care_center != request.user:
        messages.error(request, 'You can only manage adoptions for animals in your care.')
        return redirect('manage_adoption_requests')
    
    # Approve the adoption
    adoption.adoption_status = 'Approved'
    adoption.save()
    
    # Update animal status to adopted
    animal = adoption.animal
    animal.status = 'Adopted'
    animal.save()
    
    # Notification is automatic - user will see it in notifications page
    
    messages.success(request, f'Adoption request approved for {adoption.adopter.username}')
    return redirect('manage_adoption_requests')


@login_required
def delete_care_center_account(request):
    if request.user.user_type != 'care_center':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm')
        if confirm == 'DELETE':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Please type DELETE to confirm account deletion.')
            return redirect('care_center_dashboard')
    
    return render(request, 'care_center/delete_account.html')


# ==================== VETERINARIAN MODULE ====================

def veterinarian_register(request):
    if request.method == 'POST':
        form = VeterinarianRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful!')
            return redirect('veterinarian_login')
    else:
        form = VeterinarianRegistrationForm()
    return render(request, 'veterinarian/register.html', {'form': form})


def veterinarian_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'veterinarian/login.html', {'form': CustomLoginForm()})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.user_type == 'veterinarian':
                login(request, user)
                LoginHistory.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.success(request, f'Welcome back, Dr. {user.veterinarian_name}!')
                return redirect('veterinarian_dashboard')
            else:
                messages.error(request, 'This account is not a veterinarian account.')
        else:
            messages.error(request, 'Invalid username or password.')

    form = CustomLoginForm()
    return render(request, 'veterinarian/login.html', {'form': form})


@login_required
def veterinarian_dashboard(request):
    if request.user.user_type != 'veterinarian':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get all consultations for this veterinarian (both types)
    all_consultations = VeterinaryConsultation.objects.filter(
        veterinarian=request.user
    ).select_related('requested_by', 'animal').order_by('-requested_date')
    
    pending_requests = all_consultations.filter(consultation_status='Pending')
    completed_requests = all_consultations.filter(consultation_status='Completed')
    
    context = {
        'all_consultations': all_consultations,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
    }
    return render(request, 'veterinarian/dashboard.html', context)


@login_required
def provide_treatment(request, consultation_id):
    if request.user.user_type != 'veterinarian':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    consultation = get_object_or_404(VeterinaryConsultation, id=consultation_id)
    
    if request.method == 'POST':
        form = TreatmentDetailsForm(request.POST, instance=consultation)
        if form.is_valid():
            consultation = form.save(commit=False)
            
            # If status changed to Completed
            if consultation.consultation_status == 'Completed':
                consultation.completed_date = timezone.now()
                
                # ONLY update animal status if this is a care center consultation (has animal)
                if consultation.animal:
                    animal = consultation.animal
                    animal.status = 'Healthy'
                    animal.save()
                
                # For user consultations (no animal), just save the consultation
            
            consultation.save()
            messages.success(request, 'Treatment details saved successfully!')
            return redirect('veterinarian_dashboard')
    else:
        form = TreatmentDetailsForm(instance=consultation)
    
    context = {
        'form': form,
        'consultation': consultation,
    }
    return render(request, 'veterinarian/provide_treatment.html', context)


@login_required
def update_veterinarian_profile(request):
    if request.user.user_type != 'veterinarian':
        return redirect('home')
    
    if request.method == 'POST':
        form = VeterinarianProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('veterinarian_dashboard')
    else:
        form = VeterinarianProfileUpdateForm(instance=request.user)
    
    return render(request, 'veterinarian/update_profile.html', {'form': form})


@login_required
def delete_veterinarian_account(request):
    if request.user.user_type != 'veterinarian':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        confirm = request.POST.get('confirm')
        if confirm == 'DELETE':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Please type DELETE to confirm account deletion.')
            return redirect('veterinarian_dashboard')
    
    return render(request, 'veterinarian/delete_account.html')


# ==================== ADMIN MODULE ====================


@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    total_users = User.objects.filter(user_type='user').count()
    total_care_centers = User.objects.filter(user_type='care_center').count()
    total_veterinarians = User.objects.filter(user_type='veterinarian').count()
    total_reported_animals = StrayAnimalReport.objects.count()
    total_adoptions = AnimalAdoption.objects.filter(adoption_status='Completed').count()
    
    context = {
        'total_users': total_users,
        'total_care_centers': total_care_centers,
        'total_veterinarians': total_veterinarians,
        'total_reported_animals': total_reported_animals,
        'total_adoptions': total_adoptions,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def admin_view_users(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    users = User.objects.filter(user_type='user')
    return render(request, 'admin/view_users.html', {'users': users})


@login_required
def admin_view_care_centers(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    care_centers = User.objects.filter(user_type='care_center')
    return render(request, 'admin/view_care_centers.html', {'care_centers': care_centers})


@login_required
def admin_view_veterinarians(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    veterinarians = User.objects.filter(user_type='veterinarian')
    return render(request, 'admin/view_veterinarians.html', {'veterinarians': veterinarians})


def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')

# ═══════════════════════════════════════════════════════
# UPDATE PROFILE VIEWS
# ═══════════════════════════════════════════════════════

@login_required
def update_user_profile(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        # Update fields
        request.user.email = request.POST.get('email')
        request.user.phone = request.POST.get('phone')
        request.user.address = request.POST.get('address')
        request.user.district = request.POST.get('district')  # Allow district change
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_dashboard')
    
    return render(request, 'user/update_profile.html', {'user': request.user})


@login_required
def update_care_center_profile(request):
    if request.user.user_type != 'care_center':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST':
        request.user.care_center_name = request.POST.get('care_center_name')
        request.user.email = request.POST.get('email')
        request.user.phone = request.POST.get('phone')
        request.user.address = request.POST.get('address')
        # District cannot be changed for care center
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('care_center_dashboard')
    
    return render(request, 'care_center/update_profile.html', {'user': request.user})

# ═══════════════════════════════════════════════════════
# USER NOTIFICATIONS
# ═══════════════════════════════════════════════════════

@login_required
def user_notifications(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    # Get animals taken by care centers
    animal_notifications = StrayAnimalReport.objects.filter(
        reporter=request.user,
        status__in=['Under Care', 'Healthy']
    ).select_related('taken_by_care_center').order_by('-updated_at')
    
    # Get adoption request updates
    adoption_notifications = AnimalAdoption.objects.filter(
        adopter=request.user,
        adoption_status__in=['Approved', 'Rejected']
    ).select_related('animal__taken_by_care_center').order_by('-updated_at')
    
    # Mark all as read
    StrayAnimalReport.objects.filter(
        reporter=request.user,
        notification_seen=False
    ).update(notification_seen=True)
    
    AnimalAdoption.objects.filter(
        adopter=request.user,
        notification_seen=False
    ).update(notification_seen=True)
    
    context = {
        'animal_notifications': animal_notifications,
        'adoption_notifications': adoption_notifications,
    }
    return render(request, 'user/notifications.html', context)


# ═══════════════════════════════════════════════════════
# VIEW CARE CENTERS (FOR USERS)
# ═══════════════════════════════════════════════════════

@login_required
def view_care_centers_user(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    care_centers = User.objects.filter(
        user_type='care_center',
        district=request.user.district
    )
    
    context = {
        'care_centers': care_centers,
    }
    return render(request, 'user/view_care_centers.html', context)


# ═══════════════════════════════════════════════════════
# VIEW VETERINARIANS (FOR USERS)
# ═══════════════════════════════════════════════════════

@login_required
def view_veterinarians_user(request):
    if request.user.user_type != 'user':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    veterinarians = User.objects.filter(
        user_type='veterinarian',
        district=request.user.district
    )
    
    context = {
        'veterinarians': veterinarians,
    }
    return render(request, 'user/view_veterinarians.html', context)


# ═══════════════════════════════════════════════════════
# REJECT ADOPTION
# ═══════════════════════════════════════════════════════

@login_required
def reject_adoption(request, adoption_id):
    if request.user.user_type != 'care_center':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    adoption = get_object_or_404(AnimalAdoption, id=adoption_id)
    
    if adoption.animal.taken_by_care_center != request.user:
        messages.error(request, 'You can only manage adoptions for animals in your care.')
        return redirect('manage_adoption_requests')
    
    # Reject the adoption
    adoption.adoption_status = 'Rejected'
    adoption.save()
    
    # Animal remains available for adoption by others
    # Notification is automatic - user will see it in notifications page
    
    messages.warning(request, f'Adoption request rejected for {adoption.adopter.username}')
    return redirect('manage_adoption_requests')


@login_required
def upload_healthy_image(request, animal_id):
    if request.user.user_type != 'care_center':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    animal = get_object_or_404(StrayAnimalReport, id=animal_id)
    
    if animal.taken_by_care_center != request.user:
        messages.error(request, 'You can only upload images for animals in your care.')
        return redirect('care_center_dashboard')
    
    if animal.status != 'Healthy':
        messages.error(request, 'Can only upload images for healthy animals.')
        return redirect('care_center_dashboard')
    
    if request.method == 'POST':
        form = HealthyImageForm(request.POST, request.FILES, instance=animal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Healthy animal photo uploaded successfully!')
            return redirect('care_center_dashboard')
    else:
        form = HealthyImageForm(instance=animal)
    
    context = {
        'form': form,
        'animal': animal,
    }
    return render(request, 'care_center/upload_healthy_image.html', context)