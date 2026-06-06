const DEFAULT_PARAMETERS = Object.freeze({
  preset: "natural-negative",
  preset_strength: 1,
  exposure: 0,
  contrast: 0,
  highlights: 0,
  shadows: 0,
  temperature: 0,
  saturation: 0,
  halation: 0,
  grain: 0,
  vignette: 0,
  lut_id: null,
});

const state = {
  assets: [],
  selectedId: null,
  previewTimer: null,
  previewSequence: 0,
  activeJobId: null,
  jobPollTimer: null,
  lastJobStatus: null,
  statusTimer: null,
};

const elements = {
  photoInput: document.querySelector("#photo-input"),
  lutInput: document.querySelector("#lut-input"),
  lutName: document.querySelector("#lut-name"),
  dropZone: document.querySelector("#drop-zone"),
  previewCanvas: document.querySelector("#preview-canvas"),
  previewStage: document.querySelector("#preview-stage"),
  originalImage: document.querySelector("#original-image"),
  processedImage: document.querySelector("#processed-image"),
  processedLayer: document.querySelector("#processed-layer"),
  splitDivider: document.querySelector("#split-divider"),
  previewLoading: document.querySelector("#preview-loading"),
  imageMeta: document.querySelector("#image-meta"),
  presetList: document.querySelector("#preset-list"),
  queueItems: document.querySelector("#queue-items"),
  assetCount: document.querySelector("#asset-count"),
  exportButton: document.querySelector("#export-button"),
  resetButton: document.querySelector("#reset-button"),
  applyAllButton: document.querySelector("#apply-all-button"),
  statusRegion: document.querySelector("#status-region"),
  jobLabel: document.querySelector("#job-label"),
  jobProgress: document.querySelector("#job-progress"),
  exportStatus: document.querySelector(".export-status"),
  cancelJobButton: document.querySelector("#cancel-job-button"),
  retryJobButton: document.querySelector("#retry-job-button"),
  downloadLink: document.querySelector("#download-link"),
};

function selectedAsset() {
  return state.assets.find((asset) => asset.id === state.selectedId) || null;
}

function cloneDefaults() {
  return { ...DEFAULT_PARAMETERS };
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `请求失败 (${response.status})`;
    try {
      const payload = await response.json();
      message = payload.error || message;
    } catch {
      // Keep the HTTP fallback when the response is not JSON.
    }
    throw new Error(message);
  }
  return response;
}

function showStatus(message, isError = false) {
  clearTimeout(state.statusTimer);
  elements.statusRegion.textContent = message;
  elements.statusRegion.classList.toggle("is-error", isError);
  elements.statusRegion.classList.add("is-visible");
  state.statusTimer = window.setTimeout(() => {
    elements.statusRegion.classList.remove("is-visible");
  }, isError ? 5200 : 2600);
}

async function uploadFiles(files) {
  const accepted = Array.from(files || []).filter((file) => file.size > 0);
  if (!accepted.length) {
    return;
  }

  const formData = new FormData();
  accepted.forEach((file) => formData.append("files", file));
  showStatus(`正在读取 ${accepted.length} 张照片…`);

  try {
    const response = await apiFetch("/api/assets", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    const newAssets = payload.assets.map((asset) => ({
      ...asset,
      parameters: cloneDefaults(),
      previewUrl: null,
      previewVersion: 0,
      exportStatus: "待处理",
    }));
    state.assets.push(...newAssets);
    if (!state.selectedId && newAssets.length) {
      selectAsset(newAssets[0].id);
    }
    renderQueue();
    updateEnabledState();
    showStatus(`已添加 ${newAssets.length} 张照片`);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    elements.photoInput.value = "";
  }
}

function selectAsset(assetId) {
  const asset = state.assets.find((item) => item.id === assetId);
  if (!asset) {
    return;
  }
  state.selectedId = assetId;
  elements.dropZone.hidden = true;
  elements.previewStage.hidden = false;
  elements.originalImage.src = asset.thumbnail_url;
  elements.processedImage.src = asset.previewUrl || asset.thumbnail_url;
  elements.imageMeta.textContent = `${asset.original_name} · ${asset.width} × ${asset.height}`;
  syncControlsFromAsset(asset);
  renderQueue();
  updateEnabledState();
  if (!asset.previewUrl) {
    schedulePreview();
  }
}

function syncControlsFromAsset(asset) {
  document.querySelectorAll("[data-param]").forEach((input) => {
    input.value = asset.parameters[input.dataset.param];
  });
  document.querySelectorAll("[data-preset]").forEach((button) => {
    button.classList.toggle(
      "is-selected",
      button.dataset.preset === asset.parameters.preset,
    );
  });
  elements.lutName.textContent = asset.lutName || "未载入";
}

function updateParameter(name, value) {
  const asset = selectedAsset();
  if (!asset) {
    return;
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return;
  }
  asset.parameters[name] = numeric;
  document.querySelectorAll(`[data-param="${name}"]`).forEach((input) => {
    if (input.value !== String(numeric)) {
      input.value = String(numeric);
    }
  });
  schedulePreview();
}

function schedulePreview() {
  const asset = selectedAsset();
  if (!asset) {
    return;
  }
  const version = ++state.previewSequence;
  asset.previewVersion = version;
  clearTimeout(state.previewTimer);
  elements.previewLoading.hidden = false;
  state.previewTimer = window.setTimeout(() => {
    requestPreview(asset.id, version);
  }, 180);
}

async function requestPreview(assetId, version) {
  const asset = state.assets.find((item) => item.id === assetId);
  if (!asset) {
    return;
  }

  try {
    const response = await apiFetch(`/api/assets/${assetId}/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        version,
        parameters: asset.parameters,
      }),
    });
    const responseVersion = Number(response.headers.get("X-Preview-Version"));
    const blob = await response.blob();
    if (asset.previewVersion !== version || responseVersion !== version) {
      return;
    }
    if (asset.previewUrl) {
      URL.revokeObjectURL(asset.previewUrl);
    }
    asset.previewUrl = URL.createObjectURL(blob);
    if (state.selectedId === assetId) {
      elements.processedImage.src = asset.previewUrl;
    }
  } catch (error) {
    if (asset.previewVersion === version) {
      showStatus(error.message, true);
    }
  } finally {
    if (asset.previewVersion === version) {
      elements.previewLoading.hidden = true;
    }
  }
}

function renderQueue() {
  elements.assetCount.textContent = String(state.assets.length);
  elements.queueItems.replaceChildren();
  if (!state.assets.length) {
    const empty = document.createElement("span");
    empty.className = "queue-empty";
    empty.textContent = "尚未添加照片";
    elements.queueItems.append(empty);
    return;
  }

  state.assets.forEach((asset) => {
    const item = document.createElement("div");
    item.className = "queue-item";
    item.classList.toggle("is-selected", asset.id === state.selectedId);
    item.dataset.assetId = asset.id;
    item.tabIndex = 0;
    item.setAttribute("role", "button");
    item.setAttribute("aria-label", `选择 ${asset.original_name}`);

    const image = document.createElement("img");
    image.src = asset.thumbnail_url;
    image.alt = "";

    const name = document.createElement("span");
    name.className = "queue-item-name";
    name.textContent = asset.original_name;

    const status = document.createElement("span");
    status.className = "queue-item-status";
    status.textContent = asset.exportStatus;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "remove-asset";
    remove.title = "移除照片";
    remove.setAttribute("aria-label", `移除 ${asset.original_name}`);
    remove.textContent = "×";

    item.append(image, name, status, remove);
    item.addEventListener("click", (event) => {
      if (event.target.closest(".remove-asset")) {
        event.stopPropagation();
        removeAsset(asset.id);
        return;
      }
      selectAsset(asset.id);
    });
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectAsset(asset.id);
      }
    });
    elements.queueItems.append(item);
  });
}

async function removeAsset(assetId) {
  try {
    await apiFetch(`/api/assets/${assetId}`, { method: "DELETE" });
    const index = state.assets.findIndex((asset) => asset.id === assetId);
    const [removed] = state.assets.splice(index, 1);
    if (removed?.previewUrl) {
      URL.revokeObjectURL(removed.previewUrl);
    }
    if (state.selectedId === assetId) {
      state.selectedId = null;
      if (state.assets.length) {
        selectAsset(state.assets[Math.min(index, state.assets.length - 1)].id);
      } else {
        showEmptyWorkspace();
      }
    }
    renderQueue();
    updateEnabledState();
    showStatus("照片已移除");
  } catch (error) {
    showStatus(error.message, true);
  }
}

function showEmptyWorkspace() {
  elements.dropZone.hidden = false;
  elements.previewStage.hidden = true;
  elements.imageMeta.textContent = "等待照片";
  elements.lutName.textContent = "未载入";
}

function updateEnabledState() {
  const hasAsset = Boolean(selectedAsset());
  const hasAssets = state.assets.length > 0;
  elements.exportButton.disabled = !hasAssets || Boolean(state.activeJobId);
  elements.resetButton.disabled = !hasAsset;
  elements.applyAllButton.disabled = !hasAsset || state.assets.length < 2;
  document.querySelectorAll("[data-param]").forEach((input) => {
    input.disabled = !hasAsset;
  });
}

async function uploadLut(file) {
  const asset = selectedAsset();
  if (!asset || !file) {
    return;
  }
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await apiFetch("/api/luts", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    asset.parameters.lut_id = payload.lut.id;
    asset.lutName = payload.lut.name;
    elements.lutName.textContent = payload.lut.name;
    schedulePreview();
    showStatus(`已载入 ${payload.lut.name}`);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    elements.lutInput.value = "";
  }
}

function resetCurrent() {
  const asset = selectedAsset();
  if (!asset) {
    return;
  }
  asset.parameters = cloneDefaults();
  asset.lutName = null;
  syncControlsFromAsset(asset);
  schedulePreview();
  showStatus("当前照片参数已重置");
}

function applyCurrentToAll() {
  const asset = selectedAsset();
  if (!asset) {
    return;
  }
  state.assets.forEach((item) => {
    if (item.id !== asset.id) {
      item.parameters = { ...asset.parameters };
      item.lutName = asset.lutName;
      item.previewVersion = ++state.previewSequence;
      if (item.previewUrl) {
        URL.revokeObjectURL(item.previewUrl);
        item.previewUrl = null;
      }
    }
  });
  renderQueue();
  showStatus(`参数已应用到 ${state.assets.length} 张照片`);
}

async function startExport() {
  if (!state.assets.length || state.activeJobId) {
    return;
  }
  const parametersByAsset = Object.fromEntries(
    state.assets.map((asset) => [asset.id, asset.parameters]),
  );
  try {
    const response = await apiFetch("/api/exports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asset_ids: state.assets.map((asset) => asset.id),
        parameters_by_asset: parametersByAsset,
      }),
    });
    const payload = await response.json();
    state.activeJobId = payload.job_id;
    state.lastJobStatus = "pending";
    delete elements.retryJobButton.dataset.jobId;
    state.assets.forEach((asset) => {
      asset.exportStatus = "等待导出";
    });
    resetDownload();
    elements.cancelJobButton.disabled = false;
    elements.retryJobButton.disabled = true;
    elements.exportStatus.classList.add("is-active");
    updateEnabledState();
    renderQueue();
    pollJob();
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function pollJob() {
  if (!state.activeJobId) {
    return;
  }
  try {
    const response = await apiFetch(`/api/jobs/${state.activeJobId}`);
    const { job } = await response.json();
    state.lastJobStatus = job.status;
    elements.jobProgress.value = job.progress || 0;
    elements.jobLabel.textContent = jobStatusLabel(job);
    state.assets.forEach((asset) => {
      asset.exportStatus = job.status === "completed"
        ? "已完成"
        : job.status === "failed"
          ? "导出失败"
          : job.status === "cancelled"
            ? "已取消"
            : `${Math.round((job.progress || 0) * 100)}%`;
    });
    renderQueue();

    if (!["completed", "failed", "cancelled"].includes(job.status)) {
      state.jobPollTimer = window.setTimeout(pollJob, 350);
      return;
    }

    const terminalJobId = state.activeJobId;
    elements.cancelJobButton.disabled = true;
    state.activeJobId = null;
    if (job.status === "completed") {
      const completedJobId = job.id;
      elements.downloadLink.href = `/api/jobs/${completedJobId}/download`;
      elements.downloadLink.classList.remove("is-disabled");
      elements.downloadLink.setAttribute("aria-disabled", "false");
      elements.retryJobButton.disabled = true;
      showStatus("导出完成，可以下载");
    } else {
      elements.retryJobButton.dataset.jobId = terminalJobId;
      elements.retryJobButton.disabled = false;
      showStatus(job.error || jobStatusLabel(job), job.status === "failed");
    }
    updateEnabledState();
  } catch (error) {
    state.activeJobId = null;
    elements.cancelJobButton.disabled = true;
    elements.retryJobButton.disabled = false;
    updateEnabledState();
    showStatus(error.message, true);
  }
}

function jobStatusLabel(job) {
  const labels = {
    pending: "等待导出",
    decoding: "读取照片",
    running: `正在导出 ${Math.round((job.progress || 0) * 100)}%`,
    completed: "导出完成",
    failed: "导出失败",
    cancelled: "导出已取消",
  };
  return labels[job.status] || job.status;
}

async function cancelJob() {
  if (!state.activeJobId) {
    return;
  }
  try {
    await apiFetch(`/api/jobs/${state.activeJobId}/cancel`, { method: "POST" });
    showStatus("正在取消导出");
  } catch (error) {
    showStatus(error.message, true);
  }
}

async function retryJob() {
  const jobId = elements.retryJobButton.dataset.jobId;
  if (!jobId) {
    startExport();
    return;
  }
  try {
    const response = await apiFetch(`/api/jobs/${jobId}/retry`, {
      method: "POST",
    });
    const payload = await response.json();
    state.activeJobId = payload.job_id;
    delete elements.retryJobButton.dataset.jobId;
    elements.retryJobButton.disabled = true;
    elements.cancelJobButton.disabled = false;
    updateEnabledState();
    pollJob();
  } catch (error) {
    showStatus(error.message, true);
  }
}

function resetDownload() {
  elements.downloadLink.href = "#";
  elements.downloadLink.classList.add("is-disabled");
  elements.downloadLink.setAttribute("aria-disabled", "true");
}

function setViewMode(mode) {
  elements.previewCanvas.dataset.mode = mode;
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.view === mode);
  });
}

function updateSplitPosition(clientX) {
  const bounds = elements.previewStage.getBoundingClientRect();
  if (!bounds.width) {
    return;
  }
  const percent = Math.min(
    100,
    Math.max(0, ((clientX - bounds.left) / bounds.width) * 100),
  );
  elements.previewStage.style.setProperty("--split-position", `${percent}%`);
}

function setMobilePanel(panel) {
  const current = document.body.dataset.mobilePanel;
  document.body.dataset.mobilePanel = current === panel ? "" : panel;
  document.querySelectorAll("[data-mobile-panel]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(document.body.dataset.mobilePanel === button.dataset.mobilePanel),
    );
  });
}

elements.photoInput.addEventListener("change", (event) => {
  uploadFiles(event.target.files);
});

elements.lutInput.addEventListener("change", (event) => {
  uploadLut(event.target.files[0]);
});

document.addEventListener("dragover", (event) => {
  event.preventDefault();
  elements.dropZone.classList.add("is-dragging");
});

document.addEventListener("dragleave", (event) => {
  if (!event.relatedTarget) {
    elements.dropZone.classList.remove("is-dragging");
  }
});

document.addEventListener("drop", (event) => {
  event.preventDefault();
  elements.dropZone.classList.remove("is-dragging");
  uploadFiles(event.dataTransfer.files);
});

elements.presetList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-preset]");
  const asset = selectedAsset();
  if (!button || !asset) {
    return;
  }
  asset.parameters.preset = button.dataset.preset;
  syncControlsFromAsset(asset);
  schedulePreview();
});

document.querySelectorAll("[data-param]").forEach((input) => {
  input.addEventListener("input", () => {
    updateParameter(input.dataset.param, input.value);
  });
});

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => setViewMode(button.dataset.view));
});

document.querySelectorAll("[data-mobile-panel]").forEach((button) => {
  button.addEventListener("click", () => setMobilePanel(button.dataset.mobilePanel));
});

elements.previewStage.addEventListener("pointerdown", (event) => {
  if (elements.previewCanvas.dataset.mode !== "split") {
    return;
  }
  elements.previewStage.setPointerCapture(event.pointerId);
  updateSplitPosition(event.clientX);
});

elements.previewStage.addEventListener("pointermove", (event) => {
  if (
    elements.previewCanvas.dataset.mode === "split"
    && elements.previewStage.hasPointerCapture(event.pointerId)
  ) {
    updateSplitPosition(event.clientX);
  }
});

elements.resetButton.addEventListener("click", resetCurrent);
elements.applyAllButton.addEventListener("click", applyCurrentToAll);
elements.exportButton.addEventListener("click", startExport);
elements.cancelJobButton.addEventListener("click", cancelJob);
elements.retryJobButton.addEventListener("click", retryJob);

window.addEventListener("beforeunload", () => {
  state.assets.forEach((asset) => {
    if (asset.previewUrl) {
      URL.revokeObjectURL(asset.previewUrl);
    }
  });
});

updateEnabledState();
