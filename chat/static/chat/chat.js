/**
 * Реал-тайм чат через WebSocket (Django Channels).
 * Отправка, редактирование, удаление сообщений; обновление badge в шапке.
 */
(function () {
  const cfg = window.CHAT_CONFIG;
  if (!cfg) return;

  const messagesEl = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const emptyHint = document.getElementById('empty-hint');

  let socket = null;
  let editingMessageId = null;
  const editModalEl = document.getElementById('editModal');
  const editTextEl = document.getElementById('edit-text');
  const editSaveBtn = document.getElementById('edit-save');
  let editModal = null;
  if (editModalEl && window.bootstrap) {
    editModal = new bootstrap.Modal(editModalEl);
  }

  function wsUrl() {
    return `${cfg.wsScheme}://${cfg.wsHost}/ws/chat/${cfg.chatId}/`;
  }

  function connect() {
    socket = new WebSocket(wsUrl());

    socket.onopen = () => {
      socket.send(JSON.stringify({ action: 'mark_read' }));
    };

    socket.onclose = () => {
      setTimeout(connect, 2500);
    };

    socket.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }
      if (data.type === 'message') {
        appendOrUpdateMessage(data.message, true);
        refreshNavBadge();
      } else if (data.type === 'edited') {
        appendOrUpdateMessage(data.message, false);
      } else if (data.type === 'deleted') {
        appendOrUpdateMessage(data.message, false);
      } else if (data.type === 'read') {
        (data.message_ids || []).forEach((id) => markMessageRead(id));
        refreshNavBadge();
      } else if (data.type === 'error') {
        alert(data.detail || 'Ошибка');
      }
    };
  }

  function formatTime(iso) {
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  function buildMessageRow(msg) {
    const isMine = msg.sender_id === cfg.userId;
    const row = document.createElement('div');
    row.className = `msg-row ${isMine ? 'mine' : 'theirs'}`;
    row.dataset.messageId = msg.id;
    row.dataset.senderId = msg.sender_id;

    if (isMine && !msg.is_deleted) {
      const actions = document.createElement('div');
      actions.className = 'msg-actions dropdown';
      actions.innerHTML = `
        <button class="btn btn-sm btn-link text-muted-custom p-0" data-bs-toggle="dropdown">⋯</button>
        <ul class="dropdown-menu dropdown-menu-end rounded-0 border shadow-sm">
          <li><button type="button" class="dropdown-item btn-edit-msg" data-id="${msg.id}">Редактировать</button></li>
          <li><button type="button" class="dropdown-item text-danger btn-delete-msg" data-id="${msg.id}">Удалить</button></li>
        </ul>`;
      row.appendChild(actions);
    }

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble' + (msg.is_deleted ? ' deleted' : '');
    bubble.dataset.bubble = '';

    const textEl = document.createElement('div');
    textEl.className = 'msg-text';
    textEl.textContent = msg.is_deleted ? 'Сообщение удалено' : msg.text;

    const meta = document.createElement('div');
    meta.className = 'msg-meta';

    const timeSpan = document.createElement('span');
    timeSpan.className = 'msg-time';
    timeSpan.textContent = formatTime(msg.created_at);
    meta.appendChild(timeSpan);

    if (msg.is_edited && !msg.is_deleted) {
      const editedSpan = document.createElement('span');
      editedSpan.className = 'msg-edited';
      editedSpan.textContent = 'изменено';
      meta.appendChild(editedSpan);
    }

    if (isMine && !msg.is_deleted) {
      const readSpan = document.createElement('span');
      readSpan.className = 'msg-read-status' + (msg.is_read ? ' is-read' : '');
      readSpan.textContent = msg.is_read ? 'прочитано' : 'доставлено';
      meta.appendChild(readSpan);
    }

    bubble.appendChild(textEl);
    bubble.appendChild(meta);
    row.appendChild(bubble);
    bindRowActions(row);
    return row;
  }

  function appendOrUpdateMessage(msg, scroll) {
    if (emptyHint) emptyHint.remove();
    let row = messagesEl.querySelector(`[data-message-id="${msg.id}"]`);
    if (row) {
      row.replaceWith(buildMessageRow(msg));
    } else {
      row = buildMessageRow(msg);
      messagesEl.appendChild(row);
    }
    if (scroll) scrollToBottom();
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function updateReadStatus(row, isRead) {
    if (!row.classList.contains('mine')) return;
    let status = row.querySelector('.msg-read-status');
    if (!status) {
      const meta = row.querySelector('.msg-meta');
      if (!meta) return;
      status = document.createElement('span');
      status.className = 'msg-read-status';
      meta.appendChild(status);
    }
    status.classList.toggle('is-read', isRead);
    status.textContent = isRead ? 'прочитано' : 'доставлено';
  }

  function markMessageRead(id) {
    const row = messagesEl.querySelector(`[data-message-id="${id}"]`);
    if (row) updateReadStatus(row, true);
  }

  function bindRowActions(row) {
    row.querySelectorAll('.btn-edit-msg').forEach((btn) => {
      btn.addEventListener('click', () => {
        editingMessageId = parseInt(btn.dataset.id, 10);
        const textEl = row.querySelector('.msg-text');
        editTextEl.value = textEl ? textEl.textContent : '';
        if (editModal) editModal.show();
      });
    });
    row.querySelectorAll('.btn-delete-msg').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (!confirm('Удалить сообщение?')) return;
        sendWs({ action: 'delete', message_id: parseInt(btn.dataset.id, 10) });
      });
    });
  }

  messagesEl.querySelectorAll('.msg-row').forEach((row) => {
    bindRowActions(row);
    if (row.classList.contains('mine')) {
      const status = row.querySelector('.msg-read-status.is-read');
      if (status) updateReadStatus(row, true);
    }
  });

  function sendWs(payload) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    sendWs({ action: 'send', text });
    input.value = '';
    input.style.height = 'auto';
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  if (editSaveBtn) {
    editSaveBtn.addEventListener('click', () => {
      const text = editTextEl.value.trim();
      if (!editingMessageId || !text) return;
      sendWs({ action: 'edit', message_id: editingMessageId, text });
      if (editModal) editModal.hide();
      editingMessageId = null;
    });
  }

  function refreshNavBadge() {
    if (!cfg.unreadApiUrl) return;
    fetch(cfg.unreadApiUrl, { credentials: 'same-origin' })
      .then((r) => r.json())
      .then((data) => {
        const badge = document.getElementById('nav-unread-badge');
        if (!badge) return;
        const count = data.count || 0;
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.toggle('d-none', count === 0);
      })
      .catch(() => {});
  }

  connect();
  scrollToBottom();
})();
