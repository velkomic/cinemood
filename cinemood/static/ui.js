function lineIcon(kind) {
  const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  icon.setAttribute('viewBox', '0 0 20 20');
  icon.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  const paths = {
    bookmark: 'M5 3h10v14l-5-3-5 3V3Z',
    check: 'm4 10 4 4 8-8',
    shuffle: 'M4 5h3l6 10h3m-3-3 3 3-3 3M4 15h3l2-3m2-4 2-3h3m-3-3 3 3-3 3',
  };
  path.setAttribute('d', paths[kind] || paths.bookmark);
  icon.append(path);
  return icon;
}

const createMovieCardGroup = (() => {
  // Catalog and model text is always rendered as text, never HTML.
  let detailOpener = null;
  let selectedCard = null;
  let cardSequence = 0;

  function movieFacts(movie, full = false) {
    const facts = [movie.release_year ?? 'Year unknown', `${movie.runtime_minutes ?? 'Unknown'} min`];
    if (full && movie.genres.length) facts.push(movie.genres.join(' / '));
    return facts.join(' · ');
  }

  function posterElement(movie, signal) {
    const poster = document.createElement('div');
    poster.className = 'poster';
    const fallback = document.createElement('span');
    fallback.className = 'poster-fallback';
    const title = document.createElement('strong');
    title.textContent = movie.title;
    const note = document.createElement('small');
    note.textContent = 'Poster unavailable';
    fallback.append(title, note);
    const image = document.createElement('img');
    image.alt = '';
    image.loading = 'lazy';
    image.decoding = 'async';
    image.referrerPolicy = 'no-referrer';
    image.src = `/api/movies/${movie.id}/poster`;
    image.addEventListener('load', () => {
      poster.style.setProperty('--poster-image', `url("${image.currentSrc}")`);
      poster.classList.add('has-image');
    }, { once: true, signal });
    image.addEventListener('error', () => image.remove(), { once: true, signal });
    poster.append(fallback, image);
    return poster;
  }

  function closeMovieDetails(returnFocus = true) {
    if (!selectedCard) return;
    const focusWasInside = selectedCard.querySelector('.movie-details').contains(document.activeElement);
    selectedCard.classList.remove('is-expanded');
    selectedCard.removeAttribute('aria-current');
    selectedCard.querySelector('.movie-details').hidden = true;
    for (const control of selectedCard.querySelectorAll('[aria-expanded]')) control.setAttribute('aria-expanded', 'false');
    selectedCard.querySelector('.details-action').textContent = 'Details';
    if ((returnFocus || focusWasInside) && detailOpener?.isConnected) detailOpener.focus({ preventScroll: true });
    selectedCard = null;
    detailOpener = null;
  }

  function openMovieDetails(opener) {
    const card = opener.closest('.movie');
    if (selectedCard === card) {
      closeMovieDetails();
      return;
    }
    closeMovieDetails(false);
    selectedCard = card;
    detailOpener = opener;
    card.classList.add('is-expanded');
    card.setAttribute('aria-current', 'true');
    card.querySelector('.movie-details').hidden = false;
    for (const control of card.querySelectorAll('[aria-expanded]')) control.setAttribute('aria-expanded', 'true');
    card.querySelector('.details-action').textContent = 'Close details';
    document.body.classList.add('motion-paused');
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && selectedCard) {
      event.preventDefault();
      closeMovieDetails();
    }
  });

  function catalogCard(movie, context, onCollectionAction, initialState) {
    const lifetime = new AbortController();
    const signal = lifetime.signal;
    const card = document.createElement('article');
    card.className = 'movie';
    card.dataset.movieId = movie.id;
    const detailId = `movie-details-${movie.id}-${++cardSequence}`;
    const poster = document.createElement('button');
    poster.type = 'button';
    poster.className = 'poster-button';
    poster.setAttribute('aria-label', `Details for ${movie.title}`);
    poster.setAttribute('aria-controls', detailId);
    poster.setAttribute('aria-expanded', 'false');
    poster.append(posterElement(movie, signal));
    poster.addEventListener('click', () => openMovieDetails(poster), {signal});
    const title = document.createElement('h2');
    title.className = 'movie-title';
    title.textContent = movie.title;
    const facts = document.createElement('p');
    facts.className = 'facts';
    facts.textContent = movieFacts(movie);
    const actions = document.createElement('div');
    actions.className = 'movie-actions';
    const action = document.createElement('button');
    action.type = 'button';
    action.className = 'text-action details-action';
    action.textContent = 'Details';
    action.setAttribute('aria-label', `Toggle details for ${movie.title}`);
    action.setAttribute('aria-controls', detailId);
    action.setAttribute('aria-expanded', 'false');
    action.addEventListener('click', () => openMovieDetails(action), {signal});
    actions.append(action);
    const details = document.createElement('section');
    details.className = 'movie-details';
    details.id = detailId;
    details.hidden = true;
    details.setAttribute('aria-label', `${movie.title} details`);
    const heading = document.createElement('h3');
    heading.textContent = 'Synopsis';
    const overview = document.createElement('p');
    overview.className = 'synopsis';
    overview.textContent = movie.overview;
    overview.tabIndex = 0;
    overview.setAttribute('aria-label', `${movie.title} synopsis`);
    const metadata = document.createElement('p');
    metadata.className = 'detail-facts';
    metadata.textContent = movieFacts(movie, true);
    details.append(heading, overview, metadata);
    const tmdb = /^tmdb:([1-9]\d*)$/.exec(movie.source_id || '');
    if (tmdb) {
      const link = document.createElement('a');
      link.href = `https://www.themoviedb.org/movie/${tmdb[1]}`;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'View on TMDB';
      link.className = 'tmdb-link';
      link.setAttribute('aria-label', `View ${movie.title} on TMDB (opens in a new tab)`);
      details.append(link);
    }
    const explanation = document.createElement('p');
    explanation.className = 'explanation';
    const text = document.createElement('p');
    text.className = 'explanation-text';
    const save = document.createElement('button');
    save.type = 'button';
    const removing = context === 'collection';
    save.className = removing ? 'save-action is-remove' : 'save-action';
    save.title = removing ? `Remove ${movie.title} from My collection` : `Save ${movie.title} to My collection`;
    const label = document.createElement('span');
    save.append(lineIcon('bookmark'), label);
    const feedback = document.createElement('p');
    feedback.className = 'save-feedback';
    feedback.setAttribute('role', 'status');
    feedback.setAttribute('aria-live', 'polite');
    save.addEventListener('click', () => onCollectionAction(movie.id, removing), {signal});
    actions.prepend(save);
    card.append(poster, title, facts, details);
    if (context === 'recommendations') card.append(explanation, text);
    card.append(actions, feedback);
    if (context === 'spotlight') card.classList.add('preview-film');
    const setCollectionState = ({saved, pending, error}) => {
      const message = pending ? (removing ? 'Removing…' : 'Saving…') : removing ? 'Remove' : saved ? 'Saved' : 'Save';
      label.textContent = message;
      const kind = saved && !removing ? 'check' : 'bookmark';
      if (save.dataset.icon !== kind) {
        save.querySelector('svg').replaceWith(lineIcon(kind));
        save.dataset.icon = kind;
      }
      save.classList.toggle('is-saved', saved && !removing);
      save.classList.toggle('is-loading', pending);
      save.setAttribute('aria-label', pending ? message : removing ? 'Remove' : saved ? 'Saved to collection' : 'Save to collection');
      save.setAttribute('aria-pressed', String(saved && !removing));
      save.setAttribute('aria-busy', String(pending));
      // Disabling a focused action drops browser focus to the body. Keep it in
      // this displayed card so removal can apply the normal neighbour fallback.
      if (pending && document.activeElement === save) poster.focus({preventScroll: true});
      save.disabled = pending || (!removing && saved);
      feedback.classList.toggle('sr-only', !error);
      feedback.textContent = error || (saved && !removing ? 'Saved to My collection.' : '');
    };
    const setExplanation = ({phase, text: value = '', message}) => {
      explanation.textContent = message ?? ({
        pending: 'Generating explanation…',
        tentative: 'Generating explanation (not yet validated)…',
        complete: 'Why this may fit',
        unavailable: 'Explanation unavailable. Catalog details are still available.',
      })[phase];
      explanation.classList.toggle('is-complete', phase === 'complete');
      text.textContent = value;
    };
    setCollectionState(initialState);
    setExplanation({phase: 'pending'});
    return {element: card, focusTarget: poster, setCollectionState, setExplanation, dispose: () => lifetime.abort()};
  }


  // Display generations own DOM lifetimes; callers only supply presentation values.
  return function createMovieCardGroup({container, context, onCollectionAction,
      readCollectionState, focusFallback, onDispose = () => {}}) {
    const cards = new Map();
    let generation = 0;
    let disposed = false;
    const focus = target => {
      if (target?.isConnected) target.focus({preventScroll: true});
    };
    const clear = () => {
      const hadFocus = container.contains(document.activeElement);
      if (selectedCard && container.contains(selectedCard)) closeMovieDetails(false);
      for (const card of cards.values()) card.dispose();
      cards.clear();
      container.replaceChildren();
      container.dataset.count = '0';
      if (hadFocus) focus(focusFallback);
    };
    return {
      replace(movies) {
        if (disposed) return () => {};
        const current = ++generation;
        clear();
        for (const movie of movies) {
          const card = catalogCard(movie, context, onCollectionAction, readCollectionState(movie.id));
          cards.set(movie.id, card);
          container.append(card.element);
        }
        container.dataset.count = String(cards.size);
        return (movieId, presentation) => {
          if (!disposed && current === generation) cards.get(movieId)?.setExplanation(presentation);
        };
      },
      setCollectionState(movieId, state) {
        if (!disposed) cards.get(movieId)?.setCollectionState(state);
      },
      remove(movieId) {
        const card = cards.get(movieId);
        if (disposed || !card) return;
        const hadFocus = card.element.contains(document.activeElement);
        const ordered = [...cards.values()];
        const index = ordered.indexOf(card);
        const target = ordered[index + 1]?.focusTarget || ordered[index - 1]?.focusTarget || focusFallback;
        if (selectedCard === card.element) closeMovieDetails(false);
        card.dispose();
        cards.delete(movieId);
        card.element.remove();
        container.dataset.count = String(cards.size);
        if (hadFocus) focus(target);
      },
      dispose() {
        if (disposed) return;
        disposed = true;
        ++generation;
        clear();
        onDispose();
      },
    };
  };
})();

for (const event of ['pointerdown', 'keydown', 'wheel', 'touchstart', 'focusin']) {
  document.addEventListener(event, () => document.body.classList.add('motion-paused'), { once: true, passive: true });
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden) document.body.classList.add('motion-paused');
});

// Keep navigation available without consuming space while reading down the page.
const siteHeader = document.querySelector('.site-header');
if (siteHeader) {
  let lastScroll = window.scrollY;
  let direction = 0;
  let distance = 0;
  let scheduled = false;
  const revealHeader = () => siteHeader.classList.remove('is-hidden');
  window.addEventListener('scroll', () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      const y = Math.max(0, Math.min(window.scrollY, document.documentElement.scrollHeight - innerHeight));
      const delta = y - lastScroll;
      const nextDirection = Math.sign(delta);
      if (nextDirection !== direction) distance = 0;
      distance += Math.abs(delta);
      direction = nextDirection;
      lastScroll = y;
      if (y <= siteHeader.offsetHeight || siteHeader.matches(':focus-within, :hover')) {
        revealHeader();
      } else if (distance >= 12) {
        siteHeader.classList.toggle('is-hidden', delta > 0);
      }
    });
  }, { passive: true });
  document.addEventListener('pointermove', (event) => {
    if (event.pointerType === 'mouse' && event.clientY <= 20) revealHeader();
  }, { passive: true });
  siteHeader.addEventListener('focusin', revealHeader);
  window.addEventListener('pageshow', () => {
    lastScroll = window.scrollY;
    distance = 0;
    revealHeader();
  });
}
