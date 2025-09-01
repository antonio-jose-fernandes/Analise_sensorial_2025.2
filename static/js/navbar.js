function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const toggleButton = document.querySelector('.menu-toggle');
  
    sidebar.classList.toggle('show');
    overlay.style.display = sidebar.classList.contains('show') ? 'block' : 'none';
    toggleButton.setAttribute('aria-expanded', sidebar.classList.contains('show'));
  }
  
  document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const toggleButton = document.querySelector('.menu-toggle');
  
    if (window.innerWidth <= 768 &&
        !sidebar.contains(event.target) &&
        event.target !== toggleButton &&
        !toggleButton.contains(event.target)) {
      sidebar.classList.remove('show');
      overlay.style.display = 'none';
      toggleButton.setAttribute('aria-expanded', 'false');
    }
  });
  
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('overlay');
      const toggleButton = document.querySelector('.menu-toggle');
  
      if (window.innerWidth <= 768 && sidebar.classList.contains('show')) {
        sidebar.classList.remove('show');
        overlay.style.display = 'none';
        toggleButton.setAttribute('aria-expanded', 'false');
      }
    }
  });
  
  window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
      const sidebar = document.getElementById('sidebar');
      const overlay = document.getElementById('overlay');
      const toggleButton = document.querySelector('.menu-toggle');
  
      sidebar.classList.remove('show');
      overlay.style.display = 'none';
      toggleButton.setAttribute('aria-expanded', 'false');
    }
  });