const form = document.querySelector("#analysis");
const text = document.querySelector("#tweet");
const submit = document.querySelector("#submit");
const count = document.querySelector("#count");
const result = document.querySelector("#result");
const label = document.querySelector("#label");
const detail = document.querySelector("#detail");
let activeRequest;

function show(title, message, sentiment = "") {
  label.textContent = title;
  detail.textContent = message;
  result.dataset.label = sentiment;
}

function updateInput() {
  if (activeRequest) {
    activeRequest.abort();
    activeRequest = undefined;
  }
  count.textContent = `${text.value.length} / ${text.maxLength}`;
  submit.disabled = !text.value.trim();
  show("Waiting for text", "Check a tweet to see its label here.");
}

text.addEventListener("input", updateInput);
document.querySelector("#clear").addEventListener("click", () => {
  text.value = "";
  updateInput();
  text.focus();
});
document.querySelectorAll(".examples button").forEach((button) => {
  button.addEventListener("click", () => {
    text.value = button.textContent.trim();
    updateInput();
    text.focus();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (activeRequest || !text.value.trim()) return;
  const request = new AbortController();
  activeRequest = request;
  submit.disabled = true;
  show("Checking text", "Waiting for the model.");
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: text.value}),
      signal: request.signal,
    });
    if (activeRequest !== request) return;
    if (!response.ok) {
      const messages = {
        413: "Shorten the text and try again.",
        422: "Enter a shorter English tweet with some words or punctuation.",
        429: "Wait a moment and try again.",
      };
      show("Couldn't check text", messages[response.status] ?? "The service is unavailable. Try again shortly.");
      return;
    }
    const prediction = await response.json();
    if (activeRequest !== request) return;
    const names = {negative: "Negative", neutral: "Neutral", positive: "Positive"};
    show(names[prediction.label], `Model ${prediction.model_version}`, prediction.label);
  } catch (error) {
    if (activeRequest === request) show("Couldn't check text", "Check your connection and try again.");
  } finally {
    if (activeRequest === request) {
      activeRequest = undefined;
      submit.disabled = false;
    }
  }
});

updateInput();
