"""geogame URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
from django.urls import reverse_lazy

from geogame.main.views import HomePageView, ProfilePageView, UpdateAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    url(r'play/', include(('geogame.main.urls', 'game'), namespace="game")),
    url(r'profile/$', ProfilePageView.as_view(), name="profile"),
    url(r'api-form/(?P<pk>\d+)/$', UpdateAPIView.as_view(), name="api-key-view"),
    url(r'', HomePageView.as_view(), name="home"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
