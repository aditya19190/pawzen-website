from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, StrayAnimalReport, VeterinaryConsultation, AnimalAdoption, DISTRICT_CHOICES
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class RequestConsultationForm(forms.ModelForm):

    class Meta:

        model = VeterinaryConsultation

        fields = ['request_description', 'veterinarian']

        widgets = {

            'request_description': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),

            'veterinarian': forms.Select(
                attrs={'class': 'form-control'}
            ),

        }


    def __init__(self, *args, **kwargs):

        district = kwargs.pop('district', None)

        super().__init__(*args, **kwargs)

        if district:

            self.fields['veterinarian'].queryset = User.objects.filter(

                user_type='veterinarian',

                district=district,

                is_active=True

            )

class CustomLoginForm(forms.Form):

    username = forms.CharField()

    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):

        username = self.cleaned_data.get('username')

        password = self.cleaned_data.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            raise forms.ValidationError("Invalid username or password")

        return self.cleaned_data

def validate_email_exists(email):
    """Validate that email is properly formatted"""
    try:
        validate_email(email)
    except ValidationError:
        raise ValidationError("Enter a valid email address.")
    return email

# User Registration Form
class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=True)
    district = forms.ChoiceField(
        choices=[('', 'Select District')] + list(DISTRICT_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone', 'address', 'district']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return validate_email_exists(email)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'user'
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.district = self.cleaned_data['district']
        if commit:
            user.save()
        return user


# Care Center Registration Form
class CareCenterRegistrationForm(UserCreationForm):
    care_center_name = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=True)
    district = forms.ChoiceField(
        choices=[('', 'Select District')] + list(DISTRICT_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    license_number = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'care_center_name', 'email', 'password1', 'password2', 
                  'phone', 'address', 'district', 'license_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return validate_email_exists(email)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'care_center'
        user.care_center_name = self.cleaned_data['care_center_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.district = self.cleaned_data['district']
        user.license_number = self.cleaned_data['license_number']
        if commit:
            user.save()
        return user


# Veterinarian Registration Form
class VeterinarianRegistrationForm(UserCreationForm):
    veterinarian_name = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=True)
    district = forms.ChoiceField(
        choices=[('', 'Select District')] + list(DISTRICT_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    qualification = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    specialization = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    registration_number = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'veterinarian_name', 'email', 'password1', 'password2', 
                  'phone', 'address', 'district', 'qualification', 'specialization', 'registration_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        return validate_email_exists(email)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'veterinarian'
        user.veterinarian_name = self.cleaned_data['veterinarian_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.district = self.cleaned_data['district']
        user.qualification = self.cleaned_data['qualification']
        user.specialization = self.cleaned_data['specialization']
        user.registration_number = self.cleaned_data['registration_number']
        if commit:
            user.save()
        return user


# Custom Login Form
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


# Stray Animal Report Form
class ReportAnimalForm(forms.ModelForm):
    class Meta:
        model = StrayAnimalReport
        fields = ['animal_type', 'location', 'description', 'district', 'reported_image']
        widgets = {
            'animal_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'district': forms.Select(attrs={'class': 'form-select'}),
            'reported_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'reported_image': 'Animal Photo (Optional)',
        }


# Veterinary Consultation Request Form
class RequestConsultationForm(forms.ModelForm):
    class Meta:
        model = VeterinaryConsultation
        fields = ['request_description', 'veterinarian']
        widgets = {
            'request_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'veterinarian': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        district = kwargs.pop('district', None)
        super().__init__(*args, **kwargs)
        if district:
            self.fields['veterinarian'].queryset = User.objects.filter(
                user_type='veterinarian', 
                district=district,
                is_active=True
            )
        else:
            self.fields['veterinarian'].queryset = User.objects.filter(
                user_type='veterinarian',
                is_active=True
            )


# Treatment Details Form
class TreatmentDetailsForm(forms.ModelForm):
    class Meta:
        model = VeterinaryConsultation
        fields = ['treatment_details', 'consultation_status']
        widgets = {
            'treatment_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'consultation_status': forms.Select(attrs={'class': 'form-control'}),
        }


# Animal Adoption Request Form
class AnimalAdoptionForm(forms.ModelForm):
    class Meta:
        model = AnimalAdoption
        fields = ['adopter_reason']
        widgets = {
            'adopter_reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Please explain why you want to adopt this animal'
            }),
        }


# Veterinarian Profile Update Form
class VeterinarianProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['veterinarian_name', 'email', 'phone', 'address', 'qualification', 'specialization']
        widgets = {
            'veterinarian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
        }


class HealthyImageForm(forms.ModelForm):
    class Meta:
        model = StrayAnimalReport
        fields = ['healthy_image']
        widgets = {
            'healthy_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'healthy_image': 'Upload Healthy Animal Photo',
        }