// Catalog and model text is always rendered as text, never HTML.
let detailOpener = null;
let selectedCard = null;
let selectedMovieId = null;
let cardSequence = 0;

function movieFacts(movie, full = false) {
  const facts = [movie.release_year ?? 'Year unknown', `${movie.runtime_minutes ?? 'Unknown'} min`];
  if (full && movie.genres.length) facts.push(movie.genres.join(' / '));
  return facts.join(' · ');
}

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

function posterElement(movie) {
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
  }, { once: true });
  image.addEventListener('error', () => image.remove(), { once: true });
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
  selectedMovieId = null;
  detailOpener = null;
}

function openMovieDetails(movie, opener) {
  const card = opener.closest('.movie');
  if (selectedCard === card) {
    closeMovieDetails();
    return;
  }
  closeMovieDetails(false);
  selectedCard = card;
  selectedMovieId = movie.id;
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

function catalogCard(movie) {
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
  poster.append(posterElement(movie));
  poster.addEventListener('click', () => openMovieDetails(movie, poster));
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
  action.addEventListener('click', () => openMovieDetails(movie, action));
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
  card.append(poster, title, facts, details, actions);
  return card;
}

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
