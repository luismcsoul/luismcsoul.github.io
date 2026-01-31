(function(){
  const btn = document.getElementById('centerToggle');
  if(!btn) return;

  const toggle = () => {
    const exp = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', String(!exp));
    document.body.classList.toggle('reveal', !exp);
  };

  btn.addEventListener('click', toggle);
  btn.addEventListener('keydown', (e) => {
    if(e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    if(e.key === 'Escape') { document.body.classList.remove('reveal'); btn.setAttribute('aria-expanded','false'); }
  });

  // Close on outside click (mobile)
  document.addEventListener('click', (e) => {
    if(!document.body.classList.contains('reveal')) return;
    const inside = e.target.closest('#centerToggle, #branches');
    if(!inside){ document.body.classList.remove('reveal'); btn.setAttribute('aria-expanded','false'); }
  });
})();

// Enable tap-to-reveal on mobile
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById('centerToggle');
  if (!toggle) return;

  toggle.addEventListener('click', () => {
    document.body.classList.toggle('reveal');
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const phrase = document.getElementById('centerToggle');
  const orb = document.getElementById('navOrb');

  function toggleReveal() {
    body.classList.toggle('reveal');
    const expanded = body.classList.contains('reveal');
    if (phrase) phrase.setAttribute('aria-expanded', String(expanded));
    if (orb) orb.setAttribute('aria-expanded', String(expanded));
  }

  // Tap/click toggles
  if (phrase) phrase.addEventListener('click', toggleReveal);
  if (orb)    orb.addEventListener('click', toggleReveal);

  // ESC closes
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      body.classList.remove('reveal');
      if (phrase) phrase.setAttribute('aria-expanded', 'false');
      if (orb)    orb.setAttribute('aria-expanded', 'false');
    }
    // Optional: press 'o' to open/close
    if (e.key.toLowerCase() === 'o') toggleReveal();
  });
});


document.addEventListener('DOMContentLoaded', () => {
  // ----- Swipe detection for mobile / tablets -----
  let startX = 0, startY = 0, endX = 0, endY = 0;
  const thresh = 48; // minimum px to consider a swipe

  function linkFor(direction){
    return document.querySelector(`.edge[data-edge="${direction}"]`);
  }

  function navigate(direction){
    const a = linkFor(direction);
    if (a && a.getAttribute('href')) window.location = a.getAttribute('href');
  }

  document.addEventListener('touchstart', (e) => {
    const t = e.changedTouches[0];
    startX = t.clientX; startY = t.clientY;
  }, {passive:true});

  document.addEventListener('touchend', (e) => {
    const t = e.changedTouches[0];
    endX = t.clientX; endY = t.clientY;
    const dx = endX - startX, dy = endY - startY;
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > thresh){
      navigate(dx > 0 ? 'right' : 'left');
    } else if (Math.abs(dy) > thresh){
      navigate(dy > 0 ? 'bottom' : 'top');
    }
  }, {passive:true});

  // ----- Optional: arrow keys as a convenience on desktop -----
  document.addEventListener('keydown', (e) => {
    if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){
      e.preventDefault();
      if (e.key==='ArrowLeft')  navigate('left');
      if (e.key==='ArrowRight') navigate('right');
      if (e.key==='ArrowUp')    navigate('top');
      if (e.key==='ArrowDown')  navigate('bottom');
    }
  });
});
