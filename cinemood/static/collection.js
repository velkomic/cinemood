const savedMovieIds = new Set();
const collectionResults = document.querySelector('#collection-results');
const collectionStatus = document.querySelector('#collection-status');
const collectionRetry = document.querySelector('#collection-retry');

async function collectionRequest(path = '', method = 'GET') {
  const response = await fetch(`/api/collection${path}`, {
    method, credentials: 'same-origin', cache: 'no-store',
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Collection unavailable. Please try again.');
  }
  return method === 'GET' ? response.json() : null;
}

function collectionError(error) {
  return error instanceof TypeError || error.name === 'TimeoutError'
    ? 'Unable to reach your collection. Please try again.' : error.message;
}

function refreshCollectionActions() {
  for (const action of document.querySelectorAll('.save-action')) {
    const saved = savedMovieIds.has(Number(action.closest('.movie').dataset.movieId));
    const removing = action.dataset.removing === 'true';
    const pending = action.dataset.pending === 'true';
    const label = pending ? (removing ? 'Removing…' : 'Saving…') : removing ? 'Remove' : saved ? 'Saved' : 'Save';
    action.querySelector('span').textContent = label;
    const kind = saved && !removing ? 'check' : 'bookmark';
    if (action.dataset.icon !== kind) {
      action.querySelector('svg').replaceWith(lineIcon(kind));
      action.dataset.icon = kind;
    }
    action.classList.toggle('is-saved', saved && !removing);
    action.classList.toggle('is-loading', pending);
    action.setAttribute('aria-label', pending ? label : removing ? 'Remove' : saved ? 'Saved to collection' : 'Save to collection');
    action.setAttribute('aria-pressed', String(saved && !removing));
    action.setAttribute('aria-busy', String(pending));
    action.disabled = pending || (!removing && saved);
  }
}

function addCollectionAction(card, movie, removing = false) {
  const action = document.createElement('button');
  action.type = 'button';
  action.className = removing ? 'save-action is-remove' : 'save-action';
  action.dataset.removing = String(removing);
  action.title = removing ? `Remove ${movie.title} from My collection` : `Save ${movie.title} to My collection`;
  const feedback = document.createElement('p');
  feedback.className = 'save-feedback';
  feedback.setAttribute('role', 'status');
  feedback.setAttribute('aria-live', 'polite');
  action.addEventListener('click', async () => {
    action.dataset.pending = 'true';
    feedback.classList.remove('sr-only');
    feedback.textContent = '';
    refreshCollectionActions();
    try {
      const pending = collectionReady;
      if (!await pending && collectionReady === pending) collectionReady = loadCollection();
      if (!await collectionReady) throw new Error('Unable to reach your collection. Please try again.');
      await collectionRequest(`/${movie.id}`, removing ? 'DELETE' : 'PUT');
      if (removing) {
        savedMovieIds.delete(movie.id);
        if (selectedMovieId === movie.id) closeMovieDetails(false);
        const nextFocus = card.nextElementSibling?.querySelector('button') || card.previousElementSibling?.querySelector('button');
        card.remove();
        if (nextFocus) nextFocus.focus();
        else {
          collectionStatus.tabIndex = -1;
          collectionStatus.focus();
        }
        updateCollectionCount();
      } else {
        savedMovieIds.add(movie.id);
        feedback.classList.add('sr-only');
        feedback.textContent = 'Saved to My collection.';
      }
    } catch (error) {
      feedback.textContent = collectionError(error);
    } finally {
      action.dataset.pending = 'false';
      refreshCollectionActions();
    }
  });
  card.querySelector('.movie-actions').prepend(action);
  card.append(feedback);
  // Called before attachment; initialize this control, then sync attached copies.
  const label = document.createElement('span');
  label.textContent = removing ? 'Remove' : savedMovieIds.has(movie.id) ? 'Saved' : 'Save';
  action.dataset.icon = savedMovieIds.has(movie.id) && !removing ? 'check' : 'bookmark';
  action.append(lineIcon(action.dataset.icon), label);
  action.setAttribute('aria-label', removing ? 'Remove' : savedMovieIds.has(movie.id) ? 'Saved to collection' : 'Save to collection');
  action.disabled = !removing && savedMovieIds.has(movie.id);
  action.classList.toggle('is-saved', !removing && savedMovieIds.has(movie.id));
  action.setAttribute('aria-pressed', String(!removing && savedMovieIds.has(movie.id)));
  collectionReady.then(refreshCollectionActions);
}

function updateCollectionCount() {
  if (collectionResults) collectionResults.dataset.count = String(savedMovieIds.size);
  collectionStatus.textContent = savedMovieIds.size
    ? `${savedMovieIds.size} saved ${savedMovieIds.size === 1 ? 'movie' : 'movies'}.`
    : 'Your collection is empty. Discover a movie and save it here.';
}

async function loadCollection() {
  if (collectionResults) {
    collectionStatus.textContent = 'Loading your collection…';
    collectionResults.setAttribute('aria-busy', 'true');
    collectionRetry.hidden = true;
  }
  try {
    if (!navigator.locks) throw new Error('Collections need a current browser and HTTPS, or localhost for the local demo.');
    // Cookie issuance must finish before another tab sends its initial GET.
    const data = await navigator.locks.request('cinemood-collection-bootstrap', () => collectionRequest());
    savedMovieIds.clear();
    for (const movie of data.movies) savedMovieIds.add(movie.id);
    if (collectionResults) {
      if (selectedCard?.closest('#collection-results')) closeMovieDetails(false);
      collectionResults.replaceChildren();
      for (const movie of data.movies) {
        const card = catalogCard(movie);
        addCollectionAction(card, movie, true);
        collectionResults.append(card);
      }
      updateCollectionCount();
    }
    refreshCollectionActions();
    return true;
  } catch (error) {
    if (collectionResults) {
      collectionStatus.textContent = collectionError(error);
      collectionRetry.hidden = false;
    }
    return false;
  } finally {
    collectionResults?.setAttribute('aria-busy', 'false');
  }
}

let collectionReady = loadCollection();
collectionRetry?.addEventListener('click', () => { collectionReady = loadCollection(); });

window.addEventListener('pageshow', (event) => {
  if (event.persisted) collectionReady = loadCollection();
});
