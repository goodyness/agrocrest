
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('records.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]
