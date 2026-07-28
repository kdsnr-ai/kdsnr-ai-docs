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
  var A = R + 'archive.html#';
  var I = R + 'start.html#';
  var DASH = 'https://kdsnr-ai-dashboard.vercel.app';
  el.innerHTML =
    '<a class="brand" href="' + R + 'research/index.html"><span>KDSNR-AI</span><img src="' + R + 'assets/mark.png" alt=""></a>' +
    '<nav>' +
    group(R + 'update.html', '<span class="group-label">Update</span>', false, false) +
    group(R + 'research/index.html', 'Research &amp; Development', false, false) +
    '<a class="group" href="' + DASH + '" target="_blank" rel="noopener">Dashboard</a>' +
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
      { href: P + 'overview', label: '개요' },
      { href: P + 'question', label: 'Question 스키마' },
      { href: P + 'api-usage', label: 'API 사용법' },
      { href: P + 'import-file', label: 'import_file', sub: true },
      { href: P + 'extract-question', label: 'extract_question', sub: true },
      { href: P + 'compose-hwpx', label: 'compose_hwpx', sub: true },
      { href: P + 'hwp-to-pdf', label: 'hwp_to_pdf', sub: true },
      { href: P + 'hwp-to-hwpx', label: 'hwp_to_hwpx', sub: true },
    ]) +
    group(R + 'archive.html', 'Archive', page === 'archive.html', true) +
    items([
      { href: A + 'overview', label: '개요' },
      { href: A + 'schema', label: '반환 스키마' },
      { href: A + 'api-usage', label: 'API 사용법' },
      { href: A + 'search-questions', label: 'search_questions', sub: true },
      { href: A + 'get-question', label: 'get_question', sub: true },
      { href: A + 'find-similar-questions', label: 'find_similar_questions', sub: true },
    ]) +
    '</div>' +
    '<div class="nav-head">MCP</div>' +
    '<div class="nav-tree">' +
    group(R + 'mcp-setup.html', 'Setup', /^mcp-/.test(file), true) +
    items([
      { href: R + 'mcp-setup.html#chatgpt', label: 'ChatGPT' },
      { href: R + 'mcp-setup.html#claude', label: 'Claude' },
      { href: R + 'mcp-setup.html#gemini', label: 'Gemini' },
    ]) +
    '</div>' +
    '</nav>' +
    '<div class="foot">(주)강남대성수능연구소<br>kdsnrai@gmail.com</div>';

  var scrollbar = document.createElement('div');
  scrollbar.className = 'sidebar-scrollbar';
  scrollbar.innerHTML = '<div class="sidebar-scrollbar-thumb"></div>';
  document.body.appendChild(scrollbar);
  var scrollbarThumb = scrollbar.firstChild;

  function syncScrollbar() {
    var viewport = el.clientHeight;
    var total = el.scrollHeight;
    var range = total - viewport;
    if (viewport <= 0 || range <= 0) {
      scrollbar.style.display = 'none';
      return;
    }
    scrollbar.style.display = '';
    var height = Math.max(28, viewport * viewport / total);
    var top = el.scrollTop / range * (viewport - height);
    scrollbarThumb.style.height = height + 'px';
    scrollbarThumb.style.transform = 'translateY(' + top + 'px)';
  }

  el.addEventListener('scroll', syncScrollbar, { passive: true });
  window.addEventListener('resize', syncScrollbar);
  requestAnimationFrame(syncScrollbar);

  el.querySelectorAll('.group .chev').forEach(function (ch) {
    ch.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      ch.closest('.group').classList.toggle('open');
      requestAnimationFrame(syncScrollbar);
    });
  });

  var NEW_DAYS = 2;

  function dateFromId(id) {
    var m = /^v(\d{4})(\d{2})(\d{2})$/.exec(id || '');
    return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
  }

  function markNew(d) {
    if (!d || Date.now() >= d.getTime() + NEW_DAYS * 86400000) return;
    var label = el.querySelector('a[href$="update.html"] .group-label');
    if (label) label.insertAdjacentHTML('beforeend', '<span class="nav-new">NEW</span>');
  }

  fetch(R + 'update.html', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.text() : ''; })
    .then(function (html) {
      var m = html.match(/<h2[^>]*class="part"[^>]*id="(v\d{8})"/);
      markNew(m ? dateFromId(m[1]) : null);
    })
    .catch(function () {});
})();
