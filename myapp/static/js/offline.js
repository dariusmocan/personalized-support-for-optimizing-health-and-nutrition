document.addEventListener('DOMContentLoaded', function() {
  // Creează banner pentru notificarea stării conexiunii
  const offlineBanner = document.createElement('div');
  offlineBanner.id = 'offline-banner';
  offlineBanner.textContent = 'Ești momentan offline. Unele funcționalități ar putea fi limitate.';
  offlineBanner.style = `
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background-color: #f8d7da;
    color: #721c24;
    text-align: center;
    padding: 10px;
    z-index: 9999;
  `;
  document.body.appendChild(offlineBanner);

  // Funcții pentru actualizarea stării
  function updateOfflineStatus() {
    if (!navigator.onLine) {
      offlineBanner.style.display = 'block';
      document.body.classList.add('offline-mode');
    } else {
      offlineBanner.style.display = 'none';
      document.body.classList.remove('offline-mode');
    }
  }

  // Ascultă evenimentele de conexiune
  window.addEventListener('online', updateOfflineStatus);
  window.addEventListener('offline', updateOfflineStatus);
  
  // Verifică starea inițială
  updateOfflineStatus();
});