/**
 * Реал-тайм аукцион: WebSocket, обновление цены.
 * История ставок — только у автора (showBidHistory).
 */
(function () {
  const cfg = window.AUCTION_CONFIG;
  if (!cfg) return;

  const priceEl = document.getElementById('auction-current-price');
  const minBidLabel = document.getElementById('min-bid-label');
  const bidsList = document.getElementById('bids-list');
  const bidsEmpty = document.getElementById('bids-empty');
  const form = document.getElementById('auction-bid-form');
  const amountInput = document.getElementById('bid-amount');
  const showHistory = Boolean(cfg.showBidHistory);

  let socket = null;

  function wsUrl() {
    return `${cfg.wsScheme}://${cfg.wsHost}/ws/auction/${cfg.adId}/`;
  }

  const auctionBase = Number(cfg.auctionBase) || 0;
  const auctionStep = Number(cfg.auctionStep) || 1;

  function formatRubles(value) {
    const n = Math.round(Number(value));
    return Number.isFinite(n) ? String(n) : String(value);
  }

  function isOnGrid(amount) {
    return amount >= auctionBase && (amount - auctionBase) % auctionStep === 0;
  }

  function syncBidInput(minBid) {
    if (!amountInput) return;
    amountInput.min = formatRubles(minBid);
    amountInput.step = String(auctionStep);
  }

  function connect() {
    socket = new WebSocket(wsUrl());

    socket.onclose = () => setTimeout(connect, 3000);

    socket.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }
      if (data.type === 'state') applyState(data);
      if (data.type === 'bid') applyBid(data);
      if (data.type === 'finished') applyFinished(data);
      if (data.type === 'error') alert(data.detail || 'Ошибка');
    };
  }

  function applyState(data) {
    if (priceEl && data.current_price) priceEl.textContent = `${formatRubles(data.current_price)} ₽`;
    if (minBidLabel && data.min_bid) minBidLabel.textContent = formatRubles(data.min_bid);
    if (data.min_bid) syncBidInput(data.min_bid);
    if (showHistory && data.bids) renderBids(data.bids);
  }

  function applyBid(data) {
    if (priceEl && data.current_price) priceEl.textContent = `${formatRubles(data.current_price)} ₽`;
    if (minBidLabel && data.min_bid) minBidLabel.textContent = formatRubles(data.min_bid);
    if (data.min_bid) syncBidInput(data.min_bid);
    if (amountInput) amountInput.value = '';
    if (showHistory && data.bid) prependBid(data.bid);
  }

  function applyFinished(data) {
    const status = document.getElementById('auction-status-text');
    if (status && data.winner) {
      status.innerHTML = `Завершён. Победитель: <strong>${data.winner}</strong>`;
    }
    if (form) form.remove();
  }

  function prependBid(bid) {
    if (!bidsList) return;
    if (bidsEmpty) bidsEmpty.remove();
    const li = document.createElement('li');
    li.className = 'bid-row d-flex justify-content-between small';
    const d = new Date(bid.created_at);
    const time = d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
    li.innerHTML = `<span><strong>${bid.bidder}</strong></span><span>${formatRubles(bid.amount)} ₽ · ${time}</span>`;
    bidsList.prepend(li);
  }

  function renderBids(bids) {
    if (!bidsList) return;
    bidsList.innerHTML = '';
    if (!bids.length) {
      const li = document.createElement('li');
      li.className = 'text-muted-custom small';
      li.id = 'bids-empty';
      li.textContent = 'Ставок пока нет.';
      bidsList.appendChild(li);
      return;
    }
    bids.forEach((b) => prependBid(b));
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const raw = amountInput.value.trim().replace(',', '.');
      if (!raw) return;
      const amount = Number(raw);
      if (!Number.isInteger(amount) || amount < 0) {
        alert('Укажите целое число рублей, без копеек.');
        return;
      }
      if (!isOnGrid(amount)) {
        alert(
          `Ставка кратна шагу ${auctionStep} ₽ от стартовой цены ${auctionBase} ₽ ` +
            `(например ${auctionBase}, ${auctionBase + auctionStep}…).`
        );
        return;
      }
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: 'place_bid', amount }));
      } else {
        form.submit();
      }
    });
  }

  connect();
})();
