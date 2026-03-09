const STORAGE_KEY = "tem8_practice_progress_v2";
const CLIENT_ID_STORAGE_KEY = "tem8_practice_client_id";
const SEARCH_PARAMS = new URLSearchParams(window.location.search);
const LOCAL_PROGRESS_ONLY = SEARCH_PARAMS.get("progress") === "local";
const TEM8_CONFIG = window.TEM8_CONFIG || {};
const API_BASE_URL = normalizeApiBase(SEARCH_PARAMS.get("api") || TEM8_CONFIG.apiBaseUrl || "");
const CLIENT_ID = resolveClientId(SEARCH_PARAMS.get("client") || TEM8_CONFIG.clientId || "");

const state = {
  dataset: null,
  progress: null,
  bleedMarkers: [],
  selectedYear: null,
  selectedGroupId: null,
  materialsBucket: "library",
  materialFilterYear: "all",
  materialFilterCategory: "all",
  materialFilterQuery: "",
  selectedMaterialSetId: null,
  selectedMaterialGroupId: null,
  materialQuestionId: null,
  view: "practice",
  focusMode: false,
  practiceQuestionId: null,
  practiceAdvanceTimer: null,
  practiceAutoAdvanceQuestionId: null,
  wrongbookQuestionId: null,
  wrongbookDrafts: {},
  mock: null,
};

let adaptiveLayoutBound = false;

function normalizeApiBase(value) {
  const text = String(value || "").trim();
  return text ? text.replace(/\/+$/, "") : "";
}

function generateClientId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `client-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function resolveClientId(explicitValue) {
  const explicit = String(explicitValue || "").trim();
  if (explicit) {
    localStorage.setItem(CLIENT_ID_STORAGE_KEY, explicit);
    return explicit;
  }

  const stored = localStorage.getItem(CLIENT_ID_STORAGE_KEY);
  if (stored) {
    return stored;
  }

  const next = generateClientId();
  localStorage.setItem(CLIENT_ID_STORAGE_KEY, next);
  return next;
}

function buildApiUrl(path) {
  return API_BASE_URL ? `${API_BASE_URL}${path}` : path;
}

function buildStaticUrl(path) {
  const text = String(path || "").trim();
  if (!text) {
    return "";
  }
  if (/^https?:\/\//i.test(text)) {
    return text;
  }
  return text.startsWith("/") ? text : `/${text}`;
}

function buildApiHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  if (API_BASE_URL && CLIENT_ID) {
    headers["X-TEM8-Client-ID"] = CLIENT_ID;
  }
  return headers;
}

function defaultProgress() {
  return {
    version: 2,
    updated_at: null,
    answers: {},
    manual_wrong_book: {},
    mock_sessions: [],
  };
}

function normalizeAnswerRecord(record = {}) {
  return {
    selected: record.selected ?? null,
    response_text: record.response_text ?? "",
    checked_at: record.checked_at ?? null,
    is_correct: typeof record.is_correct === "boolean" ? record.is_correct : null,
    attempt_count: record.attempt_count ?? (record.checked_at ? 1 : 0),
    wrong_count: record.wrong_count ?? (record.is_correct === false ? 1 : 0),
  };
}

function normalizeProgress(progress) {
  const safe = progress || defaultProgress();
  const answers = {};
  for (const [questionId, record] of Object.entries(safe.answers || {})) {
    answers[questionId] = normalizeAnswerRecord(record);
  }
  return {
    version: 2,
    updated_at: safe.updated_at ?? null,
    answers,
    manual_wrong_book: { ...(safe.manual_wrong_book || {}) },
    mock_sessions: Array.isArray(safe.mock_sessions) ? safe.mock_sessions : [],
  };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function buildBleedMarkers(dataset) {
  const markers = new Set([
    "Wortschatz (25 Punkte)",
    "Grammatik (15 Punkte)",
    "Leseverständnis",
    "Leseverstandnis",
  ]);

  for (const yearEntry of dataset?.years || []) {
    for (const group of yearEntry.groups || []) {
      markers.add(group.instruction);
    }
  }

  return Array.from(markers).sort((left, right) => right.length - left.length);
}

function stripBleedText(value) {
  let text = String(value || "");
  for (const marker of state.bleedMarkers) {
    const markerIndex = text.indexOf(marker);
    if (markerIndex > 0) {
      text = text.slice(0, markerIndex);
    }
  }
  text = text.replace(/\bQ[lI]\b/g, "");
  text = text.replace(/[=|]+/g, " ");
  text = text.replace(/\s+([,.;:!?])/g, "$1");
  text = text.replace(/[ ]{2,}/g, " ");
  text = text.replace(/\n{3,}/g, "\n\n");
  return text.trim();
}

function cleanDisplayText(value, inline = false) {
  let text = stripBleedText(value);
  if (inline) {
    text = text.replace(/\s+/g, " ");
  }
  return text.trim().replace(/[~]+$/g, "").trim();
}

function renderBlankSpan(length, inline = false) {
  const blankLength = Math.max(Number(length) || 0, inline ? 2 : 3);
  const classes = ["fill-blank"];
  if (inline) {
    classes.push("inline");
  }
  return `<span class="${classes.join(" ")}" style="--blank-ch:${blankLength}" aria-hidden="true"></span>`;
}

function formatDisplayText(value, inline = false) {
  const placeholders = [];
  let text = cleanDisplayText(value, inline).replace(/_{2,}/g, (match) => {
    const token = `@@BLANK_${placeholders.length}@@`;
    placeholders.push(match.length);
    return token;
  });

  text = escapeHtml(text).replaceAll("\n", "<br />");
  return text.replace(/@@BLANK_(\d+)@@/g, (_, index) => renderBlankSpan(placeholders[Number(index)], inline));
}

function formatText(value) {
  return formatDisplayText(value, false);
}

function formatInline(value) {
  return formatDisplayText(value, true);
}

function getQuestionType(question) {
  if (question?.question_type) {
    return question.question_type;
  }
  return "single-choice";
}

function getBucketEntries(bucketName) {
  return state.dataset?.[bucketName] || [];
}

function getLibraryEntries() {
  return getBucketEntries("library");
}

function getExerciseEntries() {
  return getBucketEntries("exercise_sets");
}

function getYearEntries() {
  return state.dataset?.years || [];
}

function getYearEntry(year) {
  return getYearEntries().find((entry) => entry.year === year);
}

function getQuestionsForYear(year) {
  return getYearEntry(year)?.questions || [];
}

function getGroupsForYear(year) {
  return getYearEntry(year)?.groups || [];
}

function getAllQuestionContainers() {
  return [
    ...getYearEntries().map((entry) => ({ bucket: "years", entry })),
    ...getLibraryEntries().map((entry) => ({ bucket: "library", entry })),
    ...getExerciseEntries().map((entry) => ({ bucket: "exercise_sets", entry })),
  ];
}

function datasetQuestionCount() {
  return getAllQuestionContainers().reduce((sum, { entry }) => sum + (entry.questions?.length || 0), 0);
}

function getQuestionById(questionId) {
  for (const { entry } of getAllQuestionContainers()) {
    const question = entry.questions.find((item) => item.id === questionId);
    if (question) {
      return question;
    }
  }
  return null;
}

function getQuestionContainerById(questionId) {
  for (const container of getAllQuestionContainers()) {
    if (container.entry.questions.some((item) => item.id === questionId)) {
      return container;
    }
  }
  return null;
}

function getResolvedOptions(question) {
  const rawOptions = Object.entries(question?.options || {}).filter(([, value]) => value != null && String(value).trim());
  if (!rawOptions.length) {
    if (getQuestionType(question) === "true-false") {
      return [
        ["R", "Richtig"],
        ["F", "Falsch"],
      ];
    }
    return [];
  }

  const needsRepair = rawOptions.some(([, value]) => /\b[B-HRFT]\s*[.,:：]/.test(String(value)));
  if (!needsRepair) {
    return rawOptions;
  }

  const mergedText = rawOptions
    .map(([key, value]) => {
      const text = String(value || "").trim();
      if (new RegExp(`^${key}\\s*[.:：]`).test(text)) {
        return text;
      }
      return `${key}. ${text}`;
    })
    .join(" ")
    .replace(/\s+/g, " ");

  const repaired = [];
  const pattern = /([A-HRFT])(?:\s*[.,:：]|\s+)(?=\S)/g;
  const matches = Array.from(mergedText.matchAll(pattern));
  if (matches.length < 2) {
    return rawOptions;
  }

  matches.forEach((match, index) => {
    const label = match[1];
    const start = match.index + match[0].length;
    const end = index + 1 < matches.length ? matches[index + 1].index : mergedText.length;
    const text = mergedText.slice(start, end).trim();
    if (text) {
      repaired.push([label, text]);
    }
  });

  return repaired.length ? repaired : rawOptions;
}

function isChoiceQuestion(question) {
  const options = getResolvedOptions(question);
  if (getQuestionType(question) === "true-false") {
    return options.length > 0;
  }
  return options.length >= 2;
}

function isPromptQuestion(question) {
  return getQuestionType(question) === "prompt" && !isChoiceQuestion(question);
}

function isTextInputQuestion(question) {
  return !isChoiceQuestion(question) && !isPromptQuestion(question);
}

function normalizeAnswerText(value) {
  return String(value || "")
    .normalize("NFKC")
    .trim()
    .toLowerCase()
    .replace(/[，。、“”‘’！？；：,.!?;:()[\]{}"'`]/g, " ")
    .replace(/\s+/g, " ");
}

function getSubmittedValue(question, record) {
  return isChoiceQuestion(question) ? record.selected : record.response_text;
}

function getExpectedAnswers(question) {
  const accepted = Array.isArray(question.accepted_answers) ? question.accepted_answers : [];
  if (accepted.length) {
    return accepted;
  }
  if (question.display_answer) {
    return [question.display_answer];
  }
  return [];
}

function evaluateQuestionResponse(question, record) {
  if (isChoiceQuestion(question)) {
    if (!question.correct_option) {
      return null;
    }
    return record.selected === question.correct_option;
  }

  const expected = getExpectedAnswers(question).map(normalizeAnswerText).filter(Boolean);
  if (!expected.length) {
    return null;
  }
  const response = normalizeAnswerText(record.response_text);
  if (!response) {
    return null;
  }
  return expected.includes(response);
}

function getCorrectAnswerMarkup(question) {
  if (isChoiceQuestion(question) && question.correct_option) {
    const optionText = Object.fromEntries(getResolvedOptions(question))[question.correct_option];
    if (optionText) {
      return `${question.correct_option}. ${formatInline(optionText)}`;
    }
    return escapeHtml(question.correct_option);
  }

  if (question.display_answer) {
    return formatInline(question.display_answer);
  }

  const accepted = getExpectedAnswers(question);
  if (accepted.length) {
    return escapeHtml(accepted[0]);
  }

  return "未录入";
}

function isYearMockCompatible(year) {
  return getQuestionsForYear(year).every((question) => isChoiceQuestion(question));
}

function getMaterialEntries(bucketName = state.materialsBucket) {
  return bucketName === "exercise_sets" ? getExerciseEntries() : getLibraryEntries();
}

function getMaterialEntryYear(entry) {
  return entry?.year ?? "misc";
}

function getMaterialEntryCategory(entry, bucketName = state.materialsBucket) {
  if (!entry) {
    return "misc";
  }
  if (bucketName === "library") {
    return entry.section || "misc";
  }
  if (entry.id === "exercise-2023-paper") {
    return "past-paper";
  }
  if (String(entry.id).startsWith("exercise-country-")) {
    return "country-bank";
  }
  return entry.section || "misc";
}

function getMaterialCategoryLabel(category, bucketName = state.materialsBucket) {
  const labels = {
    listening: "听力",
    reading: "阅读",
    landeskunde: "国情",
    translation: "翻译",
    writing: "写作",
    "past-paper": "真题练习",
    "country-bank": "国情1000",
    exercise: "练习",
    misc: "其他",
  };
  return labels[category] || (bucketName === "library" ? "资料" : "练习");
}

function getFilteredMaterialEntries(bucketName = state.materialsBucket) {
  const query = String(state.materialFilterQuery || "").trim().toLowerCase();
  return getMaterialEntries(bucketName).filter((entry) => {
    const matchesYear =
      state.materialFilterYear === "all" ||
      String(getMaterialEntryYear(entry)) === String(state.materialFilterYear);
    const matchesCategory =
      state.materialFilterCategory === "all" ||
      getMaterialEntryCategory(entry, bucketName) === state.materialFilterCategory;
    const haystacks = [entry.title, entry.instruction, entry.source_pdf, entry.section]
      .filter(Boolean)
      .map((item) => String(item).toLowerCase());
    const matchesQuery = !query || haystacks.some((item) => item.includes(query));
    return matchesYear && matchesCategory && matchesQuery;
  });
}

function ensureMaterialSelection() {
  const entries = getFilteredMaterialEntries();
  const available = entries.find((entry) => entry.id === state.selectedMaterialSetId) ? entries : entries;
  if (!available.length) {
    state.selectedMaterialSetId = null;
    state.selectedMaterialGroupId = null;
    state.materialQuestionId = null;
    return;
  }
  if (!available.some((entry) => entry.id === state.selectedMaterialSetId)) {
    state.selectedMaterialSetId = available[0].id;
    state.selectedMaterialGroupId = null;
    state.materialQuestionId = null;
  }
}

function getMaterialFilterMeta(bucketName = state.materialsBucket) {
  const entries = getMaterialEntries(bucketName);
  const years = Array.from(new Set(entries.map((entry) => String(getMaterialEntryYear(entry))))).sort();
  const categories = Array.from(new Set(entries.map((entry) => getMaterialEntryCategory(entry, bucketName)))).sort((left, right) =>
    getMaterialCategoryLabel(left, bucketName).localeCompare(getMaterialCategoryLabel(right, bucketName), "zh-Hans-CN"),
  );
  return { years, categories };
}

function getMaterialEntry(entryId = state.selectedMaterialSetId, bucketName = state.materialsBucket) {
  return getFilteredMaterialEntries(bucketName).find((entry) => entry.id === entryId) || null;
}

function getMaterialGroups(entry = getMaterialEntry()) {
  return entry?.groups || [];
}

function getMaterialQuestions(entry = getMaterialEntry()) {
  return entry?.questions || [];
}

function getMaterialGroup(entry = getMaterialEntry(), groupId = state.selectedMaterialGroupId) {
  return getMaterialGroups(entry).find((group) => group.id === groupId) || null;
}

function getMaterialQuestionListForGroup(entry = getMaterialEntry(), groupId = state.selectedMaterialGroupId) {
  const group = getMaterialGroup(entry, groupId);
  if (!entry || !group) {
    return [];
  }
  return group.question_numbers
    .map((number) => entry.questions.find((item) => item.number === number))
    .filter(Boolean);
}

function getGroupById(year, groupId) {
  return getGroupsForYear(year).find((group) => group.id === groupId) || null;
}

function getQuestionListForGroup(year, groupId) {
  const group = getGroupById(year, groupId);
  if (!group) {
    return [];
  }
  return group.question_numbers
    .map((number) => getQuestionsForYear(year).find((item) => item.number === number))
    .filter(Boolean);
}

function getRecord(questionId) {
  state.progress.answers[questionId] = normalizeAnswerRecord(state.progress.answers[questionId]);
  return state.progress.answers[questionId];
}

function hasAnswerKey() {
  return Boolean(state.dataset?.meta?.answer_key_loaded);
}

function answerCoverageText() {
  const answered = state.dataset?.meta?.answer_count || 0;
  return answered ? `已录入 ${answered} 题答案` : "答案未录入";
}

function mergeProgress(localProgress, remoteProgress) {
  const safeLocal = normalizeProgress(localProgress);
  const safeRemote = normalizeProgress(remoteProgress);
  const localTime = safeLocal.updated_at ? Date.parse(safeLocal.updated_at) : 0;
  const remoteTime = safeRemote.updated_at ? Date.parse(safeRemote.updated_at) : 0;
  return remoteTime >= localTime ? safeRemote : safeLocal;
}

async function apiGet(url) {
  const target = buildApiUrl(url);
  const response = await fetch(target, {
    headers: buildApiHeaders(),
  });
  if (!response.ok) {
    throw new Error(`GET ${target} failed`);
  }
  return response.json();
}

async function apiPost(url, payload) {
  const target = buildApiUrl(url);
  const response = await fetch(target, {
    method: "POST",
    headers: buildApiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`POST ${target} failed`);
  }
  return response.json();
}

async function logEvent(type, payload = {}) {
  if (LOCAL_PROGRESS_ONLY) {
    return;
  }
  try {
    await apiPost("/api/events", {
      type,
      ...payload,
    });
  } catch (error) {
    console.warn("logEvent failed", error);
  }
}

async function persistProgress() {
  state.progress.updated_at = new Date().toISOString();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.progress));
  if (LOCAL_PROGRESS_ONLY) {
    return;
  }
  try {
    await apiPost("/api/progress", state.progress);
  } catch (error) {
    console.warn("persistProgress failed", error);
  }
}

async function resetProgress() {
  const confirmed = window.confirm("将清空当前所有学习进度、错题记录和模考记录。确定继续吗？");
  if (!confirmed) {
    return;
  }

  clearPracticeAdvanceTimer();
  state.progress = defaultProgress();
  state.mock = null;
  state.wrongbookDrafts = {};
  initializePracticeQuestion(true);
  initializeMaterialQuestion(true);
  initializeWrongbookQuestion(true);
  await persistProgress();
  await logEvent("progress_reset", { local_only: LOCAL_PROGRESS_ONLY });
  renderApp();
}

function getQuestionSource(question) {
  const container = getQuestionContainerById(question.id);
  const entry = container?.entry || null;
  const yearPart = question.year || entry?.year || "资料";
  const sectionPart = question.subsection || entry?.title || entry?.section || question.group_label || "题组";
  let pagePart = "";
  if (question.page != null) {
    pagePart = ` · PDF 第 ${question.page} 页`;
  } else if (question.source_page_start != null) {
    const end = question.source_page_end && question.source_page_end !== question.source_page_start ? `-${question.source_page_end}` : "";
    pagePart = ` · PDF 第 ${question.source_page_start}${end} 页`;
  }
  return `${yearPart} · ${sectionPart} · 第 ${question.number} 题${pagePart}`;
}

function wrongBookIds() {
  const automatic = Object.entries(state.progress.answers)
    .filter(([, record]) => record.is_correct === false)
    .map(([questionId]) => questionId);
  const manual = Object.entries(state.progress.manual_wrong_book || {})
    .filter(([, flagged]) => Boolean(flagged))
    .map(([questionId]) => questionId);
  return Array.from(new Set([...automatic, ...manual]));
}

function wrongBookQuestionsForYear(year) {
  return wrongBookIds()
    .map((questionId) => getQuestionById(questionId))
    .filter((question) => question?.year === year)
    .sort((left, right) => left.number - right.number);
}

function statsForYear(year) {
  const questions = getQuestionsForYear(year);
  const checked = questions.filter((question) => getRecord(question.id).checked_at).length;
  const wrong = wrongBookQuestionsForYear(year).length;
  const correct = questions.filter((question) => getRecord(question.id).is_correct === true).length;
  return {
    total: questions.length,
    checked,
    wrong,
    correct,
  };
}

function groupProgress(year, groupId) {
  const questions = getQuestionListForGroup(year, groupId);
  const checked = questions.filter((question) => getRecord(question.id).checked_at).length;
  const wrong = questions.filter((question) => wrongBookIds().includes(question.id)).length;
  return {
    total: questions.length,
    checked,
    wrong,
  };
}

function materialGroupProgress(entry, groupId) {
  const questions = getMaterialQuestionListForGroup(entry, groupId);
  const checked = questions.filter((question) => getRecord(question.id).checked_at).length;
  const correct = questions.filter((question) => getRecord(question.id).is_correct === true).length;
  return {
    total: questions.length,
    checked,
    correct,
  };
}

function canSubmitRecord(question, record) {
  if (isChoiceQuestion(question)) {
    return Boolean(record.selected);
  }
  return Boolean(String(record.response_text || "").trim());
}

function clearPracticeAdvanceTimer() {
  if (state.practiceAdvanceTimer) {
    clearTimeout(state.practiceAdvanceTimer);
    state.practiceAdvanceTimer = null;
  }
  state.practiceAutoAdvanceQuestionId = null;
}

function schedulePracticeAdvance(questionId) {
  clearPracticeAdvanceTimer();
  state.practiceAutoAdvanceQuestionId = questionId;
  state.practiceAdvanceTimer = window.setTimeout(() => {
    const record = getRecord(questionId);
    if (state.view !== "practice" || state.practiceQuestionId !== questionId || !record.checked_at) {
      return;
    }
    goToNextPracticeQuestion();
  }, 1800);
}

function getCurrentPracticeGroup() {
  if (state.practiceQuestionId) {
    const question = getQuestionById(state.practiceQuestionId);
    if (question) {
      return getGroupById(question.year, question.group_id);
    }
  }
  return getGroupById(state.selectedYear, state.selectedGroupId);
}

function initializePracticeQuestion(force = false) {
  const groupId = state.selectedGroupId || getGroupsForYear(state.selectedYear)[0]?.id;
  if (!groupId) {
    state.practiceQuestionId = null;
    return;
  }
  const questions = getQuestionListForGroup(state.selectedYear, groupId);
  if (!questions.length) {
    state.practiceQuestionId = null;
    return;
  }
  if (!force && questions.some((question) => question.id === state.practiceQuestionId)) {
    return;
  }
  state.practiceQuestionId =
    questions.find((question) => !getRecord(question.id).checked_at)?.id ||
    questions[0].id;
}

function initializeMaterialQuestion(force = false) {
  ensureMaterialSelection();
  const entry = getMaterialEntry();
  if (!entry) {
    state.selectedMaterialGroupId = null;
    state.materialQuestionId = null;
    return;
  }

  const groupId = state.selectedMaterialGroupId || getMaterialGroups(entry)[0]?.id;
  if (!groupId) {
    state.selectedMaterialGroupId = null;
    state.materialQuestionId = null;
    return;
  }

  state.selectedMaterialGroupId = groupId;
  const questions = getMaterialQuestionListForGroup(entry, groupId);
  if (!questions.length) {
    state.materialQuestionId = null;
    return;
  }

  if (!force && questions.some((question) => question.id === state.materialQuestionId)) {
    return;
  }

  state.materialQuestionId =
    questions.find((question) => !getRecord(question.id).checked_at)?.id ||
    questions[0].id;
}

function initializeWrongbookQuestion(force = false) {
  const questions = wrongBookQuestionsForYear(state.selectedYear);
  if (!questions.length) {
    state.wrongbookQuestionId = null;
    return;
  }
  if (!force && questions.some((question) => question.id === state.wrongbookQuestionId)) {
    return;
  }
  state.wrongbookQuestionId = questions[0].id;
}

function getWrongbookDraft(questionId) {
  state.wrongbookDrafts[questionId] ||= {
    selected: null,
    response_text: "",
    checked: false,
    is_correct: null,
  };
  return state.wrongbookDrafts[questionId];
}

function buildSubmittedAnswerText(question, record) {
  const submittedValue = getSubmittedValue(question, record);
  if (!submittedValue) {
    return "未作答";
  }
  if (isChoiceQuestion(question)) {
    const optionText = Object.fromEntries(getResolvedOptions(question))[submittedValue];
    return optionText ? `${submittedValue}. ${optionText}` : submittedValue;
  }
  return submittedValue;
}

function buildFeedback(question, record, checked, isCorrect, autoNext = false) {
  if (!checked) {
    return "";
  }

  const hasSpecificAnswer = Boolean(question.correct_option || getExpectedAnswers(question).length);
  if (!hasAnswerKey() || !hasSpecificAnswer) {
    return `
      <div class="feedback pending">
        题目已提交，当前题库还没有答案键。系统已记录你的作答：${escapeHtml(buildSubmittedAnswerText(question, record))}。
      </div>
    `;
  }

  const explanation = question.explanation ? `<br /><br />${formatText(question.explanation)}` : "";
  const suffix = autoNext ? `<br /><br /><span class="auto-next-note">答案已显示，系统会自动跳到下一题，你也可以立即点击“下一题”。</span>` : "";
  if (isCorrect) {
    return `
      <div class="feedback correct">
        回答正确。正确答案：${getCorrectAnswerMarkup(question)}${explanation}${suffix}
      </div>
    `;
  }

  return `
    <div class="feedback wrong">
      回答错误。正确答案：${getCorrectAnswerMarkup(question)}${explanation}${suffix}
    </div>
  `;
}

function renderOptionButton({ question, optionKey, optionText, selected, checked, isCorrect, revealCorrectness, onClick, disabled }) {
  const classes = ["option-button"];
  if (selected === optionKey) {
    classes.push("selected");
  }
  if (revealCorrectness && question.correct_option) {
    if (question.correct_option === optionKey) {
      classes.push("correct-answer");
    } else if (selected === optionKey && isCorrect === false) {
      classes.push("wrong-answer");
    }
  }

  return `
    <button
      class="${classes.join(" ")}"
      ${disabled ? "disabled" : ""}
      onclick="${disabled ? "" : onClick}"
    >
      <strong>${optionKey}.</strong> ${formatInline(optionText)}
    </button>
  `;
}

function renderTextEntryControl({ question, value, disabled, onInput, multiline = false }) {
  const placeholder = multiline ? "请输入你的作答" : "请输入答案";
  const rows = question.subprompts?.length ? Math.max(6, question.subprompts.length * 2 + 4) : 8;
  if (multiline) {
    return `
      <label class="text-response-shell">
        <span class="chip">Long Response</span>
        <textarea
          class="text-response-input multiline"
          rows="${rows}"
          placeholder="${placeholder}"
          ${disabled ? "disabled" : ""}
          oninput="${disabled ? "" : onInput}"
        >${escapeHtml(value || "")}</textarea>
      </label>
    `;
  }

  return `
    <label class="text-response-shell">
      <span class="chip">Text Answer</span>
      <input
        class="text-response-input"
        type="text"
        placeholder="${placeholder}"
        value="${escapeHtml(value || "")}"
        ${disabled ? "disabled" : ""}
        oninput="${disabled ? "" : onInput}"
      />
    </label>
  `;
}

function renderQuestionSubprompts(question) {
  if (!Array.isArray(question.subprompts) || !question.subprompts.length) {
    return "";
  }
  return `
    <div class="subprompt-list">
      ${question.subprompts.map((item) => `<div class="subprompt-item">${formatText(item)}</div>`).join("")}
    </div>
  `;
}

function renderQuestionAnswerArea({ question, record, checked, isCorrect, revealCorrectness, disabled, onSelect, onInput }) {
  if (isChoiceQuestion(question)) {
    return `
      <div class="option-grid">
        ${getResolvedOptions(question)
          .map(([optionKey, optionText]) =>
            renderOptionButton({
              question,
              optionKey,
              optionText,
              selected: record.selected,
              checked,
              isCorrect,
              revealCorrectness,
              disabled,
              onClick: `${onSelect}('${question.id}', '${optionKey}')`,
            }),
          )
          .join("")}
      </div>
    `;
  }

  return `
    ${question.prompt_text ? `<div class="prompt-block">${formatText(question.prompt_text)}</div>` : ""}
    ${renderQuestionSubprompts(question)}
    ${renderTextEntryControl({
      question,
      value: record.response_text,
      disabled,
      multiline: isPromptQuestion(question),
      onInput: `${onInput}('${question.id}', this.value)`,
    })}
  `;
}

function renderQuestionPalette(questions, currentQuestionId, clickHandlerName, statusGetter) {
  return `
    <div class="question-palette">
      ${questions
        .map((question) => {
          const status = statusGetter(question);
          const classes = ["palette-button", question.id === currentQuestionId ? "active" : "", status]
            .filter(Boolean)
            .join(" ");
          return `
            <button class="${classes}" onclick="${clickHandlerName}('${question.id}')">
              ${question.number}
            </button>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderYearNav() {
  const container = document.getElementById("year-nav");
  container.innerHTML = getYearEntries()
    .map((entry) => {
      const stats = statsForYear(entry.year);
      const active = entry.year === state.selectedYear ? "active" : "";
      return `
        <button class="year-pill ${active}" onclick="appActions.selectYear(${entry.year})">
          ${entry.year}
          <span class="muted">${stats.checked}/${stats.total}</span>
        </button>
      `;
    })
    .join("");
}

function renderStatusCard() {
  const totalQuestions = datasetQuestionCount();
  const checked = Object.values(state.progress.answers).filter((record) => record.checked_at).length;
  const wrong = wrongBookIds().length;
  const latestMock = state.progress.mock_sessions?.[0];
  const container = document.getElementById("status-card");
  container.innerHTML = `
    <div class="stats-grid">
      <div class="stat-tile">
        <span class="chip">题量</span>
        <strong>${totalQuestions}</strong>
      </div>
      <div class="stat-tile">
        <span class="chip">已练</span>
        <strong>${checked}</strong>
      </div>
      <div class="stat-tile">
        <span class="chip">错题</span>
        <strong>${wrong}</strong>
      </div>
      <div class="stat-tile">
        <span class="chip">资料</span>
        <strong>${getLibraryEntries().length + getExerciseEntries().length}</strong>
      </div>
    </div>
    <p class="status-note">${answerCoverageText()}</p>
    <p class="status-note">${latestMock ? `最近一次模考：${latestMock.year} · ${latestMock.display_score}` : "还没有模考记录。"}</p>
  `;
  document.getElementById("answer-status").className = hasAnswerKey() ? "badge" : "badge badge-warning";
  document.getElementById("answer-status").textContent = hasAnswerKey() ? answerCoverageText() : "答案未录入";
}

function renderModeTabs() {
  const modes = [
    { id: "practice", label: "题目练习" },
    { id: "materials", label: "资料题型" },
    { id: "mock", label: "模考" },
    { id: "wrongbook", label: "错题本" },
  ];
  document.getElementById("mode-tabs").innerHTML = modes
    .map(
      (mode) => `
        <button
          class="mode-tab ${mode.id === state.view ? "active" : ""}"
          ${mode.id === "mock" && !isYearMockCompatible(state.selectedYear) ? "disabled" : ""}
          onclick="${mode.id === "mock" && !isYearMockCompatible(state.selectedYear) ? "" : `appActions.switchView('${mode.id}')`}"
        >
          ${mode.label}
        </button>
      `,
    )
    .join("");
}

function renderUtilityActions() {
  document.getElementById("utility-actions").innerHTML = `
    <button class="ghost-button danger-button" onclick="appActions.resetProgress()">
      清空进度
    </button>
    <button class="focus-button ${state.focusMode ? "active" : ""}" onclick="appActions.toggleFocusMode()">
      ${state.focusMode ? "退出全屏" : "全屏做题"}
    </button>
  `;
}

function renderShellLayout() {
  const shell = document.getElementById("page-shell");
  shell.className = `page-shell${state.focusMode ? " focus-mode" : ""}`;
}

function renderHero() {
  const yearStats = statsForYear(state.selectedYear);
  const titleNode = document.getElementById("hero-title");
  const subtitleNode = document.getElementById("hero-subtitle");

  if (state.view === "materials") {
    const entry = getMaterialEntry();
    titleNode.textContent = entry ? entry.title : "资料题型";
    subtitleNode.textContent = entry
      ? `${state.materialsBucket === "library" ? "真题资料" : "练习题库"} · ${entry.question_count} 题${entry.audio_file ? " · 含音频" : ""}`
      : "浏览听力、阅读、写作、翻译、国情与 exercise 资料。";
    return;
  }

  if (state.view === "practice") {
    const currentGroup = getCurrentPracticeGroup();
    titleNode.textContent = `${state.selectedYear} 年单题练习`;
    subtitleNode.textContent = currentGroup
      ? `${currentGroup.subsection} ${currentGroup.label} · 已练 ${yearStats.checked}/${yearStats.total} · 提交后显示答案，再进入下一题。`
      : "加载题组中。";
    return;
  }

  if (state.view === "mock") {
    titleNode.textContent = `${state.selectedYear} 年模考`;
    subtitleNode.textContent = !isYearMockCompatible(state.selectedYear)
      ? "当前年份含文本题，模考暂只支持纯选择题年份。"
      : state.mock
      ? `已作答 ${Object.values(state.mock.answers).filter(Boolean).length}/${getQuestionsForYear(state.mock.year).length}。答案会在整套提交后统一显示。`
      : "整套 40 题，提交后统一判分并显示解析。";
    return;
  }

  titleNode.textContent = `${state.selectedYear} 年错题本`;
  subtitleNode.textContent = "错题本会隐藏你上次的错选，按空白题重新作答，并标出来源和累计错题次数。";
}

function getQuestionCardClasses(checked, isCorrect) {
  const classes = ["question-stage-card"];
  if (checked && isCorrect === true) {
    classes.push("correct");
  }
  if (checked && isCorrect === false) {
    classes.push("wrong");
  }
  return classes.join(" ");
}

function getNextQuestionInGroup(year, groupId, questionId) {
  const questions = getQuestionListForGroup(year, groupId);
  const index = questions.findIndex((question) => question.id === questionId);
  return index >= 0 ? questions[index + 1] || null : null;
}

function getNextGroup(year, groupId) {
  const groups = getGroupsForYear(year);
  const index = groups.findIndex((group) => group.id === groupId);
  return index >= 0 ? groups[index + 1] || null : null;
}

function renderPracticeSummary(group) {
  const progress = groupProgress(state.selectedYear, group.id);
  const nextGroup = getNextGroup(state.selectedYear, group.id);
  const totalCorrect = getQuestionListForGroup(state.selectedYear, group.id).filter((question) => getRecord(question.id).is_correct === true).length;
  return `
    <section class="summary-card screen-workspace">
      <div class="summary-topbar">
        <div>
          <div class="question-type">Practice Complete</div>
          <h3>${group.subsection} ${group.label} 已完成</h3>
        </div>
        <span class="badge">${progress.checked}/${progress.total}</span>
      </div>
      <p class="summary-copy">本题组已全部做完。答对 ${totalCorrect} 题，错题 ${progress.wrong} 题。你可以通过题号回看解析，也可以直接进入下一组。</p>
      ${renderQuestionPalette(
        getQuestionListForGroup(state.selectedYear, group.id),
        state.practiceQuestionId,
        "appActions.jumpPracticeQuestion",
        (question) => {
          const record = getRecord(question.id);
          if (record.is_correct === false) return "wrong";
          return record.checked_at ? "done" : "pending";
        },
      )}
      <div class="summary-actions">
        ${nextGroup ? `<button class="action-button" onclick="appActions.enterNextGroup()">进入下一组</button>` : ""}
        <button class="ghost-button" onclick="appActions.restartCurrentGroup()">重做本组</button>
        <button class="ghost-button" onclick="appActions.switchView('wrongbook')">查看错题本</button>
      </div>
    </section>
  `;
}

function renderPassagePane(group) {
  if (!group?.shared_context) {
    return "";
  }
  const title = [group.subsection, group.label].filter(Boolean).join(" ") || group.instruction || "共享材料";
  return `
    <article class="pane-card">
      <div class="pane-card-head">
        <div>
          <div class="question-type">共享材料</div>
          <strong>${title}</strong>
        </div>
        <span class="source-badge">左右分栏</span>
      </div>
      <div class="pane-scroll">
        <div class="passage-copy">${formatText(group.shared_context)}</div>
      </div>
    </article>
  `;
}

function renderPracticeQuestionCard(question, group) {
  const record = getRecord(question.id);
  const questions = getQuestionListForGroup(question.year, group.id);
  const index = questions.findIndex((item) => item.id === question.id);
  const nextQuestion = questions[index + 1] || null;
  const submitted = Boolean(record.checked_at);
  const autoNext = state.practiceAutoAdvanceQuestionId === question.id;
  const classes = getQuestionCardClasses(submitted, record.is_correct);
  const sourceText = getQuestionSource(question);
  const progress = groupProgress(question.year, group.id);
  const submitDisabled = !submitted && !canSubmitRecord(question, record);

  return `
    <article class="${classes}">
      <div class="question-stage-head">
        <div>
          <div class="question-type">题目练习</div>
          <h3 class="question-number">第 ${question.number} 题</h3>
          <div class="meta-line">题组 ${group.label} · 组内 ${index + 1}/${questions.length} · 已完成 ${progress.checked}/${progress.total}</div>
        </div>
        <span class="source-badge">${sourceText}</span>
      </div>
      <p class="question-stem">${formatText(question.stem)}</p>
      ${renderQuestionAnswerArea({
        question,
        record,
        checked: submitted,
        isCorrect: record.is_correct,
        revealCorrectness: submitted,
        disabled: submitted,
        onSelect: "appActions.selectPracticeOption",
        onInput: "appActions.updatePracticeResponse",
      })}
      ${buildFeedback(question, record, submitted, record.is_correct, autoNext)}
      <div class="question-stage-foot">
        <div class="summary-actions">
          <button
            class="action-button"
            ${submitDisabled ? "disabled" : ""}
            onclick="${submitDisabled ? "" : submitted ? "appActions.goToNextPracticeQuestion()" : `appActions.submitPracticeQuestion('${question.id}')`}"
          >
            ${submitted ? (nextQuestion ? "下一题" : "完成本组") : "确定提交"}
          </button>
          <button class="ghost-button" onclick="appActions.toggleWrongBook('${question.id}')">
            ${state.progress.manual_wrong_book?.[question.id] ? "移出错题本" : "加入错题本"}
          </button>
        </div>
        <div class="meta-line">${submitted ? "已锁定本题答案，可从题号导航回看。" : "先选答案，再点击“确定提交”。"}</div>
      </div>
    </article>
  `;
}

function renderPracticeView() {
  const groups = getGroupsForYear(state.selectedYear);
  const currentGroup = getCurrentPracticeGroup() || groups[0];
  if (!currentGroup) {
    return `<section class="empty-card"><h3>没有可显示的题组</h3></section>`;
  }

  const groupQuestions = getQuestionListForGroup(state.selectedYear, currentGroup.id);
  const currentQuestion = getQuestionById(state.practiceQuestionId);
  const progress = groupProgress(state.selectedYear, currentGroup.id);

  const toolbar = `
    <section class="panel screen-toolbar">
      <div class="workspace-head">
        <div>
          <div class="question-type">练习导航</div>
          <h3 class="workspace-title">${currentGroup.subsection} ${currentGroup.label}</h3>
          <p class="muted">${currentGroup.instruction}</p>
        </div>
        <span class="badge badge-muted">${progress.checked}/${progress.total}</span>
      </div>
      <div class="group-tabs">
        ${groups
          .map(
            (group) => `
              <button class="group-pill ${group.id === currentGroup.id ? "active" : ""}" onclick="appActions.selectGroup('${group.id}')">
                ${group.subsection} ${group.label}
              </button>
            `,
          )
          .join("")}
      </div>
      ${renderQuestionPalette(
        groupQuestions,
        state.practiceQuestionId,
        "appActions.jumpPracticeQuestion",
        (question) => {
          const record = getRecord(question.id);
          if (record.is_correct === false) return "wrong";
          return record.checked_at ? "done" : "pending";
        },
      )}
    </section>
  `;

  if (!currentQuestion) {
    return `
      <div class="screen-layout">
        ${toolbar}
        ${renderPracticeSummary(currentGroup)}
      </div>
    `;
  }

  const layoutClass = currentGroup.shared_context ? "split-layout" : "solo-layout";
  return `
    <div class="screen-layout">
      ${toolbar}
      <section class="workspace-card screen-workspace ${layoutClass}">
        ${currentGroup.shared_context ? renderPassagePane(currentGroup) : ""}
        ${renderPracticeQuestionCard(currentQuestion, currentGroup)}
      </section>
    </div>
  `;
}

function buildMockResult(mock) {
  const questions = getQuestionsForYear(mock.year);
  const keyedQuestions = questions.filter((question) => question.correct_option);
  if (!keyedQuestions.length) {
    return {
      display_score: "待答案录入",
      result_note: "当前题库还没有答案，模考只保存了你的作答记录。",
    };
  }
  const correctCount = keyedQuestions.filter((question) => mock.answers[question.id] === question.correct_option).length;
  return {
    display_score: `${correctCount} / ${questions.length}`,
    result_note: `已按 ${keyedQuestions.length} 道已录入答案的题目判分。答案与解析现在可以逐题查看。`,
  };
}

function currentMockQuestions() {
  if (!state.mock) {
    return [];
  }
  return getQuestionsForYear(state.mock.year);
}

function renderMockQuestionCard(question, group) {
  const selected = state.mock.answers[question.id] || null;
  const checked = Boolean(state.mock.finished_at);
  const isCorrect = checked && question.correct_option ? selected === question.correct_option : null;
  const classes = getQuestionCardClasses(checked, isCorrect);

  return `
    <article class="${classes}">
      <div class="question-stage-head">
        <div>
          <div class="question-type">模考</div>
          <h3 class="question-number">第 ${question.number} 题</h3>
          <div class="meta-line">${getQuestionSource(question)}</div>
        </div>
        <span class="badge badge-muted">${checked ? "已交卷" : "作答中"}</span>
      </div>
      <p class="question-stem">${formatText(question.stem)}</p>
      <div class="option-grid">
        ${getResolvedOptions(question)
          .filter(([optionKey]) => optionKey)
          .map(([optionKey, optionText]) =>
            renderOptionButton({
              question,
              optionKey,
              optionText,
              selected,
              checked,
              isCorrect,
              revealCorrectness: checked,
              disabled: checked,
              onClick: `appActions.selectMockOption('${question.id}', '${optionKey}')`,
            }),
          )
          .join("")}
      </div>
      ${checked ? buildFeedback(question, { selected, response_text: "" }, true, isCorrect, false) : ""}
    </article>
  `;
}

function renderMockView() {
  if (!isYearMockCompatible(state.selectedYear)) {
    return `
      <div class="screen-layout">
        <section class="summary-card screen-workspace">
          <div class="summary-topbar">
            <div>
              <div class="question-type">Mock Locked</div>
              <h3>${state.selectedYear} 年暂不支持模考</h3>
            </div>
          </div>
          <p class="summary-copy">当前年份的词汇语法中包含文本作答题。模考模式暂只支持纯选择题年份，资料题型请在“资料题型”里完成。</p>
          <div class="summary-actions">
            <button class="action-button" onclick="appActions.switchView('practice')">返回题目练习</button>
          </div>
        </section>
      </div>
    `;
  }

  const sessions = state.progress.mock_sessions || [];
  if (!state.mock) {
    return `
      <div class="screen-layout">
        <section class="summary-card screen-workspace">
          <div class="summary-topbar">
            <div>
              <div class="question-type">Full Simulation</div>
              <h3>${state.selectedYear} 年模考</h3>
            </div>
            <span class="badge">${getQuestionsForYear(state.selectedYear).length} 题</span>
          </div>
          <p class="summary-copy">整套 40 题会保留原始题序。你做完整套并提交后，系统才会统一显示答案、解析和总分。</p>
          <div class="result-strip">
            <div class="result-line"><strong>最近记录</strong><span>${sessions[0] ? sessions[0].display_score : "暂无"}</span></div>
            <div class="meta-line">${sessions[0] ? `${sessions[0].year} · ${sessions[0].completed_at}` : "提交模考后会在这里显示成绩。"}</div>
          </div>
          <div class="summary-actions">
            <button class="action-button" onclick="appActions.startMock()">开始模考</button>
          </div>
        </section>
      </div>
    `;
  }

  const questions = currentMockQuestions();
  const currentQuestion = questions.find((item) => item.id === state.mock.current_question_id) || questions[0];
  const currentGroup = getGroupById(state.mock.year, currentQuestion.group_id);
  const answeredCount = Object.values(state.mock.answers).filter(Boolean).length;
  const layoutClass = currentGroup.shared_context ? "split-layout" : "solo-layout";

  return `
    <div class="screen-layout">
      <section class="panel screen-toolbar">
      <div class="mock-topbar">
        <div>
          <div class="question-type">Mock ${state.mock.year}</div>
          <h3 class="workspace-title">${currentGroup.subsection} ${currentGroup.label}</h3>
          <p class="muted">${currentGroup.instruction}</p>
        </div>
        <div class="summary-actions">
          <span class="badge badge-muted">${answeredCount}/${questions.length}</span>
          <button class="ghost-button" onclick="appActions.resetMock()">重新开始</button>
          <button class="action-button" onclick="appActions.submitMock()">提交模考</button>
        </div>
      </div>
      ${renderQuestionPalette(
        questions,
        state.mock.current_question_id,
        "appActions.jumpMockQuestion",
        (question) => (state.mock.answers[question.id] ? "done" : "pending"),
      )}
      ${
        state.mock.finished_at
          ? `
            <div class="result-strip">
              <div class="result-line"><strong>模考结果</strong><span>${state.mock.display_score}</span></div>
              <div class="meta-line">${state.mock.result_note}</div>
            </div>
          `
          : ""
      }
      </section>
      <section class="workspace-card screen-workspace ${layoutClass} mock-layout">
        ${currentGroup.shared_context ? renderPassagePane(currentGroup) : ""}
        ${renderMockQuestionCard(currentQuestion, currentGroup)}
      </section>
    </div>
  `;
}

function renderWrongbookQuestionCard(question) {
  const baseRecord = getRecord(question.id);
  const draft = getWrongbookDraft(question.id);
  const checked = draft.checked;
  const classes = getQuestionCardClasses(checked, draft.is_correct);
  const removable = draft.is_correct === true || baseRecord.is_correct === true;
  const submitDisabled = !checked && !canSubmitRecord(question, draft);

  return `
    <article class="${classes}">
      <div class="question-stage-head">
        <div>
          <div class="question-type">错题重做</div>
          <h3 class="question-number">第 ${question.number} 题</h3>
          <div class="meta-line">${getQuestionSource(question)}</div>
        </div>
        <div class="wrongbook-meta">
          <span class="source-badge">错题次数 ${baseRecord.wrong_count || 1}</span>
          <span class="source-badge">来源 ${question.year}</span>
        </div>
      </div>
      <p class="question-stem">${formatText(question.stem)}</p>
      ${renderQuestionAnswerArea({
        question,
        record: draft,
        checked,
        isCorrect: draft.is_correct,
        revealCorrectness: checked,
        disabled: checked,
        onSelect: "appActions.selectWrongbookOption",
        onInput: "appActions.updateWrongbookResponse",
      })}
      ${buildFeedback(question, draft, checked, draft.is_correct, false)}
      <div class="question-stage-foot">
        <div class="summary-actions">
          <button
            class="action-button"
            ${submitDisabled ? "disabled" : ""}
            onclick="${submitDisabled ? "" : checked ? "appActions.goToNextWrongbookQuestion()" : `appActions.submitWrongbookQuestion('${question.id}')`}"
          >
            ${checked ? "下一题" : "确定提交"}
          </button>
          <button class="ghost-button" ${removable ? `onclick="appActions.removeFromWrongbook('${question.id}')"` : "disabled"}>
            ${removable ? "移出错题本" : "答对后可移出"}
          </button>
        </div>
        <div class="meta-line">${checked ? "历史错选已隐藏，本次按空白题重新作答。" : "错题本不会显示你之前错选的是什么。"}</div>
      </div>
    </article>
  `;
}

function renderWrongbookView() {
  const wrongQuestions = wrongBookQuestionsForYear(state.selectedYear);
  if (!wrongQuestions.length) {
    return `
      <section class="empty-card">
        <div class="question-type">Wrong Book</div>
        <h3>${state.selectedYear} 年暂无错题</h3>
        <p class="muted">做错的题会自动进入这里。进入后会按空白题重新作答，不直接显示上次错选。</p>
      </section>
    `;
  }

  const currentQuestion = wrongQuestions.find((question) => question.id === state.wrongbookQuestionId) || wrongQuestions[0];
  const currentGroup = getGroupById(currentQuestion.year, currentQuestion.group_id);
  const layoutClass = currentGroup.shared_context ? "split-layout" : "solo-layout";

  return `
    <div class="screen-layout">
      <section class="panel screen-toolbar">
      <div class="workspace-head">
        <div>
          <div class="question-type">Wrong Book</div>
          <h3 class="workspace-title">${state.selectedYear} 年错题重做</h3>
          <p class="muted">错题本只显示题目来源和累计错题次数，不展示你上次错选了什么。</p>
        </div>
        <span class="badge badge-muted">${wrongQuestions.length} 题</span>
      </div>
      ${renderQuestionPalette(
        wrongQuestions,
        currentQuestion.id,
        "appActions.jumpWrongbookQuestion",
        (question) => {
          const draft = getWrongbookDraft(question.id);
          if (draft.checked && draft.is_correct === false) return "wrong";
          return draft.checked ? "done" : "pending";
        },
      )}
      </section>
      <section class="workspace-card screen-workspace ${layoutClass} wrongbook-layout">
        ${currentGroup.shared_context ? renderPassagePane(currentGroup) : ""}
        ${renderWrongbookQuestionCard(currentQuestion)}
      </section>
    </div>
  `;
}

function renderMaterialAudio(entry) {
  if (!entry?.audio_file) {
    return "";
  }
  return `
    <div class="audio-player-card">
      <div>
        <div class="question-type">Listening Audio</div>
        <strong>${entry.title}</strong>
      </div>
      <audio controls preload="none" src="${buildStaticUrl(entry.audio_file)}"></audio>
    </div>
  `;
}

function renderMaterialQuestionCard(entry, question, group) {
  const record = getRecord(question.id);
  const questions = getMaterialQuestionListForGroup(entry, group.id);
  const index = questions.findIndex((item) => item.id === question.id);
  const nextQuestion = questions[index + 1] || null;
  const submitted = Boolean(record.checked_at);
  const submitDisabled = !submitted && !canSubmitRecord(question, record);
  const progress = materialGroupProgress(entry, group.id);
  const classes = getQuestionCardClasses(submitted, record.is_correct);

  return `
    <article class="${classes}">
      <div class="question-stage-head">
        <div>
          <div class="question-type">${state.materialsBucket === "library" ? "资料题型" : "Exercise"}</div>
          <h3 class="question-number">第 ${question.number} 题</h3>
          <div class="meta-line">${group.label || group.instruction || entry.title} · 组内 ${index + 1}/${questions.length} · 已完成 ${progress.checked}/${progress.total}</div>
        </div>
        <span class="source-badge">${getQuestionSource(question)}</span>
      </div>
      <p class="question-stem">${formatText(question.stem)}</p>
      ${renderQuestionAnswerArea({
        question,
        record,
        checked: submitted,
        isCorrect: record.is_correct,
        revealCorrectness: submitted,
        disabled: submitted,
        onSelect: "appActions.selectMaterialOption",
        onInput: "appActions.updateMaterialResponse",
      })}
      ${buildFeedback(question, record, submitted, record.is_correct, false)}
      <div class="question-stage-foot">
        <div class="summary-actions">
          <button
            class="action-button"
            ${submitDisabled ? "disabled" : ""}
            onclick="${submitDisabled ? "" : submitted ? "appActions.goToNextMaterialQuestion()" : `appActions.submitMaterialQuestion('${question.id}')`}"
          >
            ${submitted ? (nextQuestion ? "下一题" : "完成本组") : "确定提交"}
          </button>
        </div>
        <div class="meta-line">${submitted ? "已保存本题作答与结果。" : "支持选择题、判断题、填空题和开放题。先作答，再提交。"}</div>
      </div>
    </article>
  `;
}

function renderMaterialsView() {
  const entries = getFilteredMaterialEntries();
  const totalEntries = getMaterialEntries().length;
  const filterMeta = getMaterialFilterMeta();
  ensureMaterialSelection();
  const entry = getMaterialEntry();
  if (!entries.length || !entry) {
    return `
      <section class="empty-card">
        <div class="question-type">Materials</div>
        <h3>暂无资料</h3>
        <p class="muted">当前筛选条件下没有可显示的题集。可以切换 bucket、年份或类别。</p>
      </section>
    `;
  }

  const groups = getMaterialGroups(entry);
  const currentGroup = getMaterialGroup(entry) || groups[0];
  const groupQuestions = getMaterialQuestionListForGroup(entry, currentGroup?.id);
  const currentQuestion = entry.questions.find((item) => item.id === state.materialQuestionId) || groupQuestions[0] || null;
  const progress = currentGroup ? materialGroupProgress(entry, currentGroup.id) : { checked: 0, total: 0, correct: 0 };
  const layoutClass = currentGroup?.shared_context ? "split-layout" : "solo-layout";

  const toolbar = `
    <section class="panel screen-toolbar">
      <div class="workspace-head">
        <div>
          <div class="question-type">资料导航</div>
          <h3 class="workspace-title">${entry.title}</h3>
          <p class="muted">${entry.instruction || `${state.materialsBucket === "library" ? "真题资料" : "练习题库"} · ${entry.question_count} 题`}</p>
        </div>
        <span class="badge badge-muted">${progress.checked}/${progress.total}</span>
      </div>
      <div class="group-tabs bucket-tabs">
        <button class="group-pill ${state.materialsBucket === "library" ? "active" : ""}" onclick="appActions.selectMaterialsBucket('library')">真题资料</button>
        <button class="group-pill ${state.materialsBucket === "exercise_sets" ? "active" : ""}" onclick="appActions.selectMaterialsBucket('exercise_sets')">练习库</button>
      </div>
      <div class="filter-toolbar">
        <label class="filter-search">
          <span class="question-type">搜索题集</span>
          <input
            class="filter-search-input"
            type="search"
            value="${escapeHtml(state.materialFilterQuery)}"
            placeholder="按标题 / PDF 名称筛选"
            oninput="appActions.updateMaterialFilterQuery(this.value, this.selectionStart || 0)"
          />
        </label>
        <div class="material-results-summary muted">当前显示 ${entries.length} / ${totalEntries} 套题集</div>
      </div>
      <div class="group-tabs filter-tabs">
        <button class="group-pill ${state.materialFilterYear === "all" ? "active" : ""}" onclick="appActions.selectMaterialYearFilter('all')">全部年份</button>
        ${filterMeta.years
          .map(
            (year) => `
              <button class="group-pill ${String(state.materialFilterYear) === String(year) ? "active" : ""}" onclick="appActions.selectMaterialYearFilter('${year}')">
                ${year === "misc" ? "未标年" : year}
              </button>
            `,
          )
          .join("")}
      </div>
      <div class="group-tabs filter-tabs">
        <button class="group-pill ${state.materialFilterCategory === "all" ? "active" : ""}" onclick="appActions.selectMaterialCategoryFilter('all')">全部类别</button>
        ${filterMeta.categories
          .map(
            (category) => `
              <button class="group-pill ${state.materialFilterCategory === category ? "active" : ""}" onclick="appActions.selectMaterialCategoryFilter('${category}')">
                ${getMaterialCategoryLabel(category)}
              </button>
            `,
          )
          .join("")}
      </div>
      <div class="group-tabs material-set-tabs">
        ${entries
          .map(
            (item) => `
              <button class="group-pill ${item.id === entry.id ? "active" : ""}" onclick="appActions.selectMaterialSet('${item.id}')">
                ${item.title}
              </button>
            `,
          )
          .join("")}
      </div>
      <div class="material-meta-strip">
        <span class="source-badge">${entry.year || "未标年"}</span>
        <span class="source-badge">${getMaterialCategoryLabel(getMaterialEntryCategory(entry))}</span>
        <span class="source-badge">${entry.question_count} 题</span>
        ${entry.source_pdf ? `<span class="source-badge">${escapeHtml(entry.source_pdf.split("/").slice(-1)[0])}</span>` : ""}
      </div>
      ${renderMaterialAudio(entry)}
      ${
        groups.length
          ? `
            <div class="group-tabs">
              ${groups
                .map(
                  (group) => `
                    <button class="group-pill ${group.id === currentGroup?.id ? "active" : ""}" onclick="appActions.selectMaterialGroup('${group.id}')">
                      ${group.label || group.instruction || "题组"}
                    </button>
                  `,
                )
                .join("")}
            </div>
          `
          : ""
      }
      ${renderQuestionPalette(
        groupQuestions,
        currentQuestion?.id,
        "appActions.jumpMaterialQuestion",
        (question) => {
          const record = getRecord(question.id);
          if (record.is_correct === false) return "wrong";
          if (record.is_correct === true) return "done";
          return record.checked_at ? "done" : "pending";
        },
      )}
    </section>
  `;

  if (!currentQuestion || !currentGroup) {
    return `
      <div class="screen-layout">
        ${toolbar}
        <section class="empty-card">
          <div class="question-type">Empty Group</div>
          <h3>当前题组暂无可显示题目</h3>
        </section>
      </div>
    `;
  }

  return `
    <div class="screen-layout">
      ${toolbar}
      <section class="workspace-card screen-workspace ${layoutClass}">
        ${currentGroup.shared_context ? renderPassagePane(currentGroup) : ""}
        ${renderMaterialQuestionCard(entry, currentQuestion, currentGroup)}
      </section>
    </div>
  `;
}

function renderContent() {
  const content = document.getElementById("app-content");
  if (!state.dataset) {
    content.innerHTML = `<section class="empty-card"><h3>正在加载题库…</h3></section>`;
    return;
  }

  if (state.view === "practice") {
    content.innerHTML = renderPracticeView();
    return;
  }
  if (state.view === "materials") {
    content.innerHTML = renderMaterialsView();
    return;
  }
  if (state.view === "mock") {
    content.innerHTML = renderMockView();
    return;
  }
  content.innerHTML = renderWrongbookView();
}

function renderApp() {
  renderShellLayout();
  renderYearNav();
  renderStatusCard();
  renderModeTabs();
  renderUtilityActions();
  renderHero();
  renderContent();
  queueAdaptiveLayoutSync();
}

function setCssVar(name, value) {
  document.documentElement.style.setProperty(name, value);
}

function syncAdaptiveLayout() {
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 900;
  const content = document.getElementById("app-content");

  const contentTop = content ? content.getBoundingClientRect().top : 0;
  const contentMax = Math.max(220, Math.floor(viewportHeight - contentTop - 12));
  setCssVar("--content-max-height", `${contentMax}px`);
}

function queueAdaptiveLayoutSync() {
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(syncAdaptiveLayout);
  });
}

function canScrollOnAxis(element, axis, delta) {
  if (!element) {
    return false;
  }

  if (axis === "x") {
    if (element.scrollWidth <= element.clientWidth + 1) {
      return false;
    }
    if (delta < 0) {
      return element.scrollLeft > 0;
    }
    if (delta > 0) {
      return element.scrollLeft + element.clientWidth < element.scrollWidth - 1;
    }
    return false;
  }

  if (element.scrollHeight <= element.clientHeight + 1) {
    return false;
  }
  if (delta < 0) {
    return element.scrollTop > 0;
  }
  if (delta > 0) {
    return element.scrollTop + element.clientHeight < element.scrollHeight - 1;
  }
  return false;
}

function resolveWheelFallbackTarget(event) {
  const hovered = document.elementFromPoint(event.clientX, event.clientY) || event.target;
  if (!(hovered instanceof Element)) {
    return null;
  }

  const horizontal = hovered.closest(".group-tabs, .question-palette");
  const prefersHorizontal = event.shiftKey || Math.abs(event.deltaX) > Math.abs(event.deltaY);
  const horizontalDelta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
  if (prefersHorizontal && horizontal && canScrollOnAxis(horizontal, "x", horizontalDelta)) {
    return { element: horizontal, axis: "x", delta: horizontalDelta };
  }

  let current = hovered;
  while (current && current !== document.body) {
    if (canScrollOnAxis(current, "y", event.deltaY)) {
      return { element: current, axis: "y", delta: event.deltaY };
    }
    current = current.parentElement;
  }

  const content = document.getElementById("app-content");
  if (content && canScrollOnAxis(content, "y", event.deltaY)) {
    return { element: content, axis: "y", delta: event.deltaY };
  }

  const mainPanel = document.querySelector(".main-panel");
  if (mainPanel && canScrollOnAxis(mainPanel, "y", event.deltaY)) {
    return { element: mainPanel, axis: "y", delta: event.deltaY };
  }

  const sidebar = document.querySelector(".sidebar");
  if (sidebar && canScrollOnAxis(sidebar, "y", event.deltaY)) {
    return { element: sidebar, axis: "y", delta: event.deltaY };
  }

  return null;
}

function handleWheelFallback(event) {
  if (event.ctrlKey) {
    return;
  }

  const interactive = event.target instanceof Element ? event.target.closest("input, textarea, select, option") : null;
  if (interactive) {
    return;
  }

  const target = resolveWheelFallbackTarget(event);
  if (!target || !target.delta) {
    return;
  }

  event.preventDefault();
  if (target.axis === "x") {
    target.element.scrollLeft += target.delta;
    return;
  }
  target.element.scrollTop += target.delta;
}

function setupWheelFallback() {
  return;
}

function setupAdaptiveLayout() {
  if (adaptiveLayoutBound) {
    return;
  }
  window.addEventListener("resize", queueAdaptiveLayoutSync);
  document.addEventListener("fullscreenchange", queueAdaptiveLayoutSync);
  adaptiveLayoutBound = true;
}

async function selectPracticeOption(questionId, optionKey) {
  clearPracticeAdvanceTimer();
  const record = getRecord(questionId);
  record.selected = optionKey;
  record.response_text = "";
  await logEvent("practice_option_selected", { question_id: questionId, option: optionKey });
  await persistProgress();
  renderApp();
}

async function updatePracticeResponse(questionId, value) {
  clearPracticeAdvanceTimer();
  const record = getRecord(questionId);
  record.response_text = value;
  record.selected = null;
  await persistProgress();
  renderApp();
}

async function submitPracticeQuestion(questionId) {
  clearPracticeAdvanceTimer();
  const question = getQuestionById(questionId);
  const record = getRecord(questionId);
  if (!canSubmitRecord(question, record)) {
    return;
  }

  record.checked_at = new Date().toISOString();
  record.attempt_count += 1;
  record.is_correct = evaluateQuestionResponse(question, record);
  if (record.is_correct === false) {
    record.wrong_count += 1;
    state.progress.manual_wrong_book[questionId] = true;
  }

  await logEvent("practice_submitted", {
    question_id: questionId,
    selected: record.selected,
    response_text: record.response_text,
    is_correct: record.is_correct,
  });
  await persistProgress();
  renderApp();
  schedulePracticeAdvance(questionId);
}

function jumpPracticeQuestion(questionId) {
  clearPracticeAdvanceTimer();
  state.practiceQuestionId = questionId;
  const question = getQuestionById(questionId);
  if (question) {
    state.selectedGroupId = question.group_id;
  }
  renderApp();
}

function goToNextPracticeQuestion() {
  clearPracticeAdvanceTimer();
  const question = getQuestionById(state.practiceQuestionId);
  if (!question) {
    return;
  }
  const nextQuestion = getNextQuestionInGroup(question.year, question.group_id, question.id);
  state.practiceQuestionId = nextQuestion ? nextQuestion.id : null;
  renderApp();
}

function enterNextGroup() {
  const currentGroup = getCurrentPracticeGroup();
  if (!currentGroup) {
    return;
  }
  const nextGroup = getNextGroup(state.selectedYear, currentGroup.id);
  if (!nextGroup) {
    return;
  }
  clearPracticeAdvanceTimer();
  state.selectedGroupId = nextGroup.id;
  initializePracticeQuestion(true);
  renderApp();
}

async function restartCurrentGroup() {
  const currentGroup = getCurrentPracticeGroup();
  if (!currentGroup) {
    return;
  }
  clearPracticeAdvanceTimer();
  for (const question of getQuestionListForGroup(state.selectedYear, currentGroup.id)) {
    const record = getRecord(question.id);
    record.selected = null;
    record.response_text = "";
    record.checked_at = null;
    record.is_correct = null;
  }
  state.practiceQuestionId = getQuestionListForGroup(state.selectedYear, currentGroup.id)[0]?.id || null;
  await logEvent("practice_group_restarted", { year: state.selectedYear, group_id: currentGroup.id });
  await persistProgress();
  renderApp();
}

async function toggleWrongBook(questionId) {
  state.progress.manual_wrong_book[questionId] = !state.progress.manual_wrong_book[questionId];
  await logEvent("wrongbook_toggled", { question_id: questionId, enabled: state.progress.manual_wrong_book[questionId] });
  await persistProgress();
  initializeWrongbookQuestion();
  renderApp();
}

async function selectWrongbookOption(questionId, optionKey) {
  const draft = getWrongbookDraft(questionId);
  draft.selected = optionKey;
  draft.response_text = "";
  draft.checked = false;
  draft.is_correct = null;
  renderApp();
}

async function updateWrongbookResponse(questionId, value) {
  const draft = getWrongbookDraft(questionId);
  draft.response_text = value;
  draft.selected = null;
  draft.checked = false;
  draft.is_correct = null;
  renderApp();
}

async function submitWrongbookQuestion(questionId) {
  const question = getQuestionById(questionId);
  const draft = getWrongbookDraft(questionId);
  if (!canSubmitRecord(question, draft)) {
    return;
  }

  draft.checked = true;
  draft.is_correct = evaluateQuestionResponse(question, draft);

  const record = getRecord(questionId);
  record.selected = draft.selected;
  record.response_text = draft.response_text || "";
  record.checked_at = new Date().toISOString();
  record.attempt_count += 1;
  record.is_correct = draft.is_correct;
  if (draft.is_correct === false) {
    record.wrong_count += 1;
    state.progress.manual_wrong_book[questionId] = true;
  }

  await logEvent("wrongbook_submitted", {
    question_id: questionId,
    selected: draft.selected,
    response_text: draft.response_text,
    is_correct: draft.is_correct,
  });
  await persistProgress();
  renderApp();
}

function jumpWrongbookQuestion(questionId) {
  state.wrongbookQuestionId = questionId;
  renderApp();
}

function goToNextWrongbookQuestion() {
  const questions = wrongBookQuestionsForYear(state.selectedYear);
  if (!questions.length) {
    state.wrongbookQuestionId = null;
    renderApp();
    return;
  }
  const index = questions.findIndex((question) => question.id === state.wrongbookQuestionId);
  const nextQuestion = index >= 0 ? questions[index + 1] || null : questions[0];
  state.wrongbookQuestionId = nextQuestion ? nextQuestion.id : null;
  renderApp();
}

async function removeFromWrongbook(questionId) {
  const record = getRecord(questionId);
  const draft = getWrongbookDraft(questionId);
  if (record.is_correct !== true && draft.is_correct !== true) {
    return;
  }
  state.progress.manual_wrong_book[questionId] = false;
  await logEvent("wrongbook_removed", { question_id: questionId });
  await persistProgress();
  initializeWrongbookQuestion(true);
  renderApp();
}

function selectMaterialsBucket(bucketName) {
  state.materialsBucket = bucketName;
  state.materialFilterYear = "all";
  state.materialFilterCategory = "all";
  state.materialFilterQuery = "";
  state.selectedMaterialSetId = getFilteredMaterialEntries(bucketName)[0]?.id || null;
  state.selectedMaterialGroupId = null;
  state.materialQuestionId = null;
  initializeMaterialQuestion(true);
  renderApp();
}

function selectMaterialYearFilter(value) {
  state.materialFilterYear = value;
  state.selectedMaterialSetId = null;
  state.selectedMaterialGroupId = null;
  state.materialQuestionId = null;
  initializeMaterialQuestion(true);
  renderApp();
}

function selectMaterialCategoryFilter(value) {
  state.materialFilterCategory = value;
  state.selectedMaterialSetId = null;
  state.selectedMaterialGroupId = null;
  state.materialQuestionId = null;
  initializeMaterialQuestion(true);
  renderApp();
}

function updateMaterialFilterQuery(value, caretPosition = 0) {
  state.materialFilterQuery = String(value || "");
  state.selectedMaterialSetId = null;
  state.selectedMaterialGroupId = null;
  state.materialQuestionId = null;
  initializeMaterialQuestion(true);
  renderApp();
  window.requestAnimationFrame(() => {
    const input = document.querySelector(".filter-search-input");
    if (!(input instanceof HTMLInputElement)) {
      return;
    }
    input.focus();
    const offset = Math.max(0, Math.min(caretPosition, input.value.length));
    input.setSelectionRange(offset, offset);
  });
}

function selectMaterialSet(setId) {
  state.selectedMaterialSetId = setId;
  state.selectedMaterialGroupId = null;
  state.materialQuestionId = null;
  initializeMaterialQuestion(true);
  renderApp();
}

function selectMaterialGroup(groupId) {
  state.selectedMaterialGroupId = groupId;
  state.materialQuestionId = null;
  initializeMaterialQuestion(true);
  renderApp();
}

async function selectMaterialOption(questionId, optionKey) {
  const record = getRecord(questionId);
  record.selected = optionKey;
  record.response_text = "";
  await persistProgress();
  renderApp();
}

async function updateMaterialResponse(questionId, value) {
  const record = getRecord(questionId);
  record.response_text = value;
  record.selected = null;
  await persistProgress();
  renderApp();
}

async function submitMaterialQuestion(questionId) {
  const question = getQuestionById(questionId);
  const record = getRecord(questionId);
  if (!question || !canSubmitRecord(question, record)) {
    return;
  }

  record.checked_at = new Date().toISOString();
  record.attempt_count += 1;
  record.is_correct = evaluateQuestionResponse(question, record);

  await logEvent("material_submitted", {
    question_id: questionId,
    bucket: state.materialsBucket,
    selected: record.selected,
    response_text: record.response_text,
    is_correct: record.is_correct,
  });
  await persistProgress();
  renderApp();
}

function jumpMaterialQuestion(questionId) {
  state.materialQuestionId = questionId;
  renderApp();
}

function goToNextMaterialQuestion() {
  const entry = getMaterialEntry();
  const group = getMaterialGroup(entry);
  if (!entry || !group) {
    return;
  }
  const questions = getMaterialQuestionListForGroup(entry, group.id);
  const index = questions.findIndex((question) => question.id === state.materialQuestionId);
  state.materialQuestionId = index >= 0 ? questions[index + 1]?.id || null : questions[0]?.id || null;
  renderApp();
}

async function selectMockOption(questionId, optionKey) {
  if (!state.mock || state.mock.finished_at) {
    return;
  }
  state.mock.answers[questionId] = optionKey;
  await logEvent("mock_option_selected", { question_id: questionId, option: optionKey, year: state.mock.year });
  renderApp();
}

async function submitMock() {
  if (!state.mock || state.mock.finished_at) {
    return;
  }

  state.mock.finished_at = new Date().toISOString();
  const result = buildMockResult(state.mock);
  state.mock.display_score = result.display_score;
  state.mock.result_note = result.result_note;

  for (const question of getQuestionsForYear(state.mock.year)) {
    const selected = state.mock.answers[question.id] || null;
    const record = getRecord(question.id);
    record.selected = selected;
    record.checked_at = state.mock.finished_at;
    record.attempt_count += 1;
    record.is_correct = question.correct_option ? selected === question.correct_option : null;
    if (record.is_correct === false) {
      record.wrong_count += 1;
      state.progress.manual_wrong_book[question.id] = true;
    }
  }

  state.progress.mock_sessions.unshift({
    id: `mock-${Date.now()}`,
    year: state.mock.year,
    completed_at: state.mock.finished_at,
    display_score: state.mock.display_score,
  });

  await logEvent("mock_submitted", {
    year: state.mock.year,
    display_score: state.mock.display_score,
    finished_at: state.mock.finished_at,
  });
  await persistProgress();
  renderApp();
}

function startMock() {
  if (!isYearMockCompatible(state.selectedYear)) {
    renderApp();
    return;
  }
  const questions = getQuestionsForYear(state.selectedYear);
  state.view = "mock";
  state.mock = {
    year: state.selectedYear,
    started_at: new Date().toISOString(),
    finished_at: null,
    current_question_id: questions[0]?.id || null,
    answers: {},
    display_score: "",
    result_note: "",
  };
  logEvent("mock_started", { year: state.selectedYear });
  renderApp();
}

function resetMock() {
  state.mock = null;
  renderApp();
}

function jumpMockQuestion(questionId) {
  if (!state.mock) {
    return;
  }
  state.mock.current_question_id = questionId;
  renderApp();
}

function selectYear(year) {
  clearPracticeAdvanceTimer();
  state.selectedYear = year;
  state.selectedGroupId = getGroupsForYear(year)[0]?.id || null;
  if (state.view === "mock" && !isYearMockCompatible(year)) {
    state.view = "practice";
  }
  state.mock = null;
  state.wrongbookDrafts = {};
  initializePracticeQuestion(true);
  initializeWrongbookQuestion(true);
  renderApp();
}

function selectGroup(groupId) {
  clearPracticeAdvanceTimer();
  state.selectedGroupId = groupId;
  initializePracticeQuestion(true);
  renderApp();
}

function switchView(view) {
  clearPracticeAdvanceTimer();
  state.view = view;
  if (view === "practice") {
    initializePracticeQuestion();
  }
  if (view === "materials") {
    if (!state.selectedMaterialSetId) {
      state.selectedMaterialSetId = getFilteredMaterialEntries()[0]?.id || null;
    }
    initializeMaterialQuestion();
  }
  if (view === "wrongbook") {
    initializeWrongbookQuestion();
  }
  renderApp();
}

async function toggleFocusMode() {
  state.focusMode = !state.focusMode;
  if (state.focusMode && document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen().catch(() => {});
  } else if (!state.focusMode && document.fullscreenElement && document.exitFullscreen) {
    document.exitFullscreen().catch(() => {});
  }
  await logEvent("focus_mode_toggled", { enabled: state.focusMode });
  renderApp();
}

async function bootstrap() {
  try {
    const [dataset, remoteProgress] = await Promise.all([
      apiGet("/api/exams"),
      LOCAL_PROGRESS_ONLY ? Promise.resolve(defaultProgress()) : apiGet("/api/progress"),
    ]);
    const localProgress = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    state.dataset = dataset;
    state.bleedMarkers = buildBleedMarkers(dataset);
    state.progress = mergeProgress(localProgress, remoteProgress);
    state.selectedYear = dataset.meta.available_years[0];
    state.selectedGroupId = getGroupsForYear(state.selectedYear)[0]?.id || null;
    state.selectedMaterialSetId = getFilteredMaterialEntries("library")[0]?.id || null;
    state.selectedMaterialGroupId = getMaterialGroups(getMaterialEntry(state.selectedMaterialSetId, "library"))[0]?.id || null;
    initializePracticeQuestion(true);
    initializeMaterialQuestion(true);
    initializeWrongbookQuestion(true);
    setupWheelFallback();
    setupAdaptiveLayout();
    renderApp();
    await logEvent("app_loaded", { available_years: dataset.meta.available_years });
  } catch (error) {
    console.error(error);
    document.getElementById("app-content").innerHTML = `
      <section class="empty-card">
        <div class="question-type">Load Error</div>
        <h3>题库加载失败</h3>
        <p class="muted">请先运行 <code>python run.py --extract-only</code> 生成 questions.json，然后再刷新页面。</p>
      </section>
    `;
  }
}

window.appActions = {
  selectYear,
  selectGroup,
  switchView,
  resetProgress,
  toggleFocusMode,
  selectPracticeOption,
  submitPracticeQuestion,
  jumpPracticeQuestion,
  goToNextPracticeQuestion,
  enterNextGroup,
  restartCurrentGroup,
  toggleWrongBook,
  selectWrongbookOption,
  submitWrongbookQuestion,
  jumpWrongbookQuestion,
  goToNextWrongbookQuestion,
  removeFromWrongbook,
  selectMaterialsBucket,
  selectMaterialYearFilter,
  selectMaterialCategoryFilter,
  updateMaterialFilterQuery,
  selectMaterialSet,
  selectMaterialGroup,
  selectMaterialOption,
  updateMaterialResponse,
  submitMaterialQuestion,
  jumpMaterialQuestion,
  goToNextMaterialQuestion,
  startMock,
  resetMock,
  selectMockOption,
  submitMock,
  jumpMockQuestion,
  updatePracticeResponse,
  updateWrongbookResponse,
};

window.addEventListener("beforeunload", clearPracticeAdvanceTimer);

bootstrap();
