// Edge navigation: swipe on touch devices, arrow keys on desktop
document.addEventListener('DOMContentLoaded', () => {
  // Utility: find edge link by data-edge
  function linkFor(direction){
    return document.querySelector(`.edge[data-edge="${direction}"]`);
  }
  function navigate(direction){
    const a = linkFor(direction);
    if (a && a.getAttribute('href')) window.location = a.getAttribute('href');
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
  const thresh = 48; // px threshold

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

  // ----- Arrow keys + spacebar on desktop -----
  document.addEventListener('keydown', (e) => {
    if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' '].includes(e.key)){
      e.preventDefault();
      if (e.key==='ArrowLeft')  navigate('left');
      if (e.key==='ArrowRight') navigate('right');
      if (e.key==='ArrowUp')    navigate('top');
      if (e.key==='ArrowDown')  navigate('bottom');
      if (e.key===' ')          showHeroMedia();
    }
  });
  document.addEventListener('keyup', (e) => {
    if (e.key===' '){
      hideHeroMedia();
    }
  });

  // ----- Press central text on mobile -----
  const centralText = document.querySelector('.work-body'); // your main text container
  if (centralText){
    centralText.addEventListener('touchstart', () => {
      showHeroMedia();
    }, {passive:true});
    centralText.addEventListener('touchend', () => {
      hideHeroMedia();
    }, {passive:true});
  }
});
