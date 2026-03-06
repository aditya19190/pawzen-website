from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # User URLs
    path('user/register/', views.user_register, name='user_register'),
    path('user/login/', views.user_login, name='user_login'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/report-animal/', views.report_stray_animal, name='report_stray_animal'),
    path('user/adoption-list/', views.view_adoption_animals, name='view_adoption_animals'),
    path('user/request-adoption/<int:animal_id>/', views.request_adoption, name='request_adoption'),
    path('user/request-consultation/', views.request_consultation_user, name='request_consultation_user'),
    path('user/delete-account/', views.delete_user_account, name='delete_user_account'),
    
    # Care Center URLs
    path('care-center/register/', views.care_center_register, name='care_center_register'),
    path('care-center/login/', views.care_center_login, name='care_center_login'),
    path('care-center/dashboard/', views.care_center_dashboard, name='care_center_dashboard'),
    path('care-center/take-animal/<int:animal_id>/', views.take_animal, name='take_animal'),
    path('care-center/request-consultation/<int:animal_id>/', views.request_consultation_care_center, name='request_consultation_care_center'),
    path('care-center/veterinarians/', views.view_veterinarians, name='view_veterinarians'),
    path('care-center/adoption-requests/', views.manage_adoption_requests, name='manage_adoption_requests'),
    path('care-center/approve-adoption/<int:adoption_id>/', views.approve_adoption, name='approve_adoption'),
    path('care-center/delete-account/', views.delete_care_center_account, name='delete_care_center_account'),
    
    # Veterinarian URLs
    path('veterinarian/register/', views.veterinarian_register, name='veterinarian_register'),
    path('veterinarian/login/', views.veterinarian_login, name='veterinarian_login'),
    path('veterinarian/dashboard/', views.veterinarian_dashboard, name='veterinarian_dashboard'),
    path('veterinarian/provide-treatment/<int:consultation_id>/', views.provide_treatment, name='provide_treatment'),
    path('veterinarian/update-profile/', views.update_veterinarian_profile, name='update_veterinarian_profile'),
    path('veterinarian/delete-account/', views.delete_veterinarian_account, name='delete_veterinarian_account'),
    
    # Admin URLs
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_view_users, name='admin_view_users'),
    path('admin-panel/care-centers/', views.admin_view_care_centers, name='admin_view_care_centers'),
    path('admin-panel/veterinarians/', views.admin_view_veterinarians, name='admin_view_veterinarians'),
    
    # Common
    path('logout/', views.user_logout, name='logout'),

    # User profile update
    path('user/update-profile/', views.update_user_profile, name='update_user_profile'),
    
    # Care center profile update
    path('care-center/update-profile/', views.update_care_center_profile, name='update_care_center_profile'),

    # User notifications and views
    path('user/notifications/', views.user_notifications, name='user_notifications'),
    path('user/view-care-centers/', views.view_care_centers_user, name='view_care_centers_user'),
    path('user/view-veterinarians/', views.view_veterinarians_user, name='view_veterinarians_user'),
    
    # Reject adoption
    path('care-center/reject-adoption/<int:adoption_id>/', views.reject_adoption, name='reject_adoption'),

    # Upload healthy image
    path('care-center/upload-healthy-image/<int:animal_id>/', views.upload_healthy_image, name='upload_healthy_image'),
]