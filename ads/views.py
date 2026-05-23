from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .auction_services import (
    archive_old_drafts,
    finalize_expired_auctions,
    get_auction_base,
    get_auction_step,
    get_min_bid,
    is_auction_active,
    place_bid,
)
from .forms import AdvertisementForm
from .list_filters import (
    apply_auction_price_filters,
    apply_common_filters,
    apply_price_filters,
    parse_list_filters,
)
from .models import AdView, Advertisement, Bid, Category, Favorite, Photo, Region


def _list_filter_context(request, filters: dict) -> dict:
    return {
        'categories': Category.objects.filter(parent__isnull=True),
        'regions': Region.objects.all(),
        'filters': filters,
    }


def ad_list(request):
    archive_old_drafts()
    finalize_expired_auctions()
    filters = parse_list_filters(request)

    ads = (
        Advertisement.objects.filter(
            is_active=True,
            status=Advertisement.Status.PUBLISHED,
            ad_type__in=[
                Advertisement.AdType.SALE,
                Advertisement.AdType.SERVICE,
                Advertisement.AdType.EXCHANGE,
            ],
        )
        .select_related('category', 'author', 'region')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )
    ads = apply_common_filters(ads, filters)
    ads = apply_price_filters(ads, filters)

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(user=request.user).values_list('advertisement_id', flat=True)
        )

    context = {
        'advertisements': ads,
        'favorite_ids': favorite_ids,
        'reset_url': request.path,
        **_list_filter_context(request, filters),
    }
    return render(request, 'ads/ads_list.html', context)


def auction_list(request):
    """Отдельная вкладка: только активные аукционы."""
    archive_old_drafts()
    finalize_expired_auctions()
    filters = parse_list_filters(request)

    ads = (
        Advertisement.objects.filter(
            is_active=True,
            status=Advertisement.Status.PUBLISHED,
            ad_type=Advertisement.AdType.AUCTION,
            auction_finished=False,
        )
        .select_related('category', 'author', 'region', 'auction_winner')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )
    ads = apply_common_filters(ads, filters)
    ads = apply_auction_price_filters(ads, filters)
    ads = ads.order_by('auction_end')

    context = {
        'advertisements': ads,
        'reset_url': request.path,
        'price_min_label': 'Ставка от',
        'price_max_label': 'Ставка до',
        **_list_filter_context(request, filters),
    }
    return render(request, 'ads/auction_list.html', context)


def ad_detail(request, pk):
    archive_old_drafts()
    finalize_expired_auctions()
    advertisement = get_object_or_404(
        Advertisement.objects.select_related(
            'category', 'author', 'region', 'auction_winner'
        ).prefetch_related('photos'),
        pk=pk,
        is_active=True,
    )
    # Самопросмотры не считаем: автор не увеличивает счетчик и не пишем в историю.
    if not request.user.is_authenticated or request.user != advertisement.author:
        Advertisement.objects.filter(pk=advertisement.pk).update(views_count=F('views_count') + 1)
        advertisement.refresh_from_db(fields=['views_count'])
        # История просмотров для личного кабинета
        if request.user.is_authenticated:
            AdView.objects.create(user=request.user, advertisement=advertisement)
        elif request.session.session_key:
            AdView.objects.create(
                session_key=request.session.session_key,
                advertisement=advertisement,
            )
        else:
            request.session.create()
            AdView.objects.create(
                session_key=request.session.session_key,
                advertisement=advertisement,
            )
    is_favorite = False
    if request.user.is_authenticated and request.user != advertisement.author:
        is_favorite = Favorite.objects.filter(user=request.user, advertisement=advertisement).exists()

    bids = []
    auction_active = False
    min_bid = None
    show_bids_history = False
    if advertisement.is_auction:
        auction_active = is_auction_active(advertisement)
        min_bid = get_min_bid(advertisement)
        show_bids_history = request.user.is_authenticated and request.user == advertisement.author
        if show_bids_history:
            bids = list(
                advertisement.bids.select_related('bidder').order_by('-created_at')[:20]
            )

    return render(
        request,
        'ads/ad_detail.html',
        {
            'advertisement': advertisement,
            'is_favorite': is_favorite,
            'bids': bids,
            'auction_active': auction_active,
            'min_bid': min_bid,
            'show_bids_history': show_bids_history,
            'auction_base': get_auction_base(advertisement) if advertisement.is_auction else None,
            'auction_step_value': get_auction_step(advertisement) if advertisement.is_auction else None,
        },
    )


@login_required
@require_POST
def place_bid(request: HttpRequest, pk: int) -> HttpResponse:
    """HTTP-ставка (резерв, основной канал — WebSocket)."""
    advertisement = get_object_or_404(
        Advertisement, pk=pk, ad_type=Advertisement.AdType.AUCTION, is_active=True
    )
    try:
        amount = Decimal(request.POST.get('amount', '').replace(',', '.'))
        place_bid(advertisement, request.user, amount)
        messages.success(request, f'Ставка {int(amount)} ₽ принята.')
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect('ads:ad_detail', pk=pk)


@login_required
def create_ad(request):
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES)
        if form.is_valid():
            advertisement = form.save(commit=False)
            advertisement.author = request.user
            advertisement.save()
            form.save_photos(advertisement)
            messages.success(request, 'Объявление успешно создано.')
            return redirect('ads:ad_detail', pk=advertisement.pk)
    else:
        form = AdvertisementForm()
    return render(request, 'ads/create_ad.html', {'form': form})


@login_required
def edit_ad(request, pk):
    advertisement = get_object_or_404(Advertisement, pk=pk, author=request.user)
    if request.method == 'POST':
        form = AdvertisementForm(request.POST, request.FILES, instance=advertisement)
        if form.is_valid():
            advertisement = form.save()
            form.save_photos(advertisement)
            messages.success(request, 'Объявление обновлено.')
            return redirect('ads:ad_detail', pk=advertisement.pk)
    else:
        form = AdvertisementForm(instance=advertisement)
    return render(request, 'ads/edit_ad.html', {'form': form, 'advertisement': advertisement})


@login_required
@require_POST
def delete_ad(request: HttpRequest, pk: int) -> HttpResponse:
    advertisement = get_object_or_404(Advertisement, pk=pk, author=request.user)
    advertisement.delete()
    messages.success(request, 'Объявление удалено.')
    return redirect('accounts:profile')


@login_required
@require_POST
def toggle_favorite(request: HttpRequest, pk: int) -> HttpResponse:
    advertisement = get_object_or_404(
        Advertisement,
        pk=pk,
        is_active=True,
        status=Advertisement.Status.PUBLISHED,
    )
    if advertisement.author == request.user:
        messages.info(request, 'Свои объявления нельзя добавлять в избранное.')
        return redirect('ads:ad_detail', pk=pk)

    favorite, created = Favorite.objects.get_or_create(user=request.user, advertisement=advertisement)
    if created:
        messages.success(request, 'Объявление добавлено в избранное.')
    else:
        favorite.delete()
        messages.info(request, 'Объявление удалено из избранного.')

    redirect_to = request.POST.get('next', '')
    if redirect_to and url_has_allowed_host_and_scheme(
        url=redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(redirect_to)
    return redirect('ads:ad_detail', pk=pk)
