"""Логика аукционов: ставки, завершение, архивация черновиков."""

from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from .models import Advertisement, Bid
from .notifications import notify_auction_author, notify_auction_winner

DRAFT_ARCHIVE_DAYS = 2


def archive_old_drafts() -> int:
    """Черновики старше DRAFT_ARCHIVE_DAYS переводятся в архив."""
    cutoff = timezone.now() - timedelta(days=DRAFT_ARCHIVE_DAYS)
    return Advertisement.objects.filter(
        status=Advertisement.Status.DRAFT,
        created_at__lt=cutoff,
    ).update(status=Advertisement.Status.ARCHIVED)


def finalize_expired_auctions() -> int:
    """Завершить аукционы с истёкшим временем."""
    now = timezone.now()
    expired = Advertisement.objects.filter(
        ad_type=Advertisement.AdType.AUCTION,
        auction_finished=False,
        auction_end__lt=now,
        is_active=True,
    )
    count = 0
    for ad in expired:
        _finish_auction(ad)
        count += 1
    return count


def _finish_auction(advertisement: Advertisement) -> None:
    """Закрыть аукцион и записать победителя."""
    if advertisement.auction_finished:
        return
    top_bid = advertisement.bids.order_by('-amount', '-created_at').first()
    advertisement.auction_finished = True
    if top_bid:
        advertisement.auction_winner = top_bid.bidder
        advertisement.current_price = top_bid.amount
    advertisement.save(
        update_fields=['auction_finished', 'auction_winner', 'current_price', 'updated_at']
    )
    notify_auction_author(advertisement)
    notify_auction_winner(advertisement)


def is_auction_active(ad: Advertisement) -> bool:
    """Аукцион идёт: тип «аукцион», не завершён, срок не истёк."""
    if not ad.is_auction or ad.auction_finished:
        return False
    if ad.auction_end and ad.auction_end <= timezone.now():
        return False
    return ad.status == Advertisement.Status.PUBLISHED


def get_auction_step(ad: Advertisement) -> int:
    """Шаг торгов в рублях (1, 10, 100 или 1000)."""
    step = ad.auction_step or 1
    if step not in Advertisement.AUCTION_STEP_CHOICES:
        return 1
    return step


def get_auction_base(ad: Advertisement) -> int:
    """Стартовая цена аукциона в целых рублях."""
    return int(ad.auction_base_price)


def is_on_bid_grid(ad: Advertisement, amount: int) -> bool:
    """Сумма кратна шагу от стартовой цены."""
    base = get_auction_base(ad)
    step = get_auction_step(ad)
    return amount >= base and (amount - base) % step == 0


def next_bid_after(ad: Advertisement, current: int) -> int:
    """Следующая допустимая ставка строго не ниже current + шаг, на сетке шага."""
    base = get_auction_base(ad)
    step = get_auction_step(ad)
    if current < base:
        return base
    remainder = (current - base) % step
    if remainder == 0:
        return current + step
    return current + (step - remainder)


def get_min_bid(ad: Advertisement) -> Decimal:
    """Минимальная следующая ставка на сетке шага."""
    base = get_auction_base(ad)
    current = int(ad.current_price) if ad.current_price is not None else base
    if not ad.bids.exists():
        return Decimal(base)
    return Decimal(next_bid_after(ad, current))


def normalize_rubles(amount) -> Decimal:
    """Только целые рубли, без копеек."""
    try:
        value = Decimal(str(amount).replace(',', '.'))
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('Укажите корректную сумму в рублях.') from exc
    if value != value.to_integral_value():
        raise ValueError('Ставка указывается только целыми рублями, без копеек.')
    if value < 0:
        raise ValueError('Сумма не может быть отрицательной.')
    return value.to_integral_value()


@transaction.atomic
def place_bid(advertisement: Advertisement, user, amount) -> Bid:
    """Разместить ставку: целые рубли, кратно шагу от стартовой цены."""
    amount = normalize_rubles(amount)
    amount_int = int(amount)
    ad = Advertisement.objects.select_for_update().get(pk=advertisement.pk)

    if not is_auction_active(ad):
        raise ValueError('Аукцион завершён или ещё не начался.')
    if ad.author_id == user.pk:
        raise ValueError('Нельзя делать ставку на своё объявление.')

    step = get_auction_step(ad)
    base = get_auction_base(ad)
    if not is_on_bid_grid(ad, amount_int):
        raise ValueError(
            f'Ставка должна быть кратна шагу {step} ₽ от стартовой цены {base} ₽ '
            f'(например {base}, {base + step}, {base + 2 * step}…).'
        )

    min_bid = get_min_bid(ad)
    if amount < min_bid:
        raise ValueError(f'Минимальная ставка: {int(min_bid)} ₽')

    bid = Bid.objects.create(advertisement=ad, bidder=user, amount=amount)
    ad.current_price = amount
    ad.save(update_fields=['current_price', 'updated_at'])
    return bid
