from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """Админка для кастомного пользователя: те же возможности, что у стандартного User."""

    pass
