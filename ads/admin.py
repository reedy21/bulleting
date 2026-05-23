from django.contrib import admin

from .models import AdView, Advertisement, Bid, Category, Favorite, Photo, Region, UserNotification


class PhotoInline(admin.TabularInline):
    """Несколько фото к одному объявлению прямо в форме объявления."""

    model = Photo
    extra = 1


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('sort_order', 'name', 'slug', 'parent', 'created_at')
    list_display_links = ('name',)
    list_editable = ('sort_order',)
    list_filter = ('parent',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')
    readonly_fields = ('created_at',)


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('user', 'advertisement')


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('advertisement', 'bidder', 'amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('advertisement__title', 'bidder__username')


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'author',
        'price',
        'current_price',
        'auction_finished',
        'ad_type',
        'status',
        'is_active',
        'created_at',
    )
    list_filter = ('ad_type', 'status', 'is_active', 'auction_finished', 'category', 'region')
    search_fields = ('title', 'description', 'region__name')
    autocomplete_fields = ('category', 'author', 'region')
    inlines = (PhotoInline,)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'advertisement', 'order', 'uploaded_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'advertisement', 'created_at')
    search_fields = ('user__username', 'advertisement__title')


@admin.register(AdView)
class AdViewAdmin(admin.ModelAdmin):
    list_display = ('advertisement', 'user', 'session_key', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('advertisement__title', 'user__username')
