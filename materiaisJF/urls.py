from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('index.urls')),
    path('admin/', admin.site.urls),
    path('consultaOracle/', include('consultaOracle.urls')),
]
