/* 4Letters completion bounce module.
 * Independent of crossword data and game state. Call bounceSequence with cell keys
 * in the required reading order (e.g. ["2,3","2,4","2,5","2,6"]).
 * Uses Web Animations API rather than CSS class re-triggering; serializes sequences.
 */
const reducedMotion = () => {
  try { return globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false; }
  catch { return false; }
};
let queue = Promise.resolve();

function animateOne(tile) {
  tile.classList.remove('correct-double-bounce');
  tile.style.animationDelay = '';
  if (reducedMotion()) return Promise.resolve();
  const animation = tile.animate([
    { offset: 0, transform: 'translate3d(0,0,0) scale(1)', boxShadow: '0 1px 0 rgba(1,19,31,.22)' },
    { offset: .18, transform: 'translate3d(0,-10px,0) scale(1.09)', boxShadow: '0 12px 18px rgba(0,0,0,.34)' },
    { offset: .38, transform: 'translate3d(0,0,0) scale(.97)', boxShadow: '0 1px 0 rgba(1,19,31,.22)' },
    { offset: .58, transform: 'translate3d(0,-6px,0) scale(1.05)', boxShadow: '0 7px 12px rgba(0,0,0,.27)' },
    { offset: .78, transform: 'translate3d(0,0,0) scale(1)', boxShadow: '0 1px 0 rgba(1,19,31,.22)' },
    { offset: 1, transform: 'translate3d(0,0,0) scale(1)', boxShadow: '0 1px 0 rgba(1,19,31,.22)' }
  ], { duration: 620, iterations: 2, easing: 'cubic-bezier(.2,.75,.25,1.15)', fill: 'none' });
  return animation.finished.catch(() => {}).then(() => {
    animation.cancel();
    tile.style.transform = '';
    tile.style.boxShadow = '';
  });
}

export function bounceSequence(keys, root = document) {
  const run = async () => {
    for (const key of [...new Set(keys || [])]) {
      const escaped = String(key).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
      const tile = root.querySelector('.cell[data-key="' + escaped + '"]');
      if (!tile || !tile.isConnected) continue;
      await animateOne(tile);
    }
  };
  const current = queue.then(run, run);
  queue = current.catch(() => {});
  return current;
}
