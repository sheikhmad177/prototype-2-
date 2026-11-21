// Dependency-free execution checks for the extracted, original browser scripts.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

for (const [number, group] of [[1, 'A'], [2, 'B']]) {
  for (const removeGift of [false, true]) {
    const html = fs.readFileSync(number === 1 ? 'index.html' : 'prototype_2.html', 'utf8');
    assert(!html.includes('data-arena-'));
    assert(!html.includes('https://'));
    const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
    assert.equal(scripts.length, 1);
    const app = {innerHTML: ''};
    const listeners = {};
    const timers = [];
    const document = {
      readyState: 'complete',
      getElementById: id => id === 'app' ? app : null,
      addEventListener: (type, fn) => {listeners[type] = fn;}
    };
    // Deliberately request the opposite group; each file must remain isolated.
    const stored = new Map();
    const localStorage = {getItem: key => stored.get(key) ?? null,
      setItem: (key, value) => stored.set(key, value)};
    const context = {document, localStorage, window: {location: {search: `?group=${group === 'A' ? 'B' : 'A'}`}},
      URLSearchParams, setInterval: fn => timers.push(fn)};
    vm.runInNewContext(scripts[0][1], context);
    const session = {dataset: {session: group}};
    function clickAction(action) {
      const el = {dataset: {action}, closest: selector => selector === '[data-session]' ? session : null};
      listeners.click({target: {closest: selector => selector === '[data-action]' ? el : null}});
    }
    function clickView(view) {
      const el = {dataset: {view}};
      listeners.click({target: {closest: selector => selector === '[data-view]' ? el : null}});
    }
    assert(app.innerHTML.includes(`data-session="${group}"`));
    assert.equal(app.innerHTML.includes('urgency-banner'), group === 'B');
    clickAction('addToCart');
    assert(app.innerHTML.includes('Your Cart'));
    assert.equal(app.innerHTML.includes('checkbox checked'), group === 'B');
    assert.equal(app.innerHTML.includes('Calculated at next step'), group === 'B');
    if (group === 'B') {
      assert(app.innerHTML.includes('addon muted'));
      assert(app.innerHTML.includes('৳200'));
    }
    if (removeGift) clickAction('toggleGiftBox');
    clickAction('proceedCheckout');
    assert(app.innerHTML.includes('Delivery Information'));
    const field = {dataset: {field: 'name'}, value: 'Test <Customer>', closest: () => session};
    listeners.input({target: {closest: () => field}});
    clickAction('continuePayment');
    assert(app.innerHTML.includes('Payment &amp; Review'));
    assert.equal(app.innerHTML.includes('Service Charge'), group === 'B');
    const expected = 120 + 50 + (group === 'B' ? 25 : 0) + ((group === 'B') !== removeGift ? 80 : 0);
    clickAction('completeOrder');
    assert(app.innerHTML.includes(`Total Paid: <b>৳${expected}</b>`));
    assert(app.innerHTML.includes('Test &lt;Customer&gt;'));
    let saved = JSON.parse(stored.get(`soover.prototype${number}.study.v1`));
    assert.equal(saved.telemetry.filter(e => e.action === 'complete_order').length, 1);
    assert.equal(saved.telemetry.filter(e => e.action === 'click').length, removeGift ? 5 : 4);
    const participant = saved.participantId;
    const firstSession = saved.sessions[group].id;
    const eventCount = saved.telemetry.length;
    // Re-execute the original script as a page refresh, keeping only localStorage.
    vm.runInNewContext(scripts[0][1], context);
    assert(app.innerHTML.includes('Order Confirmed!'));
    saved = JSON.parse(stored.get(`soover.prototype${number}.study.v1`));
    assert.equal(saved.telemetry.length, eventCount);
    assert.equal(saved.participantId, participant);
    clickAction('completeOrder'); // Duplicate completion must not create a second order.
    clickView('telemetry');
    saved = JSON.parse(stored.get(`soover.prototype${number}.study.v1`));
    assert.equal(saved.telemetry.filter(e => e.action === 'complete_order').length, 1);
    assert.equal(saved.telemetry.filter(e => e.action === 'click').length, removeGift ? 7 : 6);
    assert(app.innerHTML.includes('Clicks (includes navigation)'));
    assert(app.innerHTML.includes('complete_order'));
    assert(app.innerHTML.includes(`<div class="card-v">৳${expected}</div>`));
    clickView(group);
    clickAction('startNewSession');
    assert(app.innerHTML.includes('Add to Cart'));
    saved = JSON.parse(stored.get(`soover.prototype${number}.study.v1`));
    assert.notEqual(saved.sessions[group].id, firstSession);
    assert.equal(saved.telemetry.filter(e => e.action === 'complete_order').length, 1);
    clickAction('toggleInspector');
    assert(!app.innerHTML.includes('class="toolbar"'));
    assert(!app.innerHTML.includes('dp-callout'));
    timers.forEach(fn => fn());
    clickAction('exitBlind');
    assert(app.innerHTML.includes('class="toolbar"'));
    context.localStorage = {getItem: () => null, setItem: () => {throw new Error('Quota exceeded');}};
    vm.runInNewContext(scripts[0][1], context);
    assert(app.innerHTML.includes('Browser storage is unavailable or full'));
    console.log(`PASS prototype ${number}: checkout ৳${expected}, exact clicks, order counts, refresh persistence, stable IDs, duplicate guard, retained history, storage warning`);
  }
}
