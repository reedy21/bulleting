from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ads.models import Advertisement

from .models import Chat, Message
from .services import get_or_create_chat, unread_messages_count, user_chats_queryset


@login_required
def chat_list(request):
    """Список всех диалогов пользователя с превью последнего сообщения."""
    chats = user_chats_queryset(request.user).annotate(
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False, messages__is_deleted=False)
            & ~Q(messages__sender=request.user),
        ),
        last_message_time=Max('messages__created_at'),
    )

    chat_items = []
    for chat in chats:
        last_msg = (
            chat.messages.filter(is_deleted=False)
            .select_related('sender')
            .order_by('-created_at')
            .first()
        )
        chat_items.append(
            {
                'chat': chat,
                'other_user': chat.other_participant(request.user),
                'last_message': last_msg,
                'unread_count': chat.unread_count,
            }
        )

    return render(request, 'chat/chat_list.html', {'chat_items': chat_items})


@login_required
def chat_room(request, pk):
    """Страница чата: история из БД + WebSocket для реал-тайма."""
    chat = get_object_or_404(
        Chat.objects.select_related('advertisement', 'buyer', 'seller'),
        pk=pk,
    )
    if not chat.involves_user(request.user):
        messages.error(request, 'У вас нет доступа к этому чату.')
        return redirect('chat:chat_list')

    message_list = list(
        chat.messages.select_related('sender').order_by('created_at')
    )
    # Помечаем входящие прочитанными при открытии страницы (дублирует WS при подключении)
    Message.objects.filter(chat=chat, is_read=False, is_deleted=False).exclude(
        sender=request.user
    ).update(is_read=True)

    return render(
        request,
        'chat/chat_room.html',
        {
            'chat': chat,
            'chat_messages': message_list,
            'other_user': chat.other_participant(request.user),
            'current_user_id': request.user.pk,
        },
    )


@login_required
def start_chat(request, ad_pk):
    """
    Кнопка «Написать автору»: создаёт чат и перенаправляет в комнату.

    Нельзя писать самому себе; только зарегистрированные пользователи.
    """
    advertisement = get_object_or_404(
        Advertisement,
        pk=ad_pk,
        is_active=True,
        status=Advertisement.Status.PUBLISHED,
    )

    if advertisement.author == request.user:
        messages.info(request, 'Нельзя начать чат со своим объявлением.')
        return redirect('ads:ad_detail', pk=ad_pk)

    chat = get_or_create_chat(advertisement, request.user)
    return redirect('chat:chat_room', pk=chat.pk)


@login_required
def unread_count_api(request):
    """API для badge уведомлений (опрос из JS)."""
    return JsonResponse({'count': unread_messages_count(request.user)})
