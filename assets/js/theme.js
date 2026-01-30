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
