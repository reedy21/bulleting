from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ads.auction_services import archive_old_drafts, finalize_expired_auctions
from ads.models import AdView, Advertisement, Bid, Photo, UserNotification

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
        .exclude(ad_type=Advertisement.AdType.AUCTION)
        .select_related('category', 'region')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )
    return render(request, 'accounts/profile.html', {'my_ads': my_ads})


def _auction_list_context(active_qs, finished_qs, *, auctions_tab: str, participating: bool):
    return {
        'profile_tab': 'auctions',
        'auctions_tab': auctions_tab,
        'participating_mode': participating,
        'active_auctions': active_qs,
        'finished_auctions': finished_qs,
        'active_empty': 'Нет активных аукционов.' if auctions_tab == 'mine' else 'Вы не участвуете в активных аукционах.',
        'finished_empty': 'Нет завершённых аукционов.' if auctions_tab == 'mine' else 'Нет завершённых аукционов с вашим участием.',
    }


@login_required
def my_auctions(request):
    """Аукционы, которые создал пользователь."""
    archive_old_drafts()
    finalize_expired_auctions()
    base_qs = (
        Advertisement.objects.filter(author=request.user, ad_type=Advertisement.AdType.AUCTION)
        .select_related('category', 'region', 'auction_winner')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )
    return render(
        request,
        'accounts/profile_auctions.html',
        _auction_list_context(
            base_qs.filter(auction_finished=False).order_by('auction_end'),
            base_qs.filter(auction_finished=True).order_by('-auction_end'),
            auctions_tab='mine',
            participating=False,
        ),
    )


@login_required
def participating_auctions(request):
    """Аукционы, в которых пользователь делал ставки (не свои)."""
    archive_old_drafts()
    finalize_expired_auctions()
    my_bids = Prefetch(
        'bids',
        queryset=Bid.objects.filter(bidder=request.user).order_by('-created_at'),
        to_attr='my_bids',
    )
    base_qs = (
        Advertisement.objects.filter(
            bids__bidder=request.user,
            ad_type=Advertisement.AdType.AUCTION,
        )
        .exclude(author=request.user)
        .distinct()
        .select_related('category', 'region', 'auction_winner')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')), my_bids)
    )
    return render(
        request,
        'accounts/profile_auctions.html',
        _auction_list_context(
            base_qs.filter(auction_finished=False).order_by('auction_end'),
            base_qs.filter(auction_finished=True).order_by('-auction_end'),
            auctions_tab='participating',
            participating=True,
        ),
    )


@login_required
def favorites(request):
    favorite_ads = (
        Advertisement.objects.filter(
            favorited_by__user=request.user,
            is_active=True,
            status=Advertisement.Status.PUBLISHED,
        )
        .select_related('category', 'author', 'region')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )
    return render(request, 'accounts/favorites.html', {'favorite_ads': favorite_ads})


@login_required
def view_history(request):
    """Недавно просмотренные объявления (уникальные, по последнему просмотру)."""
    seen = set()
    viewed_ids = []
    for ad_id in AdView.objects.filter(user=request.user).order_by('-viewed_at').values_list(
        'advertisement_id', flat=True
    ):
        if ad_id not in seen:
            seen.add(ad_id)
            viewed_ids.append(ad_id)

    ads_map = {
        ad.pk: ad
        for ad in Advertisement.objects.filter(pk__in=viewed_ids, is_active=True)
        .select_related('category', 'author', 'region')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    }
    viewed_ads = [ads_map[pk] for pk in viewed_ids if pk in ads_map]

    return render(request, 'accounts/view_history.html', {'viewed_ads': viewed_ads})


@login_required
def notifications(request):
    """In-app уведомления (победа в аукционе и др.)."""
    items = UserNotification.objects.filter(user=request.user).select_related('advertisement')[:50]
    UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'accounts/notifications.html', {'notifications': items})
