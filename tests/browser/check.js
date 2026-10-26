async (page) => {
  const checks = [];
  const runtimeErrors = [];
  const apiChecks = [];
  const guesses = [];
  page.on('pageerror', (error) => runtimeErrors.push(error.message));
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().endsWith('/guess')) guesses.push(request.postDataJSON());
  });
  page.on('response', (response) => {
    if (response.url().includes('/api/games') && [200,201].includes(response.status())) {
      apiChecks.push(response.json().then((data) => {
        if (data.status === 'playing' && Object.hasOwn(data, 'word')) throw new Error('Active answer exposed');
      }));
    }
  });
  const check = (condition, label) => { if (!condition) throw new Error(label); checks.push(label); };
  const idle = () => page.waitForFunction(() => !document.querySelector('#new-game').disabled);
  const start = async (level = 'easy') => {
    await page.locator('#difficulty').selectOption(level);
    await page.locator('#new-game').click();
    await idle();
    check(await page.locator('#difficulty-badge').textContent() === level.toUpperCase(), `${level} game starts`);
  };
  const guess = async (letter, physical = false) => {
    if (physical) await page.keyboard.press(letter);
    else await page.locator(`[data-letter="${letter}"]`).click();
    await idle();
  };

  await page.goto('http://127.0.0.1:5055');
  await page.setViewportSize({width:1280, height:1000});
  check(await page.locator('.letter-button:disabled').count() === 26, 'letters disabled before starting');
  await start();
  await guess('p');
  check(await page.locator('#word').getAttribute('aria-label') === 'Word: blank, P, P, blank, blank', 'click reveals repeated letters');
  check(await page.locator('#remaining').textContent() === '6', 'correct guess preserves lives');
  await guess('z', true);
  check(await page.locator('#remaining').textContent() === '5', 'physical keyboard sends incorrect guess');
  check(await page.locator('[data-part]:not([hidden])').count() === 1, 'first miss reveals one drawing part');
  const countBeforeDuplicate = guesses.length;
  await page.keyboard.press('z');
  await page.keyboard.press('1');
  check(guesses.length === countBeforeDuplicate, 'duplicate and invalid keys do not send requests');
  await page.screenshot({path:'output/playwright/desktop-playing.png',fullPage:true});
  for (const letter of ['a','l','e']) await guess(letter, true);
  check((await page.locator('#message-title').textContent()).includes('You found it'), 'full browser win');
  check((await page.locator('#message-detail').textContent()).includes('APPLE'), 'winning answer displayed');
  check(await page.locator('.letter-button:disabled').count() === 26, 'letters disabled after winning');
  await start();
  check(await page.locator('#remaining').textContent() === '6', 'new game resets lives without reload');
  check(await page.locator('[data-part]:not([hidden])').count() === 0, 'new game resets drawing');
  for (const letter of 'bcdfgh') await guess(letter);
  check((await page.locator('#message-title').textContent()).includes('Out of chances'), 'full browser loss');
  check(await page.locator('[data-part]:not([hidden])').count() === 6, 'six misses reveal full drawing');
  check(await page.locator('.letter-button:disabled').count() === 26, 'letters disabled after losing');
  await start('medium');
  for (const letter of 'guitar') await guess(letter);
  check((await page.locator('#message-detail').textContent()).includes('GUITAR'), 'medium game completes');
  await start('hard');
  for (const letter of 'rhytm') await guess(letter);
  check((await page.locator('#message-detail').textContent()).includes('RHYTHM'), 'hard game completes');

  await start();
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  let arrived;
  const seen = new Promise((resolve) => { arrived = resolve; });
  const delayGuess = async (route) => { arrived(); await gate; await route.continue(); };
  await page.route('**/api/games/*/guess', delayGuess);
  const countBeforePending = guesses.length;
  await page.locator('[data-letter="p"]').click();
  await seen;
  check(await page.locator('#new-game').isDisabled(), 'new game disabled while guess pending');
  check(await page.locator('#difficulty').isDisabled(), 'difficulty disabled while pending');
  check(await page.locator('.letter-button:disabled').count() === 26, 'letters disabled while pending');
  await page.keyboard.press('z');
  release();
  await idle();
  await page.unroute('**/api/games/*/guess', delayGuess);
  check(guesses.length === countBeforePending + 1, 'overlapping keyboard input prevented');

  // Simulate a lost response AFTER the server has accepted the guess.
  const lostResponse = async (route) => { await route.fetch(); await route.abort('failed'); };
  await page.route('**/api/games/*/guess', lostResponse);
  await guess('z');
  check(await page.locator('#sync-game').isVisible(), 'uncertain response offers sync');
  check(await page.locator('.letter-button:disabled').count() === 26, 'uncertain state blocks further guesses');
  await page.unroute('**/api/games/*/guess', lostResponse);
  await page.locator('#sync-game').click();
  await idle();
  check(await page.locator('#remaining').textContent() === '5', 'sync recovers accepted guess without retrying it');
  check(await page.locator('[data-letter="z"]').isDisabled(), 'synced guess is marked used');
  check(await page.locator('#sync-game').isHidden(), 'sync recovery restores normal controls');

  const missingGame = async (route) => route.fulfill({status:404, contentType:'application/json', body:JSON.stringify({error:{code:'not_found',message:'Game not found.'}})});
  await page.route('**/api/games/*/guess', missingGame);
  await guess('b');
  check((await page.locator('#message-title').textContent()).includes('no longer available'), 'expired game explains restart');
  check(await page.locator('.letter-button:disabled').count() === 26, 'expired game blocks guesses');
  await page.unroute('**/api/games/*/guess', missingGame);
  await start();

  const offlineCreate = async (route) => route.abort('failed');
  await page.route('**/api/games', offlineCreate);
  await page.locator('#new-game').click();
  await idle();
  check((await page.locator('#message-title').textContent()).includes("Couldn't reach"), 'new-game network error shown');
  await page.unroute('**/api/games', offlineCreate);
  await start();

  await page.locator('#difficulty').focus();
  const beforeFocus = guesses.length;
  await page.keyboard.press('h');
  check(guesses.length === beforeFocus, 'typing in difficulty selector does not guess');
  await page.locator('#new-game').focus();
  await page.keyboard.press('Enter');
  await idle();
  check(await page.locator('#difficulty-badge').textContent() === 'HARD', 'new game starts through keyboard activation');

  await page.setViewportSize({width:375,height:812});
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '375px mobile has no horizontal overflow');
  check(await page.locator('[data-letter="a"]').evaluate((el) => el.getBoundingClientRect().height >= 40), 'mobile letter buttons have usable height');
  await page.screenshot({path:'output/playwright/mobile-playing.png',fullPage:true});
  await page.setViewportSize({width:320,height:740});
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '320px layout has no horizontal overflow');
  await page.setViewportSize({width:1280,height:1000});
  await page.emulateMedia({reducedMotion:'reduce'});
  check(await page.locator('#new-game').isVisible(), 'reduced-motion presentation remains usable');
  await Promise.all(apiChecks);
  check(runtimeErrors.length === 0, 'no browser JavaScript runtime errors');
  check(apiChecks.length > 20, 'active API responses inspected for answer omission');
  return {passed:checks.length,checks,apiResponsesInspected:apiChecks.length,guessRequests:guesses.length,runtimeErrors};
}
