from django import forms

from .models import Advertisement, Photo


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class AdvertisementForm(forms.ModelForm):
    photos = forms.ImageField(
        label='Фотографии',
        required=False,
        widget=MultiFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text='Можно загрузить до 10 фотографий.',
    )

    class Meta:
        model = Advertisement
        fields = ['title', 'description', 'price', 'region', 'category', 'ad_type', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'ad_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_photos(self):
        files = self.files.getlist('photos')
        current_count = self.instance.photos.count() if self.instance.pk else 0
        if current_count + len(files) > 10:
            raise forms.ValidationError('Можно загрузить не более 10 фотографий.')
        return files

    def save_photos(self, advertisement: Advertisement) -> None:
        files = self.cleaned_data.get('photos') or []
        for order, image in enumerate(files):
            Photo.objects.create(advertisement=advertisement, image=image, order=order)
