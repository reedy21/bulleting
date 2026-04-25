"""Общие страницы сайта (главная)."""
from django.shortcuts import redirect


def home(request):
    """Главная страница ведет на общую доску объявлений."""
    return redirect('ads:ad_list')
