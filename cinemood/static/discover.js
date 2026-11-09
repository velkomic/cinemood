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
  if (parsed.runtime_minutes !== null) restrictions.push(`${parsed.runtime_operator === 'lt' ? 'Under' : 'At most'} ${parsed.runtime_minutes} minutes`);
  if (parsed.year_min !== null) restrictions.push(`Released from ${parsed.year_min} (inclusive)`);
  if (parsed.year_max !== null) restrictions.push(`Released through ${parsed.year_max} (inclusive)`);
  if (parsed.original_language) restrictions.push(`Original language: ${parsed.original_language}`);
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

async function search(request, selection = null) {
  button.disabled = true;
  suggestions.replaceChildren();
  interpretation.replaceChildren();
  interpretation.hidden = true;
  results.replaceChildren();
  results.setAttribute('aria-busy', 'true');
  status.textContent = selection ? 'Applying your selected change…' : 'Interpreting your request and searching the catalog…';
  try {
    const response = await fetch('/api/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request, selection }),
      signal: AbortSignal.timeout(45000),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Use a request of 1–2,000 characters.');
    }
    if (data.original_request) showInterpretation(data);
    for (const suggestion of data.suggestions || []) {
      const option = document.createElement('button');
      option.type = 'button';
      option.textContent = `${suggestion.label} (${suggestion.candidate_count} eligible)`;
      option.addEventListener('click', () => search(data.original_request, suggestion.selection));
      suggestions.append(option);
    }
    for (const [index, movie] of data.movies.entries()) {
      const card = document.createElement('article');
      const number = document.createElement('p');
      number.className = 'number';
      number.textContent = `0${index + 1} / CATALOG MATCH`;
      const title = document.createElement('h2');
      title.textContent = movie.title;
      const facts = document.createElement('p');
      facts.className = 'facts';
      facts.textContent = `${movie.release_year} · ${movie.runtime_minutes} min · ${movie.genres.join(' / ')}`;
      const overview = document.createElement('p');
      overview.textContent = movie.overview;
      card.append(number, title, facts, overview);
      results.append(card);
    }
    status.textContent = data.message;
  } catch (error) {
    status.textContent = error.name === 'TimeoutError'
      ? 'Search took too long. Please try again.'
      : error instanceof TypeError ? 'Unable to connect. Please try again.' : error.message;
  } finally {
    button.disabled = false;
    results.setAttribute('aria-busy', 'false');
  }
}
