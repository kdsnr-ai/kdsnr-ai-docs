(function () {
  var el = document.getElementById('sidebar');
  if (!el) return;
  var inSub = /\/research\//.test(location.pathname);
  var R = inSub ? '../' : '';
  var file = location.pathname.split('/').pop() || 'index.html';
  var page = (inSub ? 'research/' : '') + file;

  function group(href, label, open, hasChildren) {
    return '<a class="group' + (open ? ' open' : '') + '" href="' + href + '">' + label +
      (hasChildren ? '<span class="chev"></span>' : '') + '</a>';
  }
  function items(list) {
    return '<ul>' + list.map(function (it) {
      return '<li' + (it.sub ? ' class="sub"' : '') + '><a href="' + it.href + '">' + it.label + '</a></li>';
    }).join('') + '</ul>';
  }

  var P = R + 'pipeline.html#';
  var I = R + 'start.html#';
  el.innerHTML =
    '<a class="brand" href="' + R + 'research/index.html"><span>KDSNR-AI</span><img src="' + R + 'assets/mark.png" alt=""></a>' +
    '<nav>' +
    group(R + 'research/index.html', 'Research', false, false) +
    '<div class="nav-head">API Docs</div>' +
    '<div class="nav-tree">' +
    group(R + 'start.html', 'Installation &amp; Start', page === 'start.html', true) +
    items([
      { href: I + 'install', label: '설치' },
      { href: I + 'api-key', label: 'API Key 발급' },
      { href: I + 'client', label: 'Client' },
    ]) +
    group(R + 'pipeline.html', 'Pipeline', page === 'pipeline.html', true) +
    items([
      { href: P + 'demo', label: '소개' },
      { href: P + 'overview', label: '개요' },
      { href: P + 'question', label: 'Question 스키마' },
      { href: P + 'api-usage', label: 'API 사용법' },
      { href: P + 'import-file', label: 'import_file', sub: true },
      { href: P + 'extract-question', label: 'extract_question', sub: true },
      { href: P + 'export-preview', label: 'export_preview', sub: true },
      { href: P + 'compose-hwpx', label: 'compose_hwpx', sub: true },
      { href: P + 'hwp-to-pdf', label: 'hwp_to_pdf', sub: true },
      { href: P + 'hwp-to-hwpx', label: 'hwp_to_hwpx', sub: true },
    ]) +
    '</div>' +
    '</nav>' +
    '<div class="foot">(주)강남대성수능연구소<br>kdsnrai@gmail.com</div>';

  el.querySelectorAll('.group .chev').forEach(function (ch) {
    ch.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      ch.closest('.group').classList.toggle('open');
    });
  });
})();
