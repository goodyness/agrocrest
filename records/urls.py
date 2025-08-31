from django.contrib import admin
from django.urls import path
from records import views, admin_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
]
