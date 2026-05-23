/**
 * Уведомления: WebSocket (сообщения + in-app) + резервный опрос API.
 */
(function () {
  const badge = document.getElementById('nav-unread-badge');
  const apiUrl = document.body.dataset.unreadApi;
  const toastEl = document.getElementById('app-toast');
  const toastTitle = document.getElementById('app-toast-title');
  const toastMessage = document.getElementById('app-toast-message');
  const toastLink = document.getElementById('app-toast-link');
  let toastInstance = null;

  function updateBadge(count) {
    if (!badge) return;
    badge.textContent = count > 99 ? '99+' : count;
    badge.classList.toggle('d-none', !count);
  }

  function poll() {
    if (!apiUrl) return;
    fetch(apiUrl, { credentials: 'same-origin' })
      .then((r) => r.json())
      .then((data) => updateBadge(data.count || 0))
      .catch(() => {});
  }

  function showToast(title, message, url) {
    if (!toastEl || !window.bootstrap) return;
    if (toastTitle) toastTitle.textContent = title || '';
    if (toastMessage) toastMessage.textContent = message || '';
    if (toastLink) {
      if (url) {
        toastLink.href = url;
        toastLink.classList.remove('d-none');
      } else {
        toastLink.classList.add('d-none');
      }
    }
    if (!toastInstance) {
      toastInstance = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 8000 });
    }
    toastInstance.show();
  }

  const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  let socket;

  function connectWs() {
    socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/notifications/`);

    socket.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }
      if (data.type === 'unread') {
        updateBadge(data.count || 0);
        document.dispatchEvent(new CustomEvent('chat:notify', { detail: data }));
      }
      if (data.type === 'notification') {
        document.dispatchEvent(new CustomEvent('app:notification', { detail: data }));
        showToast(data.title, data.message, data.url);
      }
    };

    socket.onclose = () => {
      setTimeout(connectWs, 4000);
      poll();
    };

    socket.onerror = () => poll();
  }

  if (badge) {
    connectWs();
    poll();
  }
})();
