(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const STORAGE_KEY = "apexDreamBuilderV01";

  const state = {
    mode: "text",
    original: "",
    answers: {
      audience: "",
      outcome: "",
      constraint: "",
      evidence: ""
    },
    questionIndex: 0,
    card: null,
    imageName: ""
  };

  const questions = [
    {
      key: "audience",
      text: "Who should benefit most from this dream?",
      placeholder: "Example: independent professionals who feel overwhelmed by important decisions."
    },
    {
      key: "outcome",
      text: "What meaningful result should they experience?",
      placeholder: "Example: make confident decisions faster and understand why each option fits."
    },
    {
      key: "constraint",
      text: "What is the biggest real-world constraint we must respect?",
      placeholder: "Example: I can spend no more than four hours per week and need a mobile-first approach."
    },
    {
      key: "evidence",
      text: "What observable evidence would prove this dream is helping?",
      placeholder: "Example: users complete a decision and report greater confidence without needing live support."
    }
  ];

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        mode: state.mode,
        original: state.original,
        answers: state.answers,
        card: state.card,
        imageName: state.imageName
      }));
    } catch (_) {}
  }

  function restore() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (!saved) return;
      Object.assign(state, saved);
      if (saved.original) {
        $("dreamInput").value = saved.original;
        $("brainDumpInput").value = saved.original;
        $("characterCount").textContent = saved.original.length + " / 1200";
      }
      if (saved.card) renderCard(saved.card);
    } catch (_) {}
  }

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll(".mode-tab").forEach((button) => {
      const active = button.dataset.mode === mode;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll(".mode-pane").forEach((pane) => {
      const active = pane.id === "mode-" + mode;
      pane.classList.toggle("active", active);
      pane.hidden = !active;
    });
    $("captureStatus").textContent = "";
    persist();
  }

  function getCurrentDream() {
    if (state.mode === "brain") return $("brainDumpInput").value;
    if (state.mode === "image") return $("imageDescription").value;
    return $("dreamInput").value;
  }

  function startClarification() {
    const validation = DreamCore.validateDream(getCurrentDream());
    if (!validation.ok) {
      $("captureStatus").textContent = validation.message;
      return;
    }

    state.original = validation.value;
    state.questionIndex = 0;
    $("captureStatus").textContent = "";
    $("capturePanel").hidden = true;
    $("dreamCardPanel").hidden = true;
    $("questionPanel").hidden = false;
    renderQuestion();
    window.scrollTo({ top: 0, behavior: "smooth" });
    persist();
  }

  function renderQuestion() {
    const question = questions[state.questionIndex];
    $("questionCounter").textContent = "Question " + (state.questionIndex + 1) + " of " + questions.length;
    $("questionProgressBar").style.width = (((state.questionIndex + 1) / questions.length) * 100) + "%";
    $("questionText").textContent = question.text;
    $("questionAnswer").placeholder = question.placeholder;
    $("questionAnswer").value = state.answers[question.key] || "";
    $("questionAnswer").focus();
    $("nextQuestionButton").innerHTML =
      state.questionIndex === questions.length - 1
        ? 'Create My Dream Card <span aria-hidden="true">→</span>'
        : 'Continue <span aria-hidden="true">→</span>';
  }

  function advanceQuestion(skip) {
    const question = questions[state.questionIndex];
    state.answers[question.key] = skip ? "" : $("questionAnswer").value.trim();

    if (state.questionIndex < questions.length - 1) {
      state.questionIndex += 1;
      renderQuestion();
      persist();
      return;
    }

    state.card = DreamCore.buildDreamCard({
      original: state.original,
      audience: state.answers.audience,
      outcome: state.answers.outcome,
      constraint: state.answers.constraint,
      evidence: state.answers.evidence
    });
    persist();
    renderCard(state.card);
  }

  function renderCard(card) {
    state.card = card;
    $("clearDreamStatement").textContent = card.statement;
    $("audienceOutput").textContent = card.audience;
    $("outcomeOutput").textContent = card.outcome;
    $("constraintOutput").textContent = card.constraint;
    $("evidenceOutput").textContent = card.evidence;
    $("nextStepOutput").textContent = card.nextStep;
    $("clarityScore").textContent = Number(card.score).toFixed(1);
    $("evidenceLabel").textContent = card.evidenceLabel;

    $("capturePanel").hidden = true;
    $("questionPanel").hidden = true;
    $("dreamCardPanel").hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function editDream() {
    $("dreamCardPanel").hidden = true;
    $("questionPanel").hidden = true;
    $("capturePanel").hidden = false;
    $("dreamInput").value = state.original;
    $("brainDumpInput").value = state.original;
    $("characterCount").textContent = state.original.length + " / 1200";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function showToast(message) {
    const toast = $("toast");
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => toast.classList.remove("show"), 2400);
  }

  async function shareCard() {
    if (!state.card) return;
    const text = DreamCore.exportText(state.card);

    try {
      if (navigator.share) {
        await navigator.share({ title: "My APEX Dream Card", text: text });
        return;
      }
      await navigator.clipboard.writeText(text);
      showToast("Dream Card copied to clipboard.");
    } catch (error) {
      if (error && error.name === "AbortError") return;
      try {
        await navigator.clipboard.writeText(text);
        showToast("Dream Card copied to clipboard.");
      } catch (_) {
        showToast("Sharing is unavailable in this browser.");
      }
    }
  }

  function resetApp() {
    if (!confirm("Reset this Dream Card and start again?")) return;
    localStorage.removeItem(STORAGE_KEY);
    location.reload();
  }

  function setupVoice() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      $("voiceStatus").textContent =
        "Voice transcription is not available in this browser. Use iPhone Dictation in the Text tab instead.";
      $("voiceButton").disabled = true;
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => {
      $("voiceStatus").textContent = "Listening… speak your dream.";
      $("voiceButton").textContent = "■";
    };

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        transcript += event.results[i][0].transcript;
      }
      $("dreamInput").value = transcript.trim();
      $("characterCount").textContent = $("dreamInput").value.length + " / 1200";
    };

    recognition.onerror = () => {
      $("voiceStatus").textContent = "Voice capture did not complete. Use iPhone Dictation in the Text tab.";
    };

    recognition.onend = () => {
      $("voiceButton").textContent = "●";
      if ($("dreamInput").value.trim()) {
        $("voiceStatus").textContent = "Captured. Review it in the Text tab.";
        setMode("text");
      }
    };

    $("voiceButton").addEventListener("click", () => recognition.start());
  }

  document.querySelectorAll(".mode-tab").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });

  $("dreamInput").addEventListener("input", (event) => {
    $("characterCount").textContent = event.target.value.length + " / 1200";
    state.original = event.target.value;
    persist();
  });

  $("imageInput").addEventListener("change", (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    state.imageName = file.name;
    $("imageName").textContent = file.name;
    $("imagePreview").src = URL.createObjectURL(file);
    $("imagePreviewWrap").hidden = false;
    persist();
  });

  $("clarifyButton").addEventListener("click", startClarification);
  $("nextQuestionButton").addEventListener("click", () => advanceQuestion(false));
  $("skipQuestionButton").addEventListener("click", () => advanceQuestion(true));
  $("editButton").addEventListener("click", editDream);
  $("shareButton").addEventListener("click", shareCard);
  $("resetButton").addEventListener("click", resetApp);

  setupVoice();
  restore();

  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("service-worker.js").catch(() => {});
    });
  }
})();
