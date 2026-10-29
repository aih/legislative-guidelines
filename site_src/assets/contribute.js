(function () {
  var form = document.getElementById('contribute');
  var status = document.getElementById('c-status');
  var endpoint = form.dataset.endpoint;
  var repo = form.dataset.repo;

  function value(name) { return (form.elements[name].value || '').trim(); }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;
    var data = {
      jurisdiction: value('jurisdiction'), title: value('title'), issuing_body: value('issuing_body'),
      url: value('url'), edition: value('edition'), language: value('language'), kind: value('kind'),
      notes: value('notes'), name: value('name'), email: value('email')
    };

    if (endpoint) {
      status.textContent = 'Sending…';
      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(data)
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        status.textContent = 'Thank you. Your submission has been sent.';
      }).catch(function () {
        status.textContent = 'Sending failed. Please try again later.';
      });
      return;
    }

    var body = [
      '**Jurisdiction / organisation:** ' + data.jurisdiction,
      '**Title:** ' + data.title,
      '**Issuing body:** ' + (data.issuing_body || '—'),
      '**Link:** ' + data.url,
      '**Edition / date:** ' + (data.edition || '—'),
      '**Language(s):** ' + (data.language || '—'),
      '**Submission type:** ' + data.kind,
      '',
      '**Notes:**',
      data.notes || '—',
      '',
      data.name ? '_Submitted by ' + data.name + '_' : ''
    ].join('\n');
    var url = 'https://github.com/' + repo + '/issues/new?' + new URLSearchParams({
      title: 'Guideline submission: ' + data.title + ' (' + data.jurisdiction + ')',
      body: body,
      labels: 'submission'
    }).toString();
    window.open(url, '_blank', 'noopener');
    status.textContent = 'A pre-filled GitHub issue has opened in a new tab. Submit it there to send your suggestion.';
  });
})();
