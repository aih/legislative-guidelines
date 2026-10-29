(function () {
  var rows = Array.prototype.slice.call(document.querySelectorAll('#catalog tbody tr'));
  var f = {
    text: document.getElementById('f-text'),
    level: document.getElementById('f-level'),
    region: document.getElementById('f-region'),
    lang: document.getElementById('f-lang'),
    status: document.getElementById('f-status')
  };
  var count = document.getElementById('f-count');

  function apply() {
    var q = f.text.value.trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (r) {
      var ok = (!q || r.dataset.text.indexOf(q) !== -1) &&
        (!f.level.value || r.dataset.level === f.level.value) &&
        (!f.region.value || r.dataset.region === f.region.value) &&
        (!f.lang.value || r.dataset.langs.split('|').indexOf(f.lang.value) !== -1) &&
        (!f.status.value || r.dataset.status === f.status.value);
      r.hidden = !ok;
      if (ok) shown++;
    });
    count.textContent = shown + ' of ' + rows.length + ' guidelines';
  }
  Object.keys(f).forEach(function (k) { f[k].addEventListener('input', apply); });
  document.getElementById('filters').addEventListener('submit', function (e) { e.preventDefault(); });
  apply();
})();
