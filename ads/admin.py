from django.contrib import admin

from .models import Advertisement, Category, Favorite, Photo


class PhotoInline(admin.TabularInline):
    """Несколько фото к одному объявлению прямо в форме объявления."""

    model = Photo
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    list_display = ('name', 'slug', 'parent')


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'price', 'ad_type', 'status', 'is_active', 'created_at')
    list_filter = ('ad_type', 'status', 'is_active', 'category', 'region')
    search_fields = ('title', 'description', 'region')
    autocomplete_fields = ('category', 'author')
    inlines = (PhotoInline,)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'advertisement', 'order', 'uploaded_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'advertisement', 'created_at')
    search_fields = ('user__username', 'advertisement__title')
