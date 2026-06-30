// Live date on dashboard
const el = document.getElementById('live-date');
if (el) {
  const update = () => {
    const now = new Date();
    el.textContent = now.toLocaleDateString('en-IN', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  };
  update();
  setInterval(update, 60000);
}

// Auto-dismiss flash messages after 4s
document.querySelectorAll('.flash').forEach(f => {
  setTimeout(() => { f.style.transition = 'opacity .5s'; f.style.opacity = '0'; }, 4000);
});
