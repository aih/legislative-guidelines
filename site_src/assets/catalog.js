(function () {
  var list = document.getElementById('catalog');
  var items = Array.prototype.slice.call(list.querySelectorAll('li.g-item'));
  var az = document.getElementById('az');
  var count = document.getElementById('f-count');
  var empty = document.getElementById('f-empty');
  var form = document.getElementById('filters');
  var f = {
    text: document.getElementById('f-text'),
    sort: document.getElementById('f-sort'),
    level: document.getElementById('f-level'),
    tradition: document.getElementById('f-tradition'),
    region: document.getElementById('f-region'),
    lang: document.getElementById('f-lang'),
    html: document.getElementById('f-html'),
    status: document.getElementById('f-status')
  };
  Object.keys(f).forEach(function (k) { if (!f[k]) delete f[k]; });
  var collator = new Intl.Collator('en', { sensitivity: 'base', ignorePunctuation: true });

  function letterOf(s) {
    var c = s.normalize('NFD').replace(/[^A-Za-z0-9]/g, '').charAt(0).toUpperCase();
    return /[A-Z]/.test(c) ? c : '#';
  }

  function sortKey(item) {
    var j = item.dataset.jurisdiction, t = item.dataset.title;
    if (f.sort.value === 'title') return [t, j];
    if (f.sort.value === 'language') return [item.dataset.lang || '~', j];
    return [j, t];
  }

  // Group heading shown above each run of items: initial letter, language, or year.
  function groupOf(item) {
    if (f.sort.value === 'language') return item.dataset.lang || 'Unknown language';
    if (f.sort.value === 'recent') {
      var r = item.dataset.recency;
      if (r === '9999') return 'Maintained online';
      return r ? r.slice(0, 4) : 'Date unknown';
    }
    return letterOf(sortKey(item)[0]);
  }

  // Newest first; online texts without dated editions lead, undated entries trail.
  function compareRecency(a, b) {
    var ra = a.dataset.recency, rb = b.dataset.recency;
    if (ra !== rb) return ra < rb ? 1 : -1;
    return collator.compare(a.dataset.jurisdiction, b.dataset.jurisdiction);
  }

  function matches(r) {
    var q = f.text.value.trim().toLowerCase();
    return (!q || r.dataset.text.indexOf(q) !== -1) &&
      (!f.level.value || r.dataset.level === f.level.value) &&
      (!f.tradition || !f.tradition.value || r.dataset.tradition === f.tradition.value) &&
      (!f.region.value || r.dataset.region === f.region.value) &&
      (!f.lang.value || r.dataset.langs.split('|').indexOf(f.lang.value) !== -1) &&
      (!f.html || !f.html.value || r.dataset.html === f.html.value) &&
      (!f.status.value || r.dataset.status === f.status.value);
  }

  function render() {
    items.sort(f.sort.value === 'recent' ? compareRecency : function (a, b) {
      var ka = sortKey(a), kb = sortKey(b);
      return collator.compare(ka[0], kb[0]) || collator.compare(ka[1], kb[1]);
    });
    var byLetter = f.sort.value === 'jurisdiction' || f.sort.value === 'title';
    az.hidden = !byLetter;
    list.innerHTML = '';
    var letters = {}, shown = 0, current = null;
    items.forEach(function (r) {
      if (!matches(r)) return;
      shown++;
      var group = groupOf(r);
      if (group !== current) {
        current = group;
        letters[group] = true;
        var h = document.createElement('li');
        h.className = 'g-letter';
        if (byLetter) h.id = 'letter-' + group;
        h.textContent = group;
        list.appendChild(h);
      }
      list.appendChild(r);
    });
    az.innerHTML = '';
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach(function (l) {
      var el;
      if (letters[l]) {
        el = document.createElement('a');
        el.href = '#letter-' + l;
      } else {
        el = document.createElement('span');
        el.setAttribute('aria-hidden', 'true');
      }
      el.textContent = l;
      az.appendChild(el);
    });
    count.textContent = shown === items.length ? items.length + ' guidelines' : shown + ' of ' + items.length + ' guidelines';
    empty.hidden = shown > 0;
  }

  function saveState() {
    var params = new URLSearchParams();
    Object.keys(f).forEach(function (k) {
      if (f[k].value && !(k === 'sort' && f[k].value === 'jurisdiction')) params.set(k, f[k].value);
    });
    var qs = params.toString();
    history.replaceState(null, '', qs ? '?' + qs : location.pathname);
  }

  var initial = new URLSearchParams(location.search);
  Object.keys(f).forEach(function (k) {
    if (initial.has(k)) f[k].value = initial.get(k);
    f[k].addEventListener('input', function () { render(); saveState(); });
  });
  form.addEventListener('submit', function (e) { e.preventDefault(); });
  form.addEventListener('reset', function () { setTimeout(function () { render(); saveState(); }, 0); });
  render();
})();
