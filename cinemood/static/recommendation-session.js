// One page session owns transport, protocol and explanation lifetime; no DOM access.
function createRecommendationSession(onOutcome) {
  let active = null;
  let disposed = false;
  const publish = outcome => { if (!disposed) onOutcome(outcome); };
  const invalid = () => { throw new Error('Invalid recommendation stream.'); };
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const strings = value => Array.isArray(value) && value.every(item => typeof item === 'string');
  const id = value => Number.isSafeInteger(value) && value > 0;
  const optionalNumber = value => value === null || Number.isFinite(value);

  // Validate only what presentation consumes; evidence/constraint semantics stay server-side.
  function interpretation(value) {
    if (!object(value) || !strings(value.included_genres) || !strings(value.excluded_genres) ||
        !strings(value.original_languages) || !strings(value.unsupported_requirements) ||
        !strings(value.clarification) || typeof value.semantic_query !== 'string' ||
        ![null, 'lt', 'lte'].includes(value.runtime_operator) ||
        ((value.runtime_minutes === null) !== (value.runtime_operator === null)) ||
        !optionalNumber(value.runtime_minutes) || !optionalNumber(value.year_min) ||
        !optionalNumber(value.year_max) ||
        (value.excluded_original_languages !== undefined && !strings(value.excluded_original_languages))) invalid();
  }

  function validateResult(data) {
    if (!Array.isArray(data.movies) || typeof data.message !== 'string') invalid();
    const ids = new Set();
    for (const movie of data.movies) {
      if (!object(movie) || !id(movie.id) || ids.has(movie.id) ||
          typeof movie.title !== 'string' || typeof movie.overview !== 'string' ||
          !strings(movie.genres) || !optionalNumber(movie.release_year) ||
          !optionalNumber(movie.runtime_minutes) ||
          (movie.source_id !== undefined && typeof movie.source_id !== 'string')) invalid();
      ids.add(movie.id);
    }
    if (data.original_request !== undefined && typeof data.original_request !== 'string') invalid();
    if (data.suggestions?.length && (typeof data.original_request !== 'string' || !data.original_request.trim())) invalid();
    if (data.interpretation != null) interpretation(data.interpretation);
    if (data.applied_change != null) {
      if (typeof data.applied_change !== 'string') invalid();
      interpretation(data.original_interpretation);
    }
    if (data.suggestions !== undefined && (!Array.isArray(data.suggestions) ||
        data.suggestions.some(item => !object(item) || typeof item.label !== 'string' ||
          !Number.isSafeInteger(item.candidate_count) || item.candidate_count < 0 ||
          typeof item.selection !== 'string'))) invalid();
  }

  async function start(request, selection = null) {
    if (disposed || active) return;
    const controller = new AbortController();
    active = controller;
    const timeout = setTimeout(() => controller.abort(new DOMException('Search took too long.', 'TimeoutError')), 80000);
    const explanations = new Map();
    let reader = null;
    let result = null;
    let terminal = false;
    let terminalError = null;
    let sequence = 0;
    let requestId = null;
    const status = (message, quiet = false) => publish({type: 'status', message, quiet});
    const explanation = (movieId, phase, text = '', message) => publish({type: 'explanation', movieId, phase, text, message});
    const discardTentative = () => {
      for (const [movieId, item] of explanations) {
        if (!item.finished) {
          item.finished = true;
          item.text = '';
          explanation(movieId, 'unavailable');
        }
      }
    };
    function event(name, data) {
      if (controller.signal.aborted) throw controller.signal.reason;
      if (terminal || !object(data) || !Number.isSafeInteger(data.sequence) ||
          data.sequence !== sequence + 1 || typeof data.request_id !== 'string' ||
          !data.request_id.trim() || (requestId !== null && requestId !== data.request_id)) invalid();
      sequence = data.sequence;
      requestId = data.request_id;
      if (name === 'status') {
        if (typeof data.stage !== 'string') invalid();
        const labels = {interpretation: 'Interpreting your request…', retrieval: 'Searching the catalog…', explanation: 'Explaining catalog matches…'};
        status(labels[data.stage] || 'Searching…');
      } else if (name === 'result') {
        if (result !== null) invalid();
        validateResult(data);
        result = data;
        for (const movie of data.movies) explanations.set(movie.id, {text: '', finished: false});
        publish({type: 'result', result: data});
        status(data.message);
      } else if (['explanation_delta', 'explanation_complete', 'explanation_error'].includes(name)) {
        const item = explanations.get(data.movie_id);
        if (!id(data.movie_id) || !item || item.finished) invalid();
        if (name === 'explanation_error') {
          if (typeof data.message !== 'string') invalid();
          item.finished = true;
          item.text = '';
          explanation(data.movie_id, 'unavailable', '', data.message);
        } else {
          if (typeof data.text !== 'string') invalid();
          item.text = name === 'explanation_delta' ? item.text + data.text : data.text;
          item.finished = name === 'explanation_complete';
          explanation(data.movie_id, item.finished ? 'complete' : 'tentative', item.text);
        }
      } else if (name === 'complete') {
        if (result === null) invalid();
        terminal = true;
        discardTentative();
      } else if (name === 'error') {
        if (typeof data.message !== 'string') invalid();
        terminal = true;
        terminalError = data.message;
        discardTentative();
        status(data.message);
      } else invalid();
    }
    publish({type: 'busy', busy: true});
    status('Starting search…');
    try {
      const response = await fetch('/api/recommendations/stream', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({request, selection}), signal: controller.signal,
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(typeof data?.detail === 'string' ? data.detail : 'Use a request of 1–2,000 characters.');
      }
      if (!response.headers.get('content-type')?.startsWith('text/event-stream') || !response.body) {
        await response.body?.cancel();
        invalid();
      }
      reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8', {fatal: true});
      let buffer = '';
      while (true) {
        const {value, done} = await reader.read();
        if (controller.signal.aborted) throw controller.signal.reason;
        buffer += decoder.decode(value, {stream: !done});
        let boundary;
        while ((boundary = buffer.indexOf('\n\n')) !== -1) {
          if (boundary > 65536) invalid();
          const frame = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          if (terminal && !frame.trim()) continue;
          const lines = frame.split('\n');
          const names = lines.filter(line => line.startsWith('event: '));
          if (names.length !== 1) invalid();
          const payload = lines.filter(line => line.startsWith('data: ')).map(line => line.slice(6)).join('\n');
          event(names[0].slice(7), JSON.parse(payload));
        }
        // A final LF may be the first half of the delimiter, not frame content.
        if (buffer.length - (buffer.endsWith('\n') ? 1 : 0) > 65536) invalid();
        if (done) break;
      }
      if (!terminal || buffer.trim()) throw new Error('Search interrupted. Please try again.');
      if (terminalError === null) status(result.message, result.movies.length > 0);
    } catch (error) {
      discardTentative();
      status(controller.signal.aborted
        ? (controller.signal.reason?.name === 'TimeoutError' ? 'Search took too long. Please try again.' : 'Search cancelled. Catalog details are still available.')
        : error instanceof TypeError ? 'Unable to connect. Please try again.' : error.message);
    } finally {
      clearTimeout(timeout);
      if (reader) {
        await reader.cancel().catch(() => {});
        reader.releaseLock();
      }
      active = null;
      publish({type: 'busy', busy: false});
    }
  }
  return {
    start,
    cancel() { active?.abort(); },
    dispose() { disposed = true; active?.abort(); },
  };
}
