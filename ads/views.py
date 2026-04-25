from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Prefetch, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AdvertisementForm
from .models import Advertisement, Category, Favorite, Photo


def ad_list(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    region = request.GET.get('region', '').strip()
    price_min = request.GET.get('price_min', '').strip()
    price_max = request.GET.get('price_max', '').strip()

    ads = (
        Advertisement.objects.filter(is_active=True, status=Advertisement.Status.PUBLISHED)
        .select_related('category', 'author')
        .prefetch_related(Prefetch('photos', queryset=Photo.objects.order_by('order', 'id')))
    )

    if query:
        ads = ads.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category_id.isdigit():
        ads = ads.filter(category_id=int(category_id))
    if region:
        ads = ads.filter(region__icontains=region)
    if price_min:
        try:
            ads = ads.filter(price__gte=Decimal(price_min))
        except (TypeError, ValueError, InvalidOperation):
            pass
    if price_max:
        try:
            ads = ads.filter(price__lte=Decimal(price_max))
        except (TypeError, ValueError, InvalidOperation):
            pass

    categories = Category.objects.all()
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(user=request.user).values_list('advertisement_id', flat=True)
        )

    context = {
        'advertisements': ads,
        'categories': categories,
        'favorite_ids': favorite_ids,
        'filters': {
            'q': query,
            'category': category_id,
            'region': region,
            'price_min': price_min,
            'price_max': price_max,
        },
    }
    return render(request, 'ads/ads_list.html', context)


def ad_detail(request, pk):
    advertisement = get_object_or_404(
        Advertisement.objects.select_related('category', 'author').prefetch_related('photos'),
        pk=pk,
        is_active=True,
    )
    # Самопросмотры не считаем: автор не увеличивает счетчик.
    if not request.user.is_authenticated or request.user != advertisement.author:
        Advertisement.objects.filter(pk=advertisement.pk).update(views_count=F('views_count') + 1)
        advertisement.refresh_from_db(fields=['views_count'])
    is_favorite = False
    if request.user.is_authenticated and request.user != advertisement.author:
        is_favorite = Favorite.objects.filter(user=request.user, advertisement=advertisement).exists()
    return render(
        request,
        'ads/ad_detail.html',
        {'advertisement': advertisement, 'is_favorite': is_favorite},
    )


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
