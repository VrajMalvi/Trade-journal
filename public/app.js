const tradeForm = document.getElementById("tradeForm");
const tradeDateInput = document.getElementById("tradeDate");
const screenshotFileInput = document.getElementById("screenshotFile");
const imagePreview = document.getElementById("imagePreview");
const imagePreviewImage = document.getElementById("imagePreviewImage");
const imagePreviewTitle = document.getElementById("imagePreviewTitle");
const imagePreviewMeta = document.getElementById("imagePreviewMeta");
const saveStatus = document.getElementById("saveStatus");
const tradeList = document.getElementById("tradeList");
const tradeDetail = document.getElementById("tradeDetail");
const searchInput = document.getElementById("searchInput");

const totalTrades = document.getElementById("totalTrades");
const winTrades = document.getElementById("winTrades");
const lossTrades = document.getElementById("lossTrades");
const winRate = document.getElementById("winRate");
const imageTrades = document.getElementById("imageTrades");

let trades = [];
let filteredTrades = [];
let selectedTradeId = null;
let previewObjectUrl = "";

function setToday() {
  tradeDateInput.value = new Date().toISOString().slice(0, 10);
}

function setStatus(message, type = "") {
  saveStatus.textContent = message;
  saveStatus.className = `status-pill${type ? ` ${type}` : ""}`;
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function present(value, fallback = "—") {
  const text = String(value ?? "").trim();
  return escapeHtml(text || fallback);
}

function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.valueOf())) {
    return value;
  }

  return parsed.toLocaleString();
}

function formatBytes(bytes) {
  if (!bytes) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** index;
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

function buildOutcomeTag(outcome = "") {
  const normalized = outcome.toLowerCase();
  const label = outcome || "Open";
  const tone = normalized || "neutral";
  return `<span class="tag ${tone}">${escapeHtml(label)}</span>`;
}

function getTradeImageUrl(trade) {
  return trade.screenshotPath || trade.screenshotLink || "";
}

function hasTradeImage(trade) {
  return Boolean(getTradeImageUrl(trade));
}

function truncate(text, maxLength = 110) {
  const value = String(text ?? "").trim();
  if (!value) {
    return "No notes yet.";
  }

  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 1)}...`;
}

function updateStats(items) {
  const wins = items.filter((trade) => trade.outcome === "Win").length;
  const losses = items.filter((trade) => trade.outcome === "Loss").length;
  const total = items.length;
  const rate = total ? Math.round((wins / total) * 100) : 0;
  const images = items.filter(hasTradeImage).length;

  totalTrades.textContent = total;
  winTrades.textContent = wins;
  lossTrades.textContent = losses;
  winRate.textContent = `${rate}%`;
  imageTrades.textContent = images;
}

function syncSelection(preferredId = selectedTradeId) {
  if (!filteredTrades.length) {
    selectedTradeId = null;
    return;
  }

  if (preferredId && filteredTrades.some((trade) => trade.id === preferredId)) {
    selectedTradeId = preferredId;
    return;
  }

  if (selectedTradeId && filteredTrades.some((trade) => trade.id === selectedTradeId)) {
    return;
  }

  selectedTradeId = filteredTrades[0].id;
}

function renderTradeList(items) {
  if (!items.length) {
    tradeList.innerHTML = `<div class="empty-list">No trades match this view yet.</div>`;
    return;
  }

  tradeList.innerHTML = items
    .map((trade) => {
      const activeClass = trade.id === selectedTradeId ? " active" : "";
      const imageBadge = hasTradeImage(trade)
        ? `<span class="meta-chip">Image</span>`
        : "";

      return `
        <button class="trade-item${activeClass}" type="button" data-trade-id="${escapeHtml(trade.id)}">
          <div class="trade-item-top">
            <div>
              <div class="trade-item-title">${present(trade.instrument)} ${present(trade.direction, "")}</div>
              <div class="trade-item-subtitle">${present(trade.account)} • ${present(trade.tradeDate)}</div>
            </div>
            ${buildOutcomeTag(trade.outcome)}
          </div>

          <div class="trade-item-meta">
            <span>${present(trade.setupType)}</span>
            <span>${present(trade.timeframe)}</span>
            <span>${present(trade.result)}</span>
            ${imageBadge}
          </div>

          <p class="trade-item-notes">${escapeHtml(truncate(trade.notes))}</p>
        </button>
      `;
    })
    .join("");
}

function buildDetailField(label, value) {
  return `
    <div class="detail-field">
      <dt>${escapeHtml(label)}</dt>
      <dd>${present(value)}</dd>
    </div>
  `;
}

function renderTradeDetail() {
  const trade = filteredTrades.find((item) => item.id === selectedTradeId);
  if (!trade) {
    tradeDetail.className = "trade-detail empty";
    tradeDetail.innerHTML = `
      <div class="empty-detail">
        <h3>No trade selected</h3>
        <p>Save or choose a trade to see the full review view here.</p>
      </div>
    `;
    return;
  }

  const imageUrl = getTradeImageUrl(trade);
  const imageSection = imageUrl
    ? `
      <div class="detail-media">
        <img class="detail-image" src="${escapeHtml(imageUrl)}" alt="Trade screenshot" />
      </div>
    `
    : `
      <div class="detail-media empty-media">
        <span>No screenshot uploaded for this trade.</span>
      </div>
    `;

  const openImageButton = imageUrl
    ? `<a class="button ghost" href="${escapeHtml(imageUrl)}" target="_blank" rel="noreferrer">Open Image</a>`
    : "";

  const detailFields = [
    ["Trade Date", trade.tradeDate],
    ["Saved At", formatDateTime(trade.createdAt)],
    ["Instrument", trade.instrument],
    ["Account", trade.account],
    ["Direction", trade.direction],
    ["Setup Type", trade.setupType],
    ["Timeframe", trade.timeframe],
    ["Entry Price", trade.entryPrice],
    ["Stop Loss", trade.stopLoss],
    ["Take Profit", trade.takeProfit],
    ["Contracts", trade.contracts],
    ["Result", trade.result],
    ["Outcome", trade.outcome],
    ["RR Ratio", trade.rrRatio],
    ["Emotion", trade.emotion],
    ["Mistake Category", trade.mistakeCategory],
    ["Screenshot File", trade.screenshotFilename]
  ]
    .map(([label, value]) => buildDetailField(label, value))
    .join("");

  tradeDetail.className = "trade-detail";
  tradeDetail.innerHTML = `
    <div class="detail-header">
      <div>
        <h3>${present(trade.instrument)} ${present(trade.direction, "")}</h3>
        <p>${present(trade.account)} • ${present(trade.tradeDate)}</p>
      </div>
      <div class="detail-header-meta">
        ${buildOutcomeTag(trade.outcome)}
      </div>
    </div>

    <div class="detail-actions">
      ${openImageButton}
      <button class="button danger" type="button" data-delete-id="${escapeHtml(trade.id)}">Delete Trade</button>
    </div>

    ${imageSection}

    <dl class="detail-grid">
      ${detailFields}
    </dl>

    <section class="detail-notes-section">
      <h4>Notes</h4>
      <p class="detail-notes">${escapeHtml(trade.notes || "No notes added yet.")}</p>
    </section>
  `;
}

function refreshView(preferredId = selectedTradeId) {
  const query = searchInput.value.trim().toLowerCase();
  if (!query) {
    filteredTrades = [...trades];
  } else {
    filteredTrades = trades.filter((trade) =>
      [
        trade.tradeDate,
        trade.instrument,
        trade.account,
        trade.direction,
        trade.setupType,
        trade.timeframe,
        trade.result,
        trade.outcome,
        trade.emotion,
        trade.mistakeCategory,
        trade.notes,
        trade.screenshotFilename
      ]
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }

  syncSelection(preferredId);
  updateStats(filteredTrades);
  renderTradeList(filteredTrades);
  renderTradeDetail();
}

async function loadTrades(preferredId = selectedTradeId) {
  const response = await fetch("/api/trades");
  trades = await response.json();
  refreshView(preferredId);
}

function clearImagePreview() {
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = "";
  }

  imagePreview.classList.add("is-empty");
  imagePreviewImage.hidden = true;
  imagePreviewImage.removeAttribute("src");
  imagePreviewTitle.textContent = "No screenshot selected";
  imagePreviewMeta.textContent = "Upload a chart image directly with the trade.";
}

function updateImagePreview() {
  const file = screenshotFileInput.files[0];
  if (!file) {
    clearImagePreview();
    return;
  }

  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
  }

  previewObjectUrl = URL.createObjectURL(file);
  imagePreview.classList.remove("is-empty");
  imagePreviewImage.hidden = false;
  imagePreviewImage.src = previewObjectUrl;
  imagePreviewTitle.textContent = file.name;
  imagePreviewMeta.textContent = `${formatBytes(file.size)} • ${file.type || "image file"}`;
}

function resetFormForNextEntry() {
  tradeForm.reset();
  setToday();
  clearImagePreview();
}

async function deleteTrade(tradeId) {
  const confirmed = window.confirm("Delete this trade?");
  if (!confirmed) {
    return;
  }

  setStatus("Deleting...");

  try {
    const response = await fetch(`/api/trades/${tradeId}`, {
      method: "DELETE"
    });

    if (!response.ok) {
      throw new Error("Delete failed");
    }

    await loadTrades();
    setStatus("Deleted", "success");
  } catch (error) {
    console.error(error);
    setStatus("Error", "error");
  }
}

tradeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Saving...");

  const formData = new FormData(tradeForm);

  try {
    const response = await fetch("/api/trades", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.message || "Save failed");
    }

    const createdTrade = await response.json();
    await loadTrades(createdTrade.id);
    resetFormForNextEntry();
    setStatus("Saved", "success");
  } catch (error) {
    console.error(error);
    setStatus("Error", "error");
    window.alert(error.message || "Could not save the trade.");
  }
});

tradeForm.addEventListener("reset", () => {
  window.setTimeout(() => {
    setToday();
    clearImagePreview();
    setStatus("Ready");
  }, 0);
});

screenshotFileInput.addEventListener("change", updateImagePreview);
searchInput.addEventListener("input", () => refreshView());

tradeList.addEventListener("click", (event) => {
  const tradeButton = event.target.closest("[data-trade-id]");
  if (!tradeButton) {
    return;
  }

  selectedTradeId = tradeButton.dataset.tradeId;
  renderTradeList(filteredTrades);
  renderTradeDetail();
});

tradeDetail.addEventListener("click", (event) => {
  const deleteButton = event.target.closest("[data-delete-id]");
  if (!deleteButton) {
    return;
  }

  deleteTrade(deleteButton.dataset.deleteId);
});

setToday();
clearImagePreview();
loadTrades().catch((error) => {
  console.error(error);
  setStatus("Error", "error");
});
