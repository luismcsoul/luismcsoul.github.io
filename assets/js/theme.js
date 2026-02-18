// Edge navigation: swipe on touch devices, arrow keys on desktop
document.addEventListener('DOMContentLoaded', () => {
  // Utility: find edge link by data-edge attribute
  function linkFor(direction){
    return document.querySelector(`.edge[data-edge="${direction}"]`);
  }

  function navigate(direction){
    const a = linkFor(direction);
    if (a && a.getAttribute('href')) {
      window.location = a.getAttribute('href');
    }
  }

  // Utility: show/hide hero popup
  function showHeroMedia(){
    const hero = document.getElementById('mediaHeroPopup');
    if (hero) hero.style.display = 'flex';
  }
  function hideHeroMedia(){
    const hero = document.getElementById('mediaHeroPopup');
    if (hero) hero.style.display = 'none';
  }

  // ----- Swipe detection for mobile / tablets -----
  let startX = 0, startY = 0, endX = 0, endY = 0;
  const thresh = 50; // px threshold for a valid swipe

  document.addEventListener('touchstart', (e) => {
    const t = e.changedTouches[0];
    startX = t.clientX; 
    startY = t.clientY;
  }, {passive: true});

  document.addEventListener('touchend', (e) => {
    const t = e.changedTouches[0];
    endX = t.clientX; 
    endY = t.clientY;
    
    const dx = endX - startX;
    const dy = endY - startY;

    // Horizontal swipes
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > thresh) {
      // Natural Swipe: Swipe finger RIGHT (dx > 0) to go to PREVIOUS (left)
      // Swipe finger LEFT (dx < 0) to go to NEXT (right)
      navigate(dx > 0 ? 'left' : 'right');
    } 
    // Vertical swipes
    else if (Math.abs(dy) > thresh) {
      // Swipe finger DOWN (dy > 0) to go to TOP content
      // Swipe finger UP (dy < 0) to go to BOTTOM content
      navigate(dy > 0 ? 'top' : 'bottom');
    }
  }, {passive: true});

  // ----- Arrow keys + spacebar on desktop -----
  document.addEventListener('keydown', (e) => {
    // Avoid triggering navigation if user is typing in an input field
    if (['input', 'textarea'].includes(document.activeElement.tagName.toLowerCase())) return;

    if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' '].includes(e.key)){
      e.preventDefault(); // Prevent page bumping
      if (e.key === 'ArrowLeft')  navigate('left');
      if (e.key === 'ArrowRight') navigate('right');
      if (e.key === 'ArrowUp')    navigate('top');
      if (e.key === 'ArrowDown')  navigate('bottom');
      if (e.key === ' ')          showHeroMedia();
    }
  });

  document.addEventListener('keyup', (e) => {
    if (e.key === ' ') {
      hideHeroMedia();
    }
  });

  // ----- Central interaction (Tap & Hold to see Hero) -----
  const centralText = document.querySelector('.work-body') || document.querySelector('main');
  if (centralText){
    centralText.addEventListener('touchstart', (e) => {
      // Don't show hero if the user is clicking a link
      if (e.target.tagName !== 'A') showHeroMedia();
    }, {passive: true});
    
    centralText.addEventListener('touchend', () => {
      hideHeroMedia();
    }, {passive: true});
  }

  // ----- Security & UX for Popups -----
  const popupImg = document.querySelector('#mediaHeroPopup img');
  if (popupImg){
    // Prevent right-click/long-press save to protect IP visually
    popupImg.addEventListener('contextmenu', e => e.preventDefault());
    // Prevent dragging the image
    popupImg.addEventListener('dragstart', e => e.preventDefault());
  }
});
