from django.contrib import admin

from .models import Chat, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'created_at', 'is_read', 'is_edited', 'is_deleted')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'advertisement', 'buyer', 'seller', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('advertisement__title', 'buyer__username', 'seller__username')
    inlines = (MessageInline,)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'is_read', 'is_edited', 'is_deleted', 'created_at')
    list_filter = ('is_read', 'is_edited', 'is_deleted')
