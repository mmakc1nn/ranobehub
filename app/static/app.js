const textEl = document.getElementById("text");
const languageEl = document.getElementById("language");
const speakerEl = document.getElementById("speaker");
const rateEl = document.getElementById("rate");
const rateValueEl = document.getElementById("rateValue");
const speakBtn = document.getElementById("speak");
const statusEl = document.getElementById("status");
const playerEl = document.getElementById("player");
const downloadEl = document.getElementById("download");

let currentObjectUrl = null;

function setStatus(message) {
  statusEl.textContent = message;
}

async function loadLanguages() {
  const res = await fetch("/api/languages");
  const data = await res.json();
  languageEl.innerHTML = "";
  for (const lang of data.languages) {
    const option = document.createElement("option");
    option.value = lang;
    option.textContent = lang.toUpperCase();
    languageEl.appendChild(option);
  }
  if ([...languageEl.options].some((o) => o.value === "ru")) {
    languageEl.value = "ru";
  }
}

async function loadVoices() {
  speakerEl.innerHTML = "";
  setStatus("Загружаю список голосов…");
  try {
    const res = await fetch(`/api/voices?language=${encodeURIComponent(languageEl.value)}`);
    if (!res.ok) throw new Error((await res.json()).detail || "Не удалось получить голоса");
    const data = await res.json();
    for (const speaker of data.speakers) {
      const option = document.createElement("option");
      option.value = speaker;
      option.textContent = speaker;
      speakerEl.appendChild(option);
    }
    setStatus("");
  } catch (err) {
    setStatus(`Ошибка: ${err.message}`);
  }
}

rateEl.addEventListener("input", () => {
  rateValueEl.textContent = `${Number(rateEl.value).toFixed(1)}×`;
  playerEl.playbackRate = Number(rateEl.value);
});

languageEl.addEventListener("change", loadVoices);

speakBtn.addEventListener("click", async () => {
  const text = textEl.value.trim();
  if (!text) {
    setStatus("Сначала вставь текст.");
    return;
  }

  speakBtn.disabled = true;
  setStatus("Синтезирую речь… это может занять время на первом запуске (загрузка модели).");
  playerEl.classList.add("hidden");
  downloadEl.classList.add("hidden");

  try {
    const res = await fetch("/api/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        language: languageEl.value,
        speaker: speakerEl.value,
      }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `Ошибка сервера (${res.status})`);
    }

    const blob = await res.blob();
    if (currentObjectUrl) URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = URL.createObjectURL(blob);

    playerEl.src = currentObjectUrl;
    playerEl.playbackRate = Number(rateEl.value);
    playerEl.classList.remove("hidden");
    playerEl.play();

    downloadEl.href = currentObjectUrl;
    downloadEl.classList.remove("hidden");

    setStatus("Готово.");
  } catch (err) {
    setStatus(`Ошибка: ${err.message}`);
  } finally {
    speakBtn.disabled = false;
  }
});

(async function init() {
  await loadLanguages();
  await loadVoices();
})();
