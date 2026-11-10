const form = document.querySelector('#discover');
const requestInput = document.querySelector('#request');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const button = form.querySelector('button');
const interpretation = document.querySelector('#interpretation');
const suggestions = document.querySelector('#suggestions');

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
  return restrictions.length ? restrictions.join(' · ') : 'No supported hard restrictions.';
}

function showInterpretation(data) {
  interpretation.replaceChildren();
  interpretation.hidden = false;
  interpretation.append(paragraph(`Original request: ${data.original_request}`));
  const parsed = data.interpretation;
  if (!parsed) return;
  if (data.applied_change) {
    interpretation.append(paragraph(`Original restrictions: ${restrictionSummary(data.original_interpretation)}`));
  }
  interpretation.append(paragraph(`Current restrictions: ${restrictionSummary(parsed)}`));
  interpretation.append(paragraph(`Mood / themes: ${parsed.semantic_query}`));
  if (data.applied_change) interpretation.append(paragraph(`Selected change: ${data.applied_change}. Other restrictions preserved.`));
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

requestInput.addEventListener('input', () => suggestions.replaceChildren());

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const request = requestInput.value.trim();
  if (!request) {
    status.textContent = 'Describe a movie before searching.';
    requestInput.focus();
    return;
  }
  await search(request);
});

let activeController = null;
const cancelButton = document.querySelector('#cancel');
cancelButton.addEventListener('click', () => activeController?.abort());
window.addEventListener('pagehide', () => activeController?.abort());

function showResult(data, explanations) {
  if (data.original_request) showInterpretation(data);
  for (const suggestion of data.suggestions || []) {
    const option = document.createElement('button');
    option.type = 'button';
    option.textContent = `${suggestion.label} (${suggestion.candidate_count} eligible)`;
    option.addEventListener('click', () => search(data.original_request, suggestion.selection));
    suggestions.append(option);
  }
  for (const [index, movie] of data.movies.entries()) {
    const card = catalogCard(movie);
    const number = paragraph(`0${index + 1} / CATALOG MATCH`);
    number.className = 'number';
    const explanation = paragraph('Generating explanation…');
    explanation.className = 'explanation';
    const text = paragraph('');
    text.className = 'explanation-text';
    card.prepend(number);
    card.append(explanation, text);
    addCollectionAction(card, movie);
    results.append(card);
    explanations.set(movie.id, { label: explanation, text, complete: false });
  }
  status.textContent = data.message;
}

// Streaming UTF-8 decoder and frame buffer survive arbitrary network boundaries.
async function consumeEvents(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let buffer = '';
  let terminal = false;
  let sequence = 0;
  let requestId = null;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const lines = frame.split('\n');
        const event = lines.find(line => line.startsWith('event: '))?.slice(7);
        const payload = lines.filter(line => line.startsWith('data: ')).map(line => line.slice(6)).join('\n');
        const data = JSON.parse(payload);
        if (terminal || data.sequence !== ++sequence || !data.request_id ||
            (requestId !== null && requestId !== data.request_id)) throw new Error('Invalid recommendation stream.');
        requestId = data.request_id;
        terminal = event === 'complete' || event === 'error';
        onEvent(event, data);
      }
      if (buffer.length > 65536) throw new Error('Invalid recommendation stream.');
      if (done) break;
    }
    if (!terminal || buffer.trim()) throw new Error('Search interrupted. Please try again.');
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

async function search(request, selection = null) {
  if (activeController) return;
  const controller = new AbortController();
  activeController = controller;
  const timeout = setTimeout(() => controller.abort(new DOMException('Search took too long.', 'TimeoutError')), 80000);
  button.disabled = true;
  cancelButton.hidden = false;
  suggestions.replaceChildren();
  interpretation.replaceChildren();
  interpretation.hidden = true;
  results.replaceChildren();
  results.setAttribute('aria-busy', 'true');
  status.textContent = 'Starting search…';
  const explanations = new Map();
  let resultMessage = '';
  const discardTentative = () => {
    for (const item of explanations.values()) {
      if (!item.complete) {
        item.text.textContent = '';
        item.label.textContent = 'Explanation unavailable. Catalog details are still available.';
      }
    }
  };
  try {
    const response = await fetch('/api/recommendations/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request, selection }), signal: controller.signal,
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Use a request of 1–2,000 characters.');
    }
    if (!response.headers.get('content-type')?.startsWith('text/event-stream')) throw new Error('Invalid recommendation stream.');
    await consumeEvents(response, (event, data) => {
      if (event === 'status') {
        const labels = { interpretation: 'Interpreting your request…', retrieval: 'Searching the catalog…', explanation: 'Explaining catalog matches…' };
        status.textContent = labels[data.stage] || 'Searching…';
      } else if (event === 'result') {
        resultMessage = data.message;
        showResult(data, explanations);
      } else if (event === 'explanation_delta' || event === 'explanation_complete' || event === 'explanation_error') {
        const item = explanations.get(data.movie_id);
        if (!item || item.complete) throw new Error('Invalid explanation identity.');
        if (event === 'explanation_delta') {
          item.label.textContent = 'Generating explanation (not yet validated)…';
          item.text.textContent += data.text;
        } else if (event === 'explanation_complete') {
          item.complete = true;
          item.label.textContent = 'Why this may fit';
          item.text.textContent = data.text;
        } else {
          item.text.textContent = '';
          item.label.textContent = data.message;
        }
      } else if (event === 'complete') {
        discardTentative();
        status.textContent = resultMessage;
      } else if (event === 'error') {
        throw new Error(data.message);
      } else {
        throw new Error('Unknown recommendation event.');
      }
    });
  } catch (error) {
    discardTentative();
    status.textContent = controller.signal.aborted
      ? (controller.signal.reason?.name === 'TimeoutError' ? 'Search took too long. Please try again.' : 'Search cancelled. Catalog details are still available.')
      : error instanceof TypeError ? 'Unable to connect. Please try again.' : error.message;
  } finally {
    clearTimeout(timeout);
    activeController = null;
    button.disabled = false;
    cancelButton.hidden = true;
    results.setAttribute('aria-busy', 'false');
  }
}
