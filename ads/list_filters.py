"""Общие фильтры списков объявлений и аукционов."""

from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.db.models.functions import Coalesce

def parse_list_filters(request) -> dict:
    return {
        'q': request.GET.get('q', '').strip(),
        'category': request.GET.get('category', '').strip(),
        'region': request.GET.get('region', '').strip(),
        'price_min': request.GET.get('price_min', '').strip(),
        'price_max': request.GET.get('price_max', '').strip(),
    }


def apply_common_filters(queryset, filters: dict):
    """Поиск, категория, регион."""
    if filters['q']:
        queryset = queryset.filter(
            Q(title__icontains=filters['q']) | Q(description__icontains=filters['q'])
        )
    if filters['category'].isdigit():
        queryset = queryset.filter(category_id=int(filters['category']))
    if filters['region'].isdigit():
        queryset = queryset.filter(region_id=int(filters['region']))
    return queryset


def apply_price_filters(queryset, filters: dict, *, field: str = 'price'):
    """Фильтр по цене (обычные объявления — поле price)."""
    if filters['price_min']:
        try:
            queryset = queryset.filter(**{f'{field}__gte': Decimal(filters['price_min'])})
        except (TypeError, ValueError, InvalidOperation):
            pass
    if filters['price_max']:
        try:
            queryset = queryset.filter(**{f'{field}__lte': Decimal(filters['price_max'])})
        except (TypeError, ValueError, InvalidOperation):
            pass
    return queryset


def apply_auction_price_filters(queryset, filters: dict):
    """Фильтр по текущей ставке (current_price или стартовая price)."""
    if not filters['price_min'] and not filters['price_max']:
        return queryset
    queryset = queryset.annotate(
        effective_price=Coalesce('current_price', 'price'),
    )
    if filters['price_min']:
        try:
            queryset = queryset.filter(effective_price__gte=Decimal(filters['price_min']))
        except (TypeError, ValueError, InvalidOperation):
            pass
    if filters['price_max']:
        try:
            queryset = queryset.filter(effective_price__lte=Decimal(filters['price_max']))
        except (TypeError, ValueError, InvalidOperation):
            pass
    return queryset
