from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import Advertisement, Photo

AUCTION_STEP_WIDGET_CHOICES = [
    (1, '1 ₽'),
    (10, '10 ₽'),
    (100, '100 ₽'),
    (1000, '1 000 ₽'),
]


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class AdvertisementForm(forms.ModelForm):
    photos = forms.ImageField(
        label='Фотографии',
        required=False,
        widget=MultiFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text='Можно загрузить до 10 фотографий.',
    )
    auction_step = forms.TypedChoiceField(
        label='шаг ставки',
        choices=AUCTION_STEP_WIDGET_CHOICES,
        coerce=int,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_auction_step'}),
    )

    class Meta:
        model = Advertisement
        fields = [
            'title',
            'description',
            'price',
            'region',
            'category',
            'ad_type',
            'status',
            'auction_step',
            'auction_end',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '1', 'id': 'id_price'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'ad_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_ad_type'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'auction_end': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local', 'id': 'id_auction_end'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            (Advertisement.Status.DRAFT, Advertisement.Status.DRAFT.label),
            (Advertisement.Status.PUBLISHED, Advertisement.Status.PUBLISHED.label),
        ]
        self.fields['auction_end'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S']
        if self.instance.pk and self.instance.auction_end:
            self.initial['auction_end'] = timezone.localtime(self.instance.auction_end).strftime(
                '%Y-%m-%dT%H:%M'
            )
        if not self.instance.auction_step:
            self.initial.setdefault('auction_step', 1)

    def clean(self):
        cleaned = super().clean()
        is_auction = cleaned.get('ad_type') == Advertisement.AdType.AUCTION
        price = cleaned.get('price')

        if is_auction:
            if price is None:
                self.add_error('price', 'Укажите стартовую цену аукциона.')
            elif price != int(price):
                self.add_error('price', 'Цена аукциона — целое число рублей.')
            elif int(price) < 1:
                self.add_error('price', 'Цена должна быть не меньше 1 ₽.')

            if not cleaned.get('auction_end'):
                self.add_error('auction_end', 'Укажите дату окончания аукциона.')
            elif cleaned['auction_end'] <= timezone.now():
                self.add_error('auction_end', 'Дата окончания должна быть в будущем.')

            step = cleaned.get('auction_step') or 1
            if step not in Advertisement.AUCTION_STEP_CHOICES:
                self.add_error('auction_step', 'Выберите шаг: 1, 10, 100 или 1 000 ₽.')
        else:
            cleaned['auction_step'] = None
            cleaned['auction_end'] = None

        return cleaned

    def clean_photos(self):
        files = self.files.getlist('photos')
        current_count = self.instance.photos.count() if self.instance.pk else 0
        if current_count + len(files) > 10:
            raise forms.ValidationError('Можно загрузить не более 10 фотографий.')
        return files

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.ad_type == Advertisement.AdType.AUCTION:
            instance.price = Decimal(int(instance.price))
            instance.start_price = instance.price
            if not instance.current_price:
                instance.current_price = instance.price
            if not instance.auction_step:
                instance.auction_step = 1
            instance.auction_finished = False
        else:
            instance.start_price = None
            instance.current_price = None
            instance.auction_end = None
            instance.auction_step = 1
            instance.auction_finished = False
            instance.auction_winner = None

        if commit:
            instance.save()
            self.save_m2m()
        return instance

    def save_photos(self, advertisement: Advertisement) -> None:
        files = self.cleaned_data.get('photos') or []
        for order, image in enumerate(files):
            Photo.objects.create(advertisement=advertisement, image=image, order=order)
