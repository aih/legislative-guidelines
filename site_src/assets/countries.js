// Country / organisation view of the catalog: one panel per country, chosen from a
// grouped, filterable index, with a chip row for its sub-national jurisdictions.
// Routes (URL hash):  #all  A-Z list · #US  country · #US/US-TX  one state · #US/all  every state.
(function () {
  var switcher = document.getElementById('view-switch');
  var viewCountries = document.getElementById('view-countries');
  var viewAz = document.getElementById('view-az');
  if (!switcher || !viewCountries || !viewAz) return;
  var tabs = { countries: document.getElementById('tab-countries'), az: document.getElementById('tab-az') };
  var panels = Array.prototype.slice.call(viewCountries.querySelectorAll('.c-panel'));
  var navLinks = Array.prototype.slice.call(viewCountries.querySelectorAll('#c-nav a[data-code]'));
  var indexBox = document.getElementById('c-index-box');
  var narrow = window.matchMedia('(max-width: 900px)');

  switcher.hidden = false;
  viewCountries.classList.add('js');

  function showView(name) {
    viewCountries.hidden = name !== 'countries';
    viewAz.hidden = name !== 'az';
    Object.keys(tabs).forEach(function (k) {
      tabs[k].setAttribute('aria-selected', k === name ? 'true' : 'false');
      tabs[k].tabIndex = k === name ? 0 : -1;
    });
  }

  function showCountry(code, sub) {
    var panel = code && document.getElementById('c-' + code);
    if (!panel) { panel = document.getElementById('c-overview'); code = null; }
    panels.forEach(function (p) { p.hidden = p !== panel; });
    navLinks.forEach(function (a) {
      if (a.dataset.code === code) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    var subnat = panel.querySelector('.subnat');
    if (subnat) {
      var subPanels = subnat.querySelectorAll('.sub-panel');
      var any = false;
      Array.prototype.forEach.call(subPanels, function (sp) {
        var on = sub === 'all' || sp.dataset.sub === sub;
        sp.hidden = !on;
        any = any || on;
      });
      Array.prototype.forEach.call(subnat.querySelectorAll('.chip'), function (c) {
        if (c.dataset.sub === sub) c.setAttribute('aria-current', 'true');
        else c.removeAttribute('aria-current');
      });
      // A single subdivision is always shown; otherwise prompt for a choice.
      if (subPanels.length === 1) { subPanels[0].hidden = false; any = true; }
      subnat.querySelector('.sub-hint').hidden = any;
    }
    return panel;
  }

  function route(scroll) {
    var h = decodeURIComponent(location.hash.replace(/^#/, ''));
    if (h === 'all' || (h && document.getElementById(h) && viewAz.contains(document.getElementById(h)))) {
      showView('az');
      return;
    }
    if (!h && location.search) { showView('az'); return; }
    showView('countries');
    var parts = h.split('/');
    var panel = showCountry(parts[0], parts[1]);
    if (scroll && h) {
      var target = parts[1] && parts[1] !== 'all' ? document.getElementById('s-' + parts[1]) : null;
      if (parts[1] === 'all') target = panel.querySelector('.subnat');
      if (!target && narrow.matches) target = panel;
      if (target) target.scrollIntoView({ block: 'start' });
    }
  }

  tabs.countries.addEventListener('click', function () {
    var current = navLinks.filter(function (a) { return a.getAttribute('aria-current'); })[0];
    history.pushState(null, '', location.pathname + (current ? '#' + current.dataset.code : '#'));
    route(false);
  });
  tabs.az.addEventListener('click', function () {
    history.pushState(null, '', location.pathname + location.search + '#all');
    route(false);
  });
  switcher.addEventListener('keydown', function (e) {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    var next = document.activeElement === tabs.az ? tabs.countries : tabs.az;
    next.focus();
    next.click();
  });

  window.addEventListener('hashchange', function () { route(true); });
  navLinks.forEach(function (a) {
    a.addEventListener('click', function () {
      if (narrow.matches && indexBox) indexBox.open = false;
    });
  });

  // Filter the country index; regions with no match are hidden, matches open their region.
  var filter = document.getElementById('c-filter');
  var none = document.getElementById('c-none');
  filter.addEventListener('input', function () {
    var q = filter.value.trim().toLowerCase();
    var shown = 0;
    Array.prototype.forEach.call(viewCountries.querySelectorAll('.c-region'), function (region) {
      var n = 0;
      Array.prototype.forEach.call(region.querySelectorAll('li'), function (li) {
        var on = !q || li.dataset.find.indexOf(q) !== -1;
        li.hidden = !on;
        if (on) n++;
      });
      region.hidden = n === 0;
      var badge = region.querySelector('summary .c-count');
      if (!badge.dataset.total) badge.dataset.total = badge.textContent;
      badge.textContent = q ? n : badge.dataset.total;
      if (q && n) region.open = true;
      shown += n;
    });
    none.hidden = shown > 0;
  });
  filter.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    var first = viewCountries.querySelector('#c-nav li:not([hidden]) a');
    if (!first) return;
    // Open the matching state or province directly when the query names one.
    var q = filter.value.trim().toLowerCase();
    var panel = document.getElementById('c-' + first.dataset.code);
    var chips = panel ? panel.querySelectorAll('.sub-chips li[data-find]') : [];
    var hit = Array.prototype.filter.call(chips, function (li) { return q && li.dataset.find.indexOf(q) !== -1; })[0];
    location.hash = hit ? hit.querySelector('a').getAttribute('href') : first.getAttribute('href');
  });

  // Filter a country's subdivision chips.
  Array.prototype.forEach.call(viewCountries.querySelectorAll('.sub-filter'), function (input) {
    var chips = input.closest('.subnat').querySelectorAll('.sub-chips li[data-find]');
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      Array.prototype.forEach.call(chips, function (li) { li.hidden = q && li.dataset.find.indexOf(q) === -1; });
    });
  });

  window.addEventListener('popstate', function () { route(false); });
  route(true);
})();
