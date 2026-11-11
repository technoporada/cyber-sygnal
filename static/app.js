"use strict";

const elements = {
  refresh: document.querySelector("#refresh"),
  query: document.querySelector("#query"),
  category: document.querySelector("#category"),
  status: document.querySelector("#status"),
  count: document.querySelector("#count"),
  errors: document.querySelector("#errors"),
  items: document.querySelector("#items"),
};

let allItems = [];
let updatedAt = null;

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text) element.textContent = text;
  return element;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function renderErrors(errors) {
  elements.errors.replaceChildren();
  for (const error of errors) {
    elements.errors.append(
      makeElement("p", "error", `${error.source}: ${error.message}`),
    );
  }
}

function speak(item) {
  if (!("speechSynthesis" in window)) {
    elements.status.textContent = "Ta przeglądarka nie obsługuje czytania na głos.";
    return;
  }
  window.speechSynthesis.cancel();
  const text = [item.title, item.summary].filter(Boolean).join(". ");
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "pl-PL";
  const polishVoice = window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang.toLowerCase().startsWith("pl"));
  if (polishVoice) utterance.voice = polishVoice;
  window.speechSynthesis.speak(utterance);
}

function renderItems() {
  const query = elements.query.value.trim().toLocaleLowerCase("pl");
  const category = elements.category.value;
  const filtered = allItems.filter((item) => {
    const text = `${item.title} ${item.summary} ${item.source}`
      .toLocaleLowerCase("pl");
    return (!query || text.includes(query))
      && (!category || item.category === category);
  });

  elements.count.textContent = `${filtered.length} z ${allItems.length} wpisów`;
  elements.items.replaceChildren();
  if (!filtered.length) {
    elements.items.append(
      makeElement("p", "empty", allItems.length
        ? "Nic nie pasuje do tych filtrów."
        : "Nie ma jeszcze wpisów. Kliknij „Odśwież RSS”."),
    );
    return;
  }

  for (const item of filtered) {
    const card = makeElement("article", "card");
    const meta = makeElement("div", "card-meta");
    meta.append(
      makeElement("span", "source", item.source),
      makeElement("span", "category", item.category),
      makeElement("time", "date", formatDate(item.published)),
    );

    const title = makeElement("h2");
    const link = makeElement("a", "", item.title);
    link.href = item.link;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    title.append(link);
    card.append(meta, title);

    if (item.summary) card.append(makeElement("p", "summary", item.summary));

    const actions = makeElement("div", "card-actions");
    const readButton = makeElement("button", "button button-quiet", "Czytaj");
    readButton.type = "button";
    readButton.addEventListener("click", () => speak(item));
    actions.append(readButton);
    card.append(actions);
    elements.items.append(card);
  }
}

function showSnapshot(snapshot) {
  allItems = snapshot.items || [];
  updatedAt = snapshot.updated_at;
  renderErrors(snapshot.errors || []);
  renderItems();
  elements.status.textContent = updatedAt
    ? `Ostatnie odświeżenie: ${formatDate(updatedAt)}`
    : "Jeszcze nie pobrano kanałów RSS.";
}

async function loadItems() {
  const response = await fetch("/api/items");
  if (!response.ok) throw new Error("Nie udało się pobrać wpisów.");
  showSnapshot(await response.json());
}

async function refresh() {
  elements.refresh.disabled = true;
  elements.status.textContent = "Pobieram kanały RSS…";
  elements.errors.replaceChildren();
  try {
    const response = await fetch("/api/refresh", { method: "POST" });
    if (!response.ok) throw new Error("Nie udało się odświeżyć kanałów.");
    showSnapshot(await response.json());
  } catch (error) {
    elements.status.textContent = error.message || "Nie udało się odświeżyć.";
  } finally {
    elements.refresh.disabled = false;
  }
}

elements.refresh.addEventListener("click", refresh);
elements.query.addEventListener("input", renderItems);
elements.category.addEventListener("change", renderItems);
loadItems().catch((error) => {
  elements.status.textContent = error.message || "Nie udało się załadować strony.";
});
