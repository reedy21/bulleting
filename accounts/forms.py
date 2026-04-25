from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser


class StyledAuthenticationForm(AuthenticationForm):
    """Та же AuthenticationForm, но с классами Bootstrap для полей ввода."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control rounded-0')


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control rounded-0')
