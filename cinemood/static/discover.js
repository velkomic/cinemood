const form = document.querySelector('#discover');
const requestInput = document.querySelector('#request');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const button = form.querySelector('button');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const request = requestInput.value.trim();
  if (!request) {
    status.textContent = 'Describe a movie before searching.';
    requestInput.focus();
    return;
  }
  button.disabled = true;
  results.replaceChildren();
  results.setAttribute('aria-busy', 'true');
  status.textContent = 'Searching the catalog…';
  try {
    const response = await fetch('/api/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request }),
      signal: AbortSignal.timeout(25000),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Use a request of 1–2,000 characters.');
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
});
