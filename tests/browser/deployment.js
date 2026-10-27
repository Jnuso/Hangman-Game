async (page) => {
  const checks = [];
  const runtimeErrors = [];
  const onError = error => runtimeErrors.push(error.message);
  const check = (condition, label) => {
    if (!condition) throw new Error(label);
    checks.push(label);
  };
  page.on('pageerror', onError);
  let state;
  const inspect = async data => {
    state = data;
    check(data.status !== 'playing' || !Object.hasOwn(data, 'word'), 'active answer omitted');
    const ui = await page.evaluate(() => ({
      pattern: [...document.querySelectorAll('#word .letter-slot')].map(el => el.textContent.toLowerCase()).join(' '),
      remaining: Number(document.querySelector('#remaining').textContent),
      badge: document.querySelector('#difficulty-badge').textContent,
      parts: document.querySelectorAll('[data-part]:not([hidden])').length,
      buttons: [...document.querySelectorAll('.letter-button')].map(el => ({
        letter: el.dataset.letter, disabled: el.disabled,
        correct: el.classList.contains('correct'), wrong: el.classList.contains('incorrect')
      }))
    }));
    check(ui.pattern === data.pattern && ui.remaining === data.remaining_guesses &&
      ui.badge === data.difficulty.toUpperCase() && ui.parts === data.incorrect_letters.length,
      'page pattern/lives/difficulty/drawing match server');
    check(ui.buttons.every(button => {
      const used = data.guessed_letters.includes(button.letter);
      const wrong = data.incorrect_letters.includes(button.letter);
      return button.disabled === (used || data.status !== 'playing') &&
        button.correct === (used && !wrong) && button.wrong === wrong;
    }), 'all keyboard states match server');
  };
  const action = async (suffix, expected, perform) => {
    const pending = page.waitForResponse(response =>
      response.url().startsWith(new URL(page.url()).origin + '/api/games') &&
      response.url().endsWith(suffix) && response.request().method() === 'POST');
    await perform();
    const response = await pending;
    check(response.status() === expected, 'expected API status ' + expected);
    const data = await response.json();
    await page.waitForFunction(() => !document.querySelector('#new-game').disabled);
    await inspect(data);
  };
  const start = async difficulty => {
    await page.locator('#difficulty').selectOption(difficulty);
    await action('/api/games', 201, () => page.getByRole('button', {name:'New game', exact:true}).click());
    check(state.remaining_guesses === 6 && state.guessed_letters.length === 0, 'fresh game resets state');
  };
  const guess = async (letter, keyboard = false) => {
    await action('/guess', 200, () => keyboard ? page.keyboard.press(letter) :
      page.locator(`[data-letter="${letter}"]`).click());
  };
  try {
    await page.setViewportSize({width:1280,height:1000});
    check(await page.locator('.letter-button:disabled').count() === 26, 'initial controls disabled');
    await start('easy');
    await guess('a');
    await page.screenshot({path:'output/playwright/deployed-desktop-playing.png',fullPage:true});
    let physical = true;
    for (const letter of 'bcdefghijklmnopqrstuvwxyz') {
      if (state.status !== 'playing') break;
      await guess(letter, physical);
      physical = !physical;
    }
    check(['won','lost'].includes(state.status), 'complete game through browser');
    const terminal = {status:state.status,word:state.word};
    check((await page.locator('#message-detail').textContent()).includes(state.word.toUpperCase()), 'terminal answer displayed');
    check(await page.locator('.letter-button:disabled').count() === 26, 'terminal keyboard disabled');
    await page.screenshot({path:'output/playwright/deployed-desktop-finished.png',fullPage:true});
    const oldId = state.game_id;
    await start('medium');
    check(state.game_id !== oldId, 'new game without reload');
    await guess('a', true);
    await start('hard');
    await guess('a');
    await page.setViewportSize({width:375,height:812});
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '375px layout without horizontal overflow');
    check(await page.locator('[data-letter="b"]').evaluate(el => el.getBoundingClientRect().height >= 40), 'mobile letter target at least 40px');
    await page.screenshot({path:'output/playwright/deployed-mobile-playing.png',fullPage:true});
    await page.setViewportSize({width:320,height:740});
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), '320px layout without horizontal overflow');
    await page.setViewportSize({width:1280,height:1000});
    check(runtimeErrors.length === 0, 'no browser runtime errors');
    return {url:page.url(),passed:checks.length,checks,terminal,runtimeErrors,result:'passed'};
  } finally {
    page.off('pageerror', onError);
  }
}
