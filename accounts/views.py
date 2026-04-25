from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ads.models import Advertisement, Photo

from .forms import CustomUserCreationForm, StyledAuthenticationForm


def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно. Добро пожаловать!')
            return redirect('core:home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    authentication_form = StyledAuthenticationForm


@require_http_methods(['GET', 'POST'])
def user_logout(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, 'Вы вышли из аккаунта.')
        return render(request, 'accounts/logout.html', {'logged_out': True})

    if not request.user.is_authenticated:
        messages.warning(request, 'Вы не авторизованы.')
        return redirect('accounts:login')

    return render(request, 'accounts/logout.html', {'logged_out': False})


@login_required
def cabinet(request):
    return redirect('accounts:profile')


@login_required
def profile(request):
    my_ads = (
        Advertisement.objects.filter(author=request.user)
        .select_related('category')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )
    return render(request, 'accounts/profile.html', {'my_ads': my_ads})


@login_required
def favorites(request):
    favorite_ads = (
        Advertisement.objects.filter(
            favorited_by__user=request.user,
            is_active=True,
            status=Advertisement.Status.PUBLISHED,
        )
        .select_related('category', 'author')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )
    return render(request, 'accounts/favorites.html', {'favorite_ads': favorite_ads})
