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

function catalogCard(movie) {
  const card = document.createElement('article');
  card.dataset.movieId = movie.id;
  const title = document.createElement('h2');
  title.textContent = movie.title;
  const facts = document.createElement('p');
  facts.className = 'facts';
  facts.textContent = `${movie.release_year ?? 'Year unknown'} · ${movie.runtime_minutes ?? 'Unknown'} min · ${movie.genres.join(' / ')}`;
  const overview = document.createElement('p');
  overview.textContent = movie.overview;
  card.append(title, facts, overview);
  return card;
}

function collectionError(error) {
  return error instanceof TypeError || error.name === 'TimeoutError'
    ? 'Unable to reach your collection. Please try again.' : error.message;
}

function addCollectionAction(card, movie, removing = false) {
  const action = document.createElement('button');
  action.type = 'button';
  const feedback = document.createElement('p');
  feedback.setAttribute('role', 'status');
  feedback.setAttribute('aria-live', 'polite');
  const updateLabel = () => {
    const saved = savedMovieIds.has(movie.id);
    action.textContent = removing ? 'Remove' : saved ? 'Saved to collection' : 'Save to collection';
    action.disabled = !removing && saved;
  };
  updateLabel();
  collectionReady.then(updateLabel);
  action.addEventListener('click', async () => {
    action.disabled = true;
    feedback.textContent = removing ? 'Removing…' : 'Saving…';
    try {
      // Wait for initial cookie issuance before allowing concurrent saves.
      const pending = collectionReady;
      if (!await pending && collectionReady === pending) collectionReady = loadCollection();
      if (!await collectionReady) throw new Error('Unable to reach your collection. Please try again.');
      await collectionRequest(`/${movie.id}`, removing ? 'DELETE' : 'PUT');
      if (removing) {
        savedMovieIds.delete(movie.id);
        card.remove();
        updateCollectionCount();
      } else {
        savedMovieIds.add(movie.id);
        feedback.textContent = 'Saved. Find it in My collection.';
      }
    } catch (error) {
      feedback.textContent = collectionError(error);
    } finally {
      updateLabel();
    }
  });
  card.append(action, feedback);
}

function updateCollectionCount() {
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
    const data = await collectionRequest();
    savedMovieIds.clear();
    for (const movie of data.movies) savedMovieIds.add(movie.id);
    if (collectionResults) {
      collectionResults.replaceChildren();
      for (const movie of data.movies) {
        const card = catalogCard(movie);
        addCollectionAction(card, movie, true);
        collectionResults.append(card);
      }
      updateCollectionCount();
    }
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
