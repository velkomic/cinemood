const savedMovieIds = new Set();
const pendingCollectionMovies = new Set();
const collectionErrors = new Map();
const collectionGroups = new Map();
const collectionResults = document.querySelector('#collection-results');
const collectionStatus = document.querySelector('#collection-status');
const collectionRetry = document.querySelector('#collection-retry');
let mutationRevision = 0;
let loadSequence = 0;
let refreshNeeded = false;

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

function readCollectionState(movieId) {
  return {saved: savedMovieIds.has(movieId), pending: pendingCollectionMovies.has(movieId), error: collectionErrors.get(movieId) || ''};
}

function publishCollectionState(movieId) {
  for (const group of collectionGroups.keys()) group.setCollectionState(movieId, readCollectionState(movieId));
}

function createCollectionCardGroup(container, context, focusFallback) {
  const group = createMovieCardGroup({
    container, context, focusFallback,
    readCollectionState, onCollectionAction: mutateCollection,
    onDispose: () => collectionGroups.delete(group),
  });
  collectionGroups.set(group, context);
  return group;
}

const collectionGroup = collectionResults
  ? createCollectionCardGroup(collectionResults, 'collection', collectionStatus) : null;
if (collectionStatus) collectionStatus.tabIndex = -1;

async function mutateCollection(movieId, removing) {
  if (pendingCollectionMovies.has(movieId)) return;
  pendingCollectionMovies.add(movieId);
  ++mutationRevision;
  collectionErrors.delete(movieId);
  publishCollectionState(movieId);
  try {
    const bootstrap = collectionReady;
    if (!await bootstrap && collectionReady === bootstrap) collectionReady = loadCollection();
    if (!await collectionReady) throw new Error('Unable to reach your collection. Please try again.');
    await collectionRequest(`/${movieId}`, removing ? 'DELETE' : 'PUT');
    if (removing) {
      savedMovieIds.delete(movieId);
      for (const [group, context] of collectionGroups) {
        if (context === 'collection') group.remove(movieId);
      }
      if (collectionGroup) updateCollectionCount();
    } else {
      savedMovieIds.add(movieId);
    }
  } catch (error) {
    collectionErrors.set(movieId, collectionError(error));
  } finally {
    pendingCollectionMovies.delete(movieId);
    publishCollectionState(movieId);
    refreshCollectionIfNeeded();
  }
}

function updateCollectionCount() {
  collectionResults.dataset.count = String(savedMovieIds.size);
  collectionStatus.textContent = savedMovieIds.size
    ? `${savedMovieIds.size} saved ${savedMovieIds.size === 1 ? 'movie' : 'movies'}.`
    : 'Your collection is empty. Discover a movie and save it here.';
}

function refreshCollectionIfNeeded() {
  if (refreshNeeded && !pendingCollectionMovies.size) {
    refreshNeeded = false;
    collectionReady = loadCollection();
  }
}

async function loadCollection() {
  const sequence = ++loadSequence;
  const revision = mutationRevision;
  const startedWithMutation = pendingCollectionMovies.size > 0;
  if (collectionResults) {
    collectionStatus.textContent = 'Loading your collection…';
    collectionResults.setAttribute('aria-busy', 'true');
    collectionRetry.hidden = true;
  }
  try {
    if (!navigator.locks) throw new Error('Collections need a current browser and HTTPS, or localhost for the local demo.');
    // Serialize identity issuance across tabs; never hold the lock for mutations.
    const data = await navigator.locks.request('cinemood-collection-bootstrap', () => collectionRequest());
    if (sequence !== loadSequence) return true;
    // A GET snapshot cannot establish ordering with any overlapping mutation.
    if (startedWithMutation || revision !== mutationRevision) {
      refreshNeeded = true;
      return true;
    }
    refreshNeeded = false;
    const changed = new Set([...savedMovieIds, ...data.movies.map(movie => movie.id)]);
    savedMovieIds.clear();
    for (const movie of data.movies) savedMovieIds.add(movie.id);
    collectionGroup?.replace(data.movies);
    if (collectionGroup) updateCollectionCount();
    for (const movieId of changed) publishCollectionState(movieId);
    return true;
  } catch (error) {
    if (sequence === loadSequence && collectionResults) {
      collectionStatus.textContent = collectionError(error);
      collectionRetry.hidden = false;
    }
    return false;
  } finally {
    if (sequence === loadSequence) {
      collectionResults?.setAttribute('aria-busy', 'false');
      refreshCollectionIfNeeded();
    }
  }
}

let collectionReady = loadCollection();
collectionRetry?.addEventListener('click', () => { collectionReady = loadCollection(); });
window.addEventListener('pageshow', (event) => {
  if (event.persisted) collectionReady = loadCollection();
});
