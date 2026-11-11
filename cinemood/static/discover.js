const form = document.querySelector('#discover');
const requestInput = document.querySelector('#request');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const button = form.querySelector('button');
const interpretation = document.querySelector('#interpretation');
const suggestions = document.querySelector('#suggestions');
const preview = document.querySelector('#catalog-preview');
const resultHeading = document.querySelector('#results-heading');
const resultCount = document.querySelector('#result-count');
const recommendationCards = createCollectionCardGroup(results, 'recommendations', requestInput);
const previewStatus = document.querySelector('#preview-status');
const spotlightCards = createCollectionCardGroup(document.querySelector('#preview-track'), 'spotlight', requestInput);

function paragraph(text) {
  const element = document.createElement('p');
  element.textContent = text;
  return element;
}

function restrictionSummary(parsed) {
  const restrictions = [];
  if (parsed.included_genres.length) restrictions.push(`All required genres: ${parsed.included_genres.join(', ')}`);
  if (parsed.excluded_genres.length) restrictions.push(`Excluded genres: ${parsed.excluded_genres.join(', ')}`);
  if (parsed.runtime_minutes !== null) restrictions.push(`${parsed.runtime_operator === 'lt' ? 'Under' : 'At most'} ${parsed.runtime_minutes} ${parsed.runtime_minutes === 1 ? 'minute' : 'minutes'}`);
  if (parsed.year_min !== null) restrictions.push(`Released from ${parsed.year_min} (inclusive)`);
  if (parsed.year_max !== null) restrictions.push(`Released through ${parsed.year_max} (inclusive)`);
  if (parsed.original_languages.length) restrictions.push(`Original ${parsed.original_languages.length === 1 ? 'language' : 'languages (any)'}: ${parsed.original_languages.join(' or ')}`);
  if (parsed.excluded_original_languages?.length) restrictions.push(`Excluded original languages: ${parsed.excluded_original_languages.join(', ')}`);
  return restrictions.length ? restrictions.join(' · ') : 'No supported hard restrictions.';
}

function showInterpretation(data) {
  interpretation.replaceChildren();
  interpretation.hidden = false;
  const parsed = data.interpretation;
  if (!parsed) return;
  const context = document.createElement('details');
  context.className = 'request-context';
  const summary = document.createElement('summary');
  summary.textContent = 'Request details';
  context.append(summary, paragraph(`Original request: ${data.original_request}`), paragraph(`Current restrictions: ${restrictionSummary(parsed)}`), paragraph(`Mood / themes: ${parsed.semantic_query}`));
  if (data.applied_change) context.append(paragraph(`Original restrictions: ${restrictionSummary(data.original_interpretation)}`));
  if (data.applied_change) context.append(paragraph(`Selected change: ${data.applied_change}. Other restrictions preserved.`));
  interpretation.append(context);
  if (parsed.unsupported_requirements.length) {
    const warning = document.createElement('div');
    warning.className = 'warning';
    warning.setAttribute('role', 'note');
    warning.setAttribute('aria-label', 'Unchecked requirements');
    warning.append(paragraph('Some requirements could not be checked. Results and eligible counts use only the supported restrictions.'));
    for (const item of parsed.unsupported_requirements) warning.append(paragraph(`Not checked: ${item}`));
    interpretation.append(warning);
  }
  for (const question of parsed.clarification) interpretation.append(paragraph(`Please clarify: ${question}`));
}

function resizeRequest() {
  requestInput.style.height = 'auto';
  requestInput.style.height = `${Math.min(requestInput.scrollHeight + 2, 160)}px`;
}
requestInput.addEventListener('input', () => {
  suggestions.replaceChildren();
  resizeRequest();
});
window.addEventListener('resize', resizeRequest);
window.addEventListener('pageshow', resizeRequest);
document.fonts.ready.then(resizeRequest);
requestInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
    event.preventDefault();
    if (!button.disabled) form.requestSubmit();
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const request = requestInput.value.trim();
  if (!request) {
    status.textContent = 'Describe a movie before searching.';
    requestInput.focus();
    return;
  }
  requestInput.value = request;
  resizeRequest();
  await search(request);
});

const cancelButton = document.querySelector('#cancel');
let updateExplanation = () => {};
const recommendationSession = createRecommendationSession(outcome => {
  if (outcome.type === 'result') {
    updateExplanation = showResult(outcome.result);
  } else if (outcome.type === 'explanation') {
    updateExplanation(outcome.movieId, outcome);
  } else if (outcome.type === 'status') {
    status.textContent = outcome.message;
    status.classList.toggle('sr-only', outcome.quiet);
  } else if (outcome.type === 'busy') {
    button.disabled = outcome.busy;
    cancelButton.hidden = !outcome.busy;
    results.setAttribute('aria-busy', String(outcome.busy));
    if (outcome.busy) {
      suggestions.replaceChildren();
      document.body.classList.add('motion-paused');
    }
  }
});
cancelButton.addEventListener('click', () => recommendationSession.cancel());
window.addEventListener('pagehide', () => recommendationSession.cancel());

function showResult(data) {
  interpretation.replaceChildren();
  interpretation.hidden = true;
  spotlightCards.replace([]);
  preview.hidden = true;
  resultHeading.hidden = data.movies.length === 0;
  results.dataset.count = String(data.movies.length);
  resultCount.textContent = `${data.movies.length} ${data.movies.length === 1 ? 'film' : 'films'}`;
  results.classList.remove('is-replaced');
  if (data.original_request) showInterpretation(data);
  for (const suggestion of data.suggestions || []) {
    const option = document.createElement('button');
    option.type = 'button';
    option.textContent = `${suggestion.label} (${suggestion.candidate_count} eligible)`;
    option.addEventListener('click', () => search(data.original_request, suggestion.selection));
    suggestions.append(option);
  }
  const updateExplanation = recommendationCards.replace(data.movies);
  results.classList.add('is-replaced');
  return updateExplanation;
}

function search(request, selection = null) {
  return recommendationSession.start(request, selection);
}

// Each homepage visit and explicit shuffle asks for a fresh, bounded selection.
const shuffleButton = document.querySelector('#shuffle-preview');
shuffleButton.prepend(lineIcon('shuffle'));
let previewController = null;
let previewIds = [];
try {
  const saved = JSON.parse(sessionStorage.getItem('cinemood:spotlight') || '[]');
  if (Array.isArray(saved)) previewIds = saved.filter(id => Number.isSafeInteger(id) && id > 0).slice(0, 5);
} catch { /* Browsing remains available if session storage is disabled. */ }

async function loadPreview() {
  previewController?.abort();
  const controller = new AbortController();
  previewController = controller;
  const track = document.querySelector('#preview-track');
  shuffleButton.disabled = true;
  shuffleButton.classList.add('is-loading');
  track.setAttribute('aria-busy', 'true');
  previewStatus.textContent = track.children.length ? 'Finding a fresh selection…' : 'Loading the catalog…';
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const query = new URLSearchParams();
    for (const id of previewIds) query.append('exclude', id);
    const response = await fetch(`/api/catalog-preview?${query}`, { cache: 'no-store', signal: controller.signal });
    if (!response.ok) throw new Error('Preview unavailable');
    const data = await response.json();
    if (controller !== previewController) return;
    spotlightCards.replace(data.movies);
    previewIds = data.movies.map(movie => movie.id);
    try { sessionStorage.setItem('cinemood:spotlight', JSON.stringify(previewIds)); } catch { /* Optional storage. */ }
    shuffleButton.disabled = !data.has_more;
    previewStatus.textContent = !data.movies.length ? 'The catalog is empty. Movies will appear here after loading.'
      : data.has_more ? '' : 'You’re seeing all the films currently in this catalog.';
  } catch (error) {
    if (controller !== previewController) return;
    shuffleButton.disabled = false;
    previewStatus.textContent = controller.signal.aborted
      ? 'The preview took too long. Try Shuffle films again.'
      : 'Preview unavailable. Try Shuffle films again, or search above.';
  } finally {
    clearTimeout(timeout);
    if (controller === previewController) {
      shuffleButton.classList.remove('is-loading');
      track.setAttribute('aria-busy', 'false');
    }
  }
}
shuffleButton.addEventListener('click', loadPreview);
window.addEventListener('pageshow', (event) => { if (event.persisted) loadPreview(); });
loadPreview();
