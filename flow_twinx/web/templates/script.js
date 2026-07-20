const audio = document.getElementById("audioPlayer");
const playBtn = document.getElementById("playBtn");
const miniPlayBtn = document.getElementById("miniPlayBtn");
const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const shuffleBtn = document.getElementById("shuffleBtn");
const repeatBtn = document.getElementById("repeatBtn");
const progressFill = document.getElementById("progressFill");
const progressBar = document.getElementById("progressBar");
const currentTime = document.getElementById("currentTime");
const totalTime = document.getElementById("totalTime");
const volumeSlider = document.getElementById("volumeSlider");
const albumArt = document.getElementById("albumArt");
const trackTitle = document.getElementById("trackTitle");
const trackArtist = document.getElementById("trackArtist");
const playerBg = document.getElementById("playerBg");
const miniArt = document.getElementById("miniArt");
const miniTitle = document.getElementById("miniTitle");
const miniArtist = document.getElementById("miniArtist");
const miniPlayer = document.getElementById("miniPlayer");
const playerMain = document.getElementById("playerMain");
const miniExpandBtn = document.getElementById("miniExpandBtn");
const settingsModal = document.getElementById("settingsModal");
const settingsBtn = document.getElementById("settingsBtn");
const closeSettings = document.getElementById("closeSettings");
const saveSettings = document.getElementById("saveSettings");
const resetSettingsBtn = document.getElementById("resetSettings");
const searchInput = document.getElementById("searchInput");
const resultsContainer = document.getElementById("resultsContainer");
const srcYt = document.getElementById("srcYt");
const srcLocal = document.getElementById("srcLocal");
const clearQueueBtn = document.getElementById("clearQueueBtn");
const queueContainer = document.getElementById("queueContainer");
const scanLocalBtn = document.getElementById("scanLocalBtn");
const albumsGrid = document.getElementById("albumsGrid");
const albumSongs = document.getElementById("albumSongs");
const localSongsContainer = document.getElementById("localSongs");
const queueBar = document.getElementById("queueBar");
const queueBarTitle = document.getElementById("queueBarTitle");
const queueBarCount = document.getElementById("queueBarCount");
const queueBarArt = document.getElementById("queueBarArt");
const queueBarExpand = document.getElementById("queueBarExpand");
const queueOverlay = document.getElementById("queueOverlay");
const queueOverlayClose = document.getElementById("queueOverlayClose");
const autoPlayToggle = document.getElementById("autoPlayToggle");
const downloadBtn = document.getElementById("downloadBtn");
const toastEl = document.getElementById("toast");
const setDownloadPath = document.getElementById("setDownloadPath");

let queue = [];
let queueIndex = -1;
let playHistory = [];
let isPlaying = false;
let isShuffled = false;
let repeatMode = 0; // 0=off, 1=repeat-one, 2=repeat-all
let autoPlay = true;
let searchSource = "youtube";
let activeTab = "search";
let localTracks = [];
let currentTrackType = null;

let settings = {
  theme: "dark",
  accent: "#6c63ff",
  bgBlur: 10,
  bgDim: 60,
  defaultVolume: 80,
  crossfade: 2,
  miniOnBlur: false,
  defaultSource: "youtube",
};

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

let searchTimer = null;

function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => doSearch(), 800);
}

searchInput.addEventListener("input", debounceSearch);

searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    clearTimeout(searchTimer);
    doSearch();
  }
});

function doSearch() {
  const q = searchInput.value.trim();
  if (q.length < 2) {
    resultsContainer.innerHTML = "";
    return;
  }
  if (searchSource === "youtube") {
    searchYouTube(q);
  } else {
    searchLocal(q);
  }
}

srcYt.addEventListener("click", () => setSearchSource("youtube"));
srcLocal.addEventListener("click", () => setSearchSource("local"));

function setSearchSource(source) {
  searchSource = source;
  srcYt.classList.toggle("active", source === "youtube");
  srcLocal.classList.toggle("active", source === "local");
  doSearch();
}

playBtn.addEventListener("click", togglePlay);
miniPlayBtn.addEventListener("click", togglePlay);
prevBtn.addEventListener("click", prevTrack);
nextBtn.addEventListener("click", nextTrack);
shuffleBtn.addEventListener("click", toggleShuffle);
repeatBtn.addEventListener("click", toggleRepeat);
volumeSlider.addEventListener("input", (e) => {
  audio.volume = e.target.value / 100;
});
audio.addEventListener("timeupdate", updateProgress);
audio.addEventListener("loadedmetadata", updateTotalTime);
audio.addEventListener("ended", handleEnd);
audio.addEventListener("play", () => updatePlayBtn(true));
audio.addEventListener("pause", () => updatePlayBtn(false));
audio.addEventListener("error", () => {
  console.error("Playback error, trying next");
  nextTrack();
});

progressBar.addEventListener("click", (e) => {
  const rect = progressBar.getBoundingClientRect();
  const pct = (e.clientX - rect.left) / rect.width;
  audio.currentTime = pct * audio.duration;
});

clearQueueBtn.addEventListener("click", clearQueue);
document.getElementById("saveQueueBtn").addEventListener("click", saveQueue);
scanLocalBtn.addEventListener("click", scanLocal);

miniExpandBtn.addEventListener("click", () => {
  miniPlayer.style.display = "none";
  playerMain.style.display = "flex";
  document.querySelector(".sidebar").style.width = "";
  document.querySelector(".sidebar").style.minWidth = "";
  document.querySelector(".sidebar").style.display = "";
});

settingsBtn.addEventListener("click", () =>
  settingsModal.classList.add("open"),
);
closeSettings.addEventListener("click", () =>
  settingsModal.classList.remove("open"),
);
settingsModal.addEventListener("click", (e) => {
  if (e.target === settingsModal) settingsModal.classList.remove("open");
});
saveSettings.addEventListener("click", saveSettingsToAPI);
resetSettingsBtn.addEventListener("click", resetSettings);

autoPlayToggle.addEventListener("change", (e) => {
  autoPlay = e.target.checked;
  if (!autoPlay) {
    if (queueIndex >= 0 && queue[queueIndex]) {
      const currentTrack = queue[queueIndex];
      queue = queue.filter((song, idx) => idx === queueIndex || !song._autoAdded);
      queueIndex = queue.indexOf(currentTrack);
    } else {
      queue = queue.filter((song) => !song._autoAdded);
      if (queueIndex >= queue.length) queueIndex = queue.length - 1;
    }
    renderQueue();
  }
});

queueBar.addEventListener("click", (e) => {
  if (
    e.target.closest(".autoplay-toggle") ||
    e.target.closest("#queueBarExpand")
  )
    return;
  toggleQueueOverlay();
});

queueBarExpand.addEventListener("click", (e) => {
  e.stopPropagation();
  toggleQueueOverlay();
});

queueOverlayClose.addEventListener("click", () => {
  queueOverlay.classList.remove("open");
  queueBarExpand.classList.remove("open");
});

function toggleQueueOverlay() {
  const isOpen = queueOverlay.classList.toggle("open");
  queueBarExpand.classList.toggle("open", isOpen);
}

function setTab(tab) {
  activeTab = tab;
  document
    .querySelectorAll(".sidebar-tabs .tab")
    .forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
  const tabId = "tab" + tab.charAt(0).toUpperCase() + tab.slice(1);
  document.querySelectorAll(".sidebar-content .tab-content").forEach((t) => {
    t.classList.toggle("active", t.id === tabId);
  });
}

document.querySelectorAll(".sidebar-tabs .tab").forEach((tab) => {
  if (tab.dataset.tab) {
    tab.addEventListener("click", () => setTab(tab.dataset.tab));
  }
});

document.addEventListener("visibilitychange", () => {
  if (
    settings.miniOnBlur &&
    document.hidden &&
    playerMain.style.display !== "none"
  ) {
    goMini();
  }
});


function togglePlay() {
  if (audio.paused) {
    if (audio.src && audio.src !== "") {
      audio.play();
    } else if (queue.length > 0 && queueIndex >= 0) {
      loadAndPlay(queue[queueIndex]);
    } else if (queue.length > 0) {
      queueIndex = 0;
      loadAndPlay(queue[0]);
    }
  } else {
    audio.pause();
  }
}

function updatePlayBtn(playing) {
  isPlaying = playing;
  const icon = playing ? "bi bi-pause-fill" : "bi bi-play-fill";
  playBtn.querySelector("i").className = icon;
  miniPlayBtn.querySelector("i").className = icon;
  document.body.classList.toggle("playing", playing);
}

function loadAndPlay(track) {
  if (!track) return;
  currentTrackType = track.source || "yt";
  let src = "";
  if (currentTrackType === "local") {
    src = "/local/" + encodeURI(track.path).slice(1);
    track.thumbnail = track.thumbnail || "";
    track.channel = track.channel || track.album || "Local Music";
  } else {
    src = track.stream_url || `/play?video_id=${track.video_id}`;
  }
  audio.src = src;
  audio.play().catch((e) => {
    if (track.video_id && currentTrackType !== "local") {
      fetch(`/play?video_id=${track.video_id}`)
        .then((r) => r.json())
        .then((data) => {
          if (data.stream_url) {
            audio.src = data.stream_url;
            audio.play();
          }
        });
    }
  });

  setDisplayInfo(track);
  updateActiveCard(track);
  updateMiniPlayer(track);
  updateBg(track.thumbnail);
  updateQueueBar();

  if (autoPlay && currentTrackType !== "local" && track.video_id) {
    autoLoadRecommendations(track.video_id);
  }
}

function setDisplayInfo(track) {
  trackTitle.textContent = track.title || "Unknown";
  trackArtist.textContent = track.channel || track.artist || "";
  albumArt.src =
    track.thumbnail && track.thumbnail.trim() !== ""
      ? track.thumbnail
      : "/static/Frame%201.jpg";
}

function updateMiniPlayer(track) {
  miniArt.src =
    track.thumbnail && track.thumbnail.trim() !== ""
      ? track.thumbnail
      : "/static/Frame%201.jpg";
  miniTitle.textContent = track.title || "Unknown";
  miniArtist.textContent = track.channel || track.artist || "";
}

function updateBg(url) {
  if (url && url.trim() !== "") {
    playerBg.style.backgroundImage = `url(${url})`;
  } else {
    playerBg.style.backgroundImage = "none";
  }
}

function updateActiveCard(track) {
  document
    .querySelectorAll(".song-card")
    .forEach((c) => c.classList.remove("active"));
  const cards = document.querySelectorAll(".song-card");
  cards.forEach((c) => {
    const t = c.dataset.title;
    const id = c.dataset.videoId || c.dataset.path;
    if (t === track.title && id === (track.video_id || track.path)) {
      c.classList.add("active");
    }
  });
}

function updateProgress() {
  if (!audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  progressFill.style.width = pct + "%";
  currentTime.textContent = formatTime(audio.currentTime);
}

function updateTotalTime() {
  totalTime.textContent = formatTime(audio.duration);
}

function formatTime(s) {
  if (isNaN(s) || !isFinite(s)) return "0:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

let lastRecommendationId = null;
let recommendationLoading = false;

function autoLoadRecommendations(videoId) {
  if (!videoId || recommendationLoading) return;
  const songsRemaining = queue.length - queueIndex - 1;
  if (songsRemaining >= 5) return;
  if (videoId === lastRecommendationId) return;
  lastRecommendationId = videoId;
  recommendationLoading = true;
  fetch(`/recommend?video_id=${encodeURIComponent(videoId)}&limit=20`)
    .then((r) => r.json())
    .then((data) => {
      const results = data.results || [];
      const existingIds = new Set(queue.map((t) => t.video_id));
      let added = 0;
      results.forEach((item) => {
        if (!item.video_id || existingIds.has(item.video_id)) return;
        queue.push({ ...item, source: "yt", _autoAdded: true });
        existingIds.add(item.video_id);
        added++;
      });
      if (added > 0) renderQueue();
      recommendationLoading = false;
    })
    .catch(() => {
      recommendationLoading = false;
    });
}

function handleEnd() {
  if (repeatMode === 1) {
    audio.play();
    return;
  }
  if (!autoPlay && repeatMode !== 2) {
    updatePlayBtn(false);
    audio.currentTime = 0;
    return;
  }
  if (queueIndex < queue.length - 1 || repeatMode === 2) {
    nextTrack();
  } else {
    updatePlayBtn(false);
    audio.currentTime = 0;
  }
}

function prevTrack() {
  if (audio.currentTime > 3) {
    audio.currentTime = 0;
    return;
  }
  if (playHistory.length > 0) {
    const prev = playHistory.pop();
    if (prev) {
      loadAndPlay(prev);
      return;
    }
  }
  if (queueIndex > 0) {
    queueIndex--;
    loadAndPlay(queue[queueIndex]);
  }
}

function nextTrack() {
  const prev = queue[queueIndex];
  if (isShuffled && queue.length > 0) {
    let nextIdx;
    do {
      nextIdx = Math.floor(Math.random() * queue.length);
    } while (nextIdx === queueIndex && queue.length > 1);
    queueIndex = nextIdx;
  } else {
    if (queueIndex < queue.length - 1) {
      queueIndex++;
    } else if (repeatMode === 2) {
      queueIndex = 0;
    } else {
      return;
    }
  }
  if (prev) {
    playHistory.push(prev);
    if (playHistory.length > 50) playHistory.shift();
  }
  loadAndPlay(queue[queueIndex]);
}

function toggleShuffle() {
  isShuffled = !isShuffled;
  shuffleBtn.classList.toggle("active", isShuffled);
}

function toggleRepeat() {
  repeatMode = (repeatMode + 1) % 3;
  const icons = ["bi bi-repeat", "bi bi-repeat-1", "bi bi-repeat"];
  const titles = ["Repeat off", "Repeat one", "Repeat all"];
  repeatBtn.querySelector("i").className = icons[repeatMode];
  repeatBtn.title = titles[repeatMode];
  if (repeatMode === 0) repeatBtn.classList.remove("active");
  else repeatBtn.classList.add("active");
}

function clearQueue() {
  queue = [];
  queueIndex = -1;
  audio.pause();
  audio.src = "";
  updatePlayBtn(false);
  renderQueue();
  queueOverlay.classList.remove("open");
  queueBarExpand.classList.remove("open");
  queueBarExpand.querySelector("i").className = "bi bi-list-ul";
}


function searchYouTube(query) {
  const limit = 15;
  fetch(`/search?q=${encodeURIComponent(query)}&limit=${limit}`)
    .then((r) => r.json())
    .then((data) => {
      const res = data.results || [];
      resultsContainer.innerHTML = "";
      res.forEach((item) => {
        const card = createSongCard(item, "yt");
        card.addEventListener("click", () => playTrack(item));
        const addBtn = card.querySelector(".song-actions button");
        addBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          addToQueue(item);
        });
        resultsContainer.appendChild(card);
      });
    });
}

function searchLocal(query) {
  fetch(`/api/local-search?q=${encodeURIComponent(query)}`)
    .then((r) => r.json())
    .then((data) => {
      const res = data.results || [];
      resultsContainer.innerHTML = "";
      if (res.length === 0) {
        resultsContainer.innerHTML =
          '<div style="color: var(--text3); text-align:center; padding:20px; font-size: 13px;">No local results</div>';
        return;
      }
      res.forEach((item) => {
        const card = createSongCard(
          { ...item, thumbnail: "", channel: "Local Music", duration: 0 },
          "local",
        );
        card.addEventListener("click", () => playLocal(item));
        const addBtn = card.querySelector(".song-actions button");
        addBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          addToQueue({ ...item, source: "local" });
        });
        resultsContainer.appendChild(card);
      });
    });
}

function createSongCard(data, type) {
  const card = document.createElement("div");
  card.className = "song-card";
  card.dataset.title = data.title;
  card.dataset.videoId = data.video_id || "";
  card.dataset.path = data.path || "";
  const thumb =
    data.thumbnail && data.thumbnail.trim() !== ""
      ? data.thumbnail
      : "/static/Frame%201.jpg";
  card.innerHTML = `
    <img src="${thumb}" alt="" loading="lazy">
    <div class="song-info">
      <div class="song-title">${data.title || "Unknown"}</div>
      <div class="song-artist">${data.channel || data.artist || "Unknown"}</div>
    </div>
    ${data.duration ? `<span class="song-duration">${formatTime(data.duration)}</span>` : ""}
    <div class="song-actions">
      <button title="Add to queue"><i class="bi bi-plus-lg"></i></button>
    </div>
  `;
  return card;
}

function playTrack(item) {
  addHistory();
  queue = [item];
  queueIndex = 0;
  loadAndPlay(queue[0]);
  renderQueue();
}

function playLocal(item) {
  const entry = { ...item, source: "local", channel: "Local Music" };
  addHistory();
  queue = [entry];
  queueIndex = 0;
  loadAndPlay(queue[0]);
  renderQueue();
}

function addHistory() {
  if (queueIndex >= 0 && queue[queueIndex]) {
    playHistory.push(queue[queueIndex]);
    if (playHistory.length > 50) playHistory.shift();
  }
}

function loadIndex(arr, item) {
  return arr.findIndex(
    (a) => a.video_id === item.video_id || a.path === item.path,
  );
}

function addToQueue(item, doRender = true) {
  if (item.source === "local") {
    item.channel = item.channel || "Local Music";
  }
  queue.push(item);
  if (queueIndex === -1) {
    queueIndex = 0;
  }
  if (doRender) renderQueue();
}

function renderQueue() {
  queueContainer.innerHTML =
    queue.length === 0
      ? '<div style="color: var(--text3);text-align:center;padding:20px;font-size:13px;">Queue is empty</div>'
      : "";
  queue.forEach((item, idx) => {
    const card = document.createElement("div");
    card.className =
      "song-card" +
      (idx === queueIndex && item === queue[queueIndex] ? " active" : "");
    const thumb =
      item.thumbnail && item.thumbnail.trim() !== ""
        ? item.thumbnail
        : "/static/Frame%201.jpg";
    const dur = item.duration || "";
    card.innerHTML = `
      <img src="${thumb}" alt="" loading="lazy">
      <div class="song-info">
        <div class="song-title">${item.title}</div>
        <div class="song-artist">${item.channel || item.artist || "Unknown"}</div>
      </div>
      ${dur ? `<span class="song-duration">${formatTime(dur)}</span>` : ""}
      <div class="song-actions">
        <button class="queue-remove" data-idx="${idx}" title="Remove"><i class="bi bi-x-lg"></i></button>
      </div>
    `;
    card.addEventListener("click", () => {
      addHistory();
      queueIndex = idx;
      loadAndPlay(item);
      renderQueue();
    });
    card.querySelector(".queue-remove").addEventListener("click", (e) => {
      e.stopPropagation();
      removeFromQueue(parseInt(e.currentTarget.dataset.idx));
    });
    queueContainer.appendChild(card);
  });
  updateQueueBar();
}

function updateQueueBar() {
  const nextIdx = queueIndex + 1;
  if (queue.length > 0 && nextIdx < queue.length) {
    const nextTrack = queue[nextIdx];
    queueBarTitle.textContent = nextTrack.title || "Unknown";
    const thumb =
      nextTrack.thumbnail && nextTrack.thumbnail.trim() !== ""
        ? nextTrack.thumbnail
        : "/static/Frame%201.jpg";
    queueBarArt.src = thumb;
  } else if (queue.length > 0) {
    queueBarTitle.textContent = "End of queue";
    queueBarArt.src = "/static/Frame%201.jpg";
  } else {
    queueBarTitle.textContent = "Queue empty";
    queueBarArt.src = "/static/Frame%201.jpg";
  }
  updateQueueBarInfo();
}

function updateQueueBarInfo() {
  const nextIdx = queueIndex + 1;
  if (queue.length > 0) {
    const remaining = queue.length - nextIdx;
    queueBarCount.textContent =
      remaining > 0
        ? `${queue.length} songs \u00b7 ${remaining} next`
        : `${queue.length} song${queue.length !== 1 ? "s" : ""}`;
  } else {
    queueBarCount.textContent = "";
  }
}

function removeFromQueue(idx) {
  const wasPlaying = idx === queueIndex;
  queue.splice(idx, 1);
  if (wasPlaying) {
    if (queue.length === 0) {
      queueIndex = -1;
      audio.pause();
      audio.src = "";
      updatePlayBtn(false);
    } else {
      queueIndex = idx >= queue.length ? queue.length - 1 : idx;
      loadAndPlay(queue[queueIndex]);
    }
  } else if (idx < queueIndex) {
    queueIndex--;
  }
  renderQueue();
}


function scanLocal() {
  fetch("/offline")
    .then((r) => r.json())
    .then((data) => {
      localTracks = (data.results || []).map((t) => ({
        ...t,
        source: "local",
        channel: "Local Files",
      }));
      loadLocalTracks();
    });
  fetch("/api/albums")
    .then((r) => r.json())
    .then((data) => {
      albumsGrid.innerHTML =
        data.albums && data.albums.length
          ? ""
          : '<div style="color:var(--text3);font-size:13px;grid-column:1/-1;">No albums found</div>';
      (data.albums || []).forEach((album) => {
        const card = document.createElement("div");
        card.className = "album-card";
        card.innerHTML = `<i class="bi bi-folder2-open"></i><span>${album}</span>`;
        card.addEventListener("click", () => showAlbumSongs(album));
        albumsGrid.appendChild(card);
      });
    });
}

function showAlbumSongs(album) {
  fetch(`/api/album/${encodeURIComponent(album)}`)
    .then((r) => r.json())
    .then((data) => {
      const songs = data.results || [];
      albumSongs.innerHTML = `<div class="album-header"><button id="albumBackBtn"><i class="bi bi-arrow-left"></i></button> ${album}</div>`;
      document.getElementById("albumBackBtn").addEventListener("click", () => {
        albumSongs.innerHTML = "";
      });
      songs.forEach((item) => {
        const entry = {
          title: item.title,
          path: item.path,
          source: "local",
          channel: album,
          thumbnail: "",
        };
        const card = createSongCard(entry, "local");
        card.addEventListener("click", () => playLocal(entry));
        const addBtn = card.querySelector(".song-actions button");
        addBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          addToQueue(entry);
        });
        albumSongs.appendChild(card);
      });
    });
}

function loadLocalTracks() {
  if (localTracks.length === 0) {
    localSongsContainer.innerHTML =
      '<div style="color: var(--text3); text-align:center; padding: 20px; font-size: 13px;">No local music. <strong>Scan</strong> to load.</div>';
    return;
  }
  localSongsContainer.innerHTML = "";
  localTracks.forEach((t) => {
    const card = createSongCard(t, "local");
    card.addEventListener("click", () => playLocal(t));
    const addBtn = card.querySelector(".song-actions button");
    addBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      addToQueue(t);
    });
    localSongsContainer.appendChild(card);
  });
}

function saveQueue() {
  if (queue.length === 0) return;
  const blob = new Blob([JSON.stringify(queue, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "queue.json";
  a.click();
  URL.revokeObjectURL(url);
}

function loadLiked() {
  fetch("/api/liked")
    .then((r) => r.json())
    .then((data) => {
      const songs = data.results || [];
      const ids = data.liked_ids || [];
      const container = document.getElementById("likedSongs");
      if (!container) return;
      if (songs.length === 0 && ids.length === 0) {
        container.innerHTML =
          '<div style="color: var(--text3); text-align:center; padding: 20px; font-size: 13px;">No liked songs yet.</div>';
        return;
      }
      container.innerHTML = "";
      songs.forEach((item) => {
        const entry = {
          ...item,
          source: "local",
          channel: "Liked Songs",
          thumbnail: "",
        };
        const card = createSongCard(entry, "local");
        card.addEventListener("click", () => playLocal(entry));
        const addBtn = card.querySelector(".song-actions button");
        addBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          addToQueue(entry);
        });
        container.appendChild(card);
      });
      if (ids.length > 0 && songs.length === 0) {
        ids.forEach((vid) => {
          const item = {
            video_id: vid,
            title: vid,
            source: "yt",
            channel: "Liked",
            thumbnail: "",
            duration: 0,
          };
          const card = createSongCard(item, "yt");
          card.addEventListener("click", () => playTrack(item));
          const addBtn = card.querySelector(".song-actions button");
          addBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            addToQueue(item);
          });
          container.appendChild(card);
        });
      }
    });
}


function loadSettings() {
  fetch("/api/settings")
    .then((r) => r.json())
    .then((data) => {
      if (data && Object.keys(data).length > 0) {
        Object.assign(settings, data);
        applySettings();
        updateSettingsUI();
      }
    });
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

function lightenHex(hex, amount) {
  const { r, g, b } = hexToRgb(hex);
  const lr = Math.min(255, r + amount);
  const lg = Math.min(255, g + amount);
  const lb = Math.min(255, b + amount);
  return `#${lr.toString(16).padStart(2, "0")}${lg.toString(16).padStart(2, "0")}${lb.toString(16).padStart(2, "0")}`;
}

function applySettings() {
  document.documentElement.setAttribute("data-theme", settings.theme || "dark");
  const accent = settings.accent || "#6c63ff";
  const { r, g, b } = hexToRgb(accent);
  document.documentElement.style.setProperty("--accent", accent);
  document.documentElement.style.setProperty(
    "--accent2",
    lightenHex(accent, 30),
  );
  document.documentElement.style.setProperty(
    "--accent-glow",
    `rgba(${r},${g},${b},0.3)`,
  );
  document.documentElement.style.setProperty(
    "--bg-blur",
    (settings.bgBlur || 10) + "px",
  );
  document.documentElement.style.setProperty(
    "--bg-dim",
    (settings.bgDim || 60) / 100,
  );
  volumeSlider.value = settings.defaultVolume || 80;
  audio.volume = (settings.defaultVolume || 80) / 100;
  if (settings.defaultSource) setSearchSource(settings.defaultSource);
}

function updateSettingsUI() {
  document.getElementById("setTheme").value = settings.theme || "dark";
  document.getElementById("setAccent").value = settings.accent || "#6c63ff";
  document.getElementById("setBgBlur").value = settings.bgBlur || 10;
  document.getElementById("setBgDim").value = settings.bgDim || 60;
  document.getElementById("setVolume").value = settings.defaultVolume || 80;
  document.getElementById("setCrossfade").value = settings.crossfade || 2;
  document.getElementById("setMiniOnBlur").checked =
    settings.miniOnBlur || false;
  document.getElementById("setDefaultSource").value =
    settings.defaultSource || "youtube";
  document.getElementById("setDownloadPath").value =
    settings.downloadPath || "~/.flow/downloads";
}

function saveSettingsToAPI() {
  const newSettings = {
    theme: document.getElementById("setTheme").value,
    accent: document.getElementById("setAccent").value,
    bgBlur: parseInt(document.getElementById("setBgBlur").value),
    bgDim: parseInt(document.getElementById("setBgDim").value),
    defaultVolume: parseInt(document.getElementById("setVolume").value),
    crossfade: parseInt(document.getElementById("setCrossfade").value) || 2,
    miniOnBlur: document.getElementById("setMiniOnBlur").checked,
    defaultSource: document.getElementById("setDefaultSource").value,
    downloadPath: document.getElementById("setDownloadPath").value || "~/.flow/downloads",
  };
  fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(newSettings),
  })
    .then((r) => r.json())
    .then((data) => {
      Object.assign(settings, data.settings || newSettings);
      applySettings();
      settingsModal.classList.remove("open");
    });
}

function resetSettings() {
  settings = {
    theme: "dark",
    accent: "#6c63ff",
    bgBlur: 10,
    bgDim: 60,
    defaultVolume: 80,
    crossfade: 2,
    miniOnBlur: false,
    defaultSource: "youtube",
    downloadPath: "~/.flow/downloads",
  };
  applySettings();
  updateSettingsUI();
  fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}

function goMini() {
  playerMain.style.display = "none";
  miniPlayer.style.display = "flex";
}

function showToast(msg, duration) {
  duration = duration || 3000;
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(function () {
    toastEl.classList.remove("show");
  }, duration);
}

function downloadTrack() {
  if (queueIndex < 0 || !queue[queueIndex]) {
    showToast("No track selected");
    return;
  }
  var track = queue[queueIndex];
  var vid = track.video_id;
  if (!vid) {
    showToast("Cannot download local tracks");
    return;
  }
  var saveDir = settings.downloadPath || "~/.flow/downloads";
  downloadBtn.classList.add("downloading");
  showToast("Downloading...");
  fetch("/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: vid, save_dir: saveDir }),
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      downloadBtn.classList.remove("downloading");
      if (data.success) {
        showToast("Downloaded: " + (data.title || track.title));
      } else {
        showToast("Failed: " + (data.error || "Unknown error"));
      }
    })
    .catch(function () {
      downloadBtn.classList.remove("downloading");
      showToast("Download failed");
    });
}

downloadBtn.addEventListener("click", downloadTrack);

function goFull() {
  miniPlayer.style.display = "none";
  playerMain.style.display = "flex";
}

document.addEventListener("keydown", (e) => {
  if (e.target === searchInput) return;
  switch (e.key) {
    case " ":
    case "k":
      e.preventDefault();
      togglePlay();
      break;
    case "ArrowLeft":
      e.preventDefault();
      audio.currentTime = Math.max(0, audio.currentTime - 5);
      break;
    case "ArrowRight":
      e.preventDefault();
      audio.currentTime = Math.min(audio.duration, audio.currentTime + 5);
      break;
    case "ArrowUp":
      e.preventDefault();
      audio.volume = Math.min(1, audio.volume + 0.1);
      volumeSlider.value = audio.volume * 100;
      break;
    case "ArrowDown":
      e.preventDefault();
      audio.volume = Math.max(0, audio.volume - 0.1);
      volumeSlider.value = audio.volume * 100;
      break;
    case "n":
      nextTrack();
      break;
    case "p":
      prevTrack();
      break;
  }
});

loadSettings();
setTab("search");
scanLocal();
loadLiked();
