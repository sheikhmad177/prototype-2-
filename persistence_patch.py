"""Targeted persistence and telemetry corrections for the existing prototype."""


def apply(text, replace_once, group='A'):
    text = replace_once(text, '    var telemetry = [];', '''    var STORAGE_KEY = 'soover.prototype1.study.v1';
    var storageWarning = '';
    var participantId = uid() + uid();
    var telemetry = [];''')
    text = replace_once(text, '    function log(s, screen, action, detail){\n      telemetry.push({ t: new Date().toISOString(), group: s.prototype, screen: screen, action: action, detail: detail });\n    }', '''    function saveStudy(){
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({version:1, participantId:participantId,
          telemetry:telemetry, sessions:sessions}));
        storageWarning = '';
      } catch(e) {
        storageWarning = 'Browser storage is unavailable or full. Export CSV before leaving; new events may be lost.';
      }
    }
    function restoreStudy(){
      try {
        var raw = localStorage.getItem(STORAGE_KEY);
        if(!raw) return;
        var data = JSON.parse(raw);
        if(data.version !== 1 || !Array.isArray(data.telemetry) || !data.sessions || !data.participantId)
          throw new Error('Invalid saved study');
        telemetry = data.telemetry;
        sessions = data.sessions;
        participantId = data.participantId;
      } catch(e) {
        storageWarning = 'Saved data could not be read. This page will not overwrite it. Export this session before closing.';
        // Preserve unreadable records rather than silently overwriting them.
        STORAGE_KEY += '.recovery.' + Date.now();
      }
    }
    function log(s, screen, action, detail){
      telemetry.push({ eventId:uid()+uid(), participantId:participantId, sessionId:s.id,
        t: new Date().toISOString(), group:s.prototype, screen:screen, action:action, detail:detail });
      saveStudy();
    }''')
    text = replace_once(text, '    function startNewSession(s){\n      s.screen = 1;', '''    function startNewSession(s){
      s.id = uid() + uid();
      s.completed = false;
      s.screen = 1;''')
    text = replace_once(text, "id: uid(),", "id: uid() + uid(),\n        completed: false,")
    text = replace_once(text, "if(s){ var t = totals(s); log(s,4,'complete_order'", "if(s && s.screen === 4 && !s.completed){ s.completed = true; var t = totals(s); log(s,4,'complete_order'")
    text = replace_once(text, "        case 'clearLog': telemetry.length = 0; render(); break;", "        case 'clearLog': break; // Retention: no destructive clear control.")
    text = replace_once(text, "        + '<button class=\"btn-ghost danger\" data-action=\"clearLog\">Clear Log</button></div></div>'", "        + '</div></div>'")
    text = replace_once(text, "      var comps = telemetry.filter(function(e){ return e.action === 'complete_order'; });", "      var clicks = telemetry.filter(function(e){ return e.action === 'click'; }).length;\n      var comps = telemetry.filter(function(e){ return e.action === 'complete_order'; });")
    text = replace_once(text, "All participant interactions are recorded client-side for this study session. Export the full event stream as CSV for analysis.", "This browser only — saved across refreshes on this device. Not connected to Google Sheets. Export CSV to retain a separate copy; this is not an all-participants dashboard.")
    text = replace_once(text, "        + '<div class=\"cards\">'", "        + '<div class=\"cards\">'\n        + '<div class=\"card\"><div class=\"card-v\">' + clicks + '</div><div class=\"card-l\">Clicks (includes navigation)</div></div>'")
    text = replace_once(text, "var header = ['Timestamp','Group','Screen','Event','Detail'];", "var header = ['Timestamp','Group','Screen','Event','Detail','Event ID','Participant ID','Session ID'];")
    text = replace_once(text, "return [e.t,e.group,e.screen,e.action,e.detail];", "return [e.t,e.group,e.screen,e.action,e.detail,e.eventId,e.participantId,e.sessionId];")
    text = replace_once(text, '      v = String(v);', "      v = String(v == null ? '' : v);\n      if(/^[=+@\\-\\t\\r]/.test(v)) v = \"'\" + v;")
    text = replace_once(text, "      app.innerHTML = blind ? blindLayout() : researcherLayout();", """      var layout = blind ? blindLayout() : researcherLayout();
      saveStudy();
      app.innerHTML = (storageWarning ? '<div role="alert" style="background:#fff0d0;color:#542c00;padding:16px;">' + esc(storageWarning) + '</div>' : '') + layout;""")
    text = replace_once(text, "      var params = new URLSearchParams(window.location.search);", "      restoreStudy();\n      var params = new URLSearchParams(window.location.search);")
    text = replace_once(text, "      document.addEventListener('click', function(e){\n        var a", """      document.addEventListener('click', function(e){
        var session = ensureSession('A');
        var clickedAction = e.target.closest('[data-action]');
        var clickedView = e.target.closest('[data-view]');
        log(session, session.screen, 'click', clickedAction ? clickedAction.dataset.action :
          (clickedView ? 'view:' + clickedView.dataset.view : 'page'));
        var a""")
    text = replace_once(text, "        if(v){ view = v.dataset.view; render(); }", "        if(v){ view = v.dataset.view; render(); }\n        else if(view === 'telemetry') render();")
    text = replace_once(text, "        if(s) s.customer[f.dataset.field] = f.value;", "        if(s){ s.customer[f.dataset.field] = f.value; saveStudy(); }")
    if group == 'B':
        text = replace_once(text, "soover.prototype1.study.v1", "soover.prototype2.study.v1")
        text = replace_once(text, "var session = ensureSession('A');", "var session = ensureSession('B');")
    return text
