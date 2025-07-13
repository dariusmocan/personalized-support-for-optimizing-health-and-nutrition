// Variabilă pentru a reține evenimentul de instalare
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  // Previne afișarea promptului automat
  e.preventDefault();
  // Salvează evenimentul pentru utilizare ulterioară
  deferredPrompt = e;
  // Afișează propriul buton de instalare
  showInstallButton();
});

function showInstallButton() {
  // Verifică dacă avem deja un buton
  if (document.getElementById('install-button')) return;
  
  // Creează butonul de instalare
  const installButton = document.createElement('button');
  installButton.id = 'install-button';
  installButton.textContent = 'Instalează aplicația';
  installButton.className = 'install-button';
  installButton.style = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 10px 15px;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    z-index: 9999;
  `;
  
  // Adaugă eveniment
  installButton.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    // Afișează promptul
    deferredPrompt.prompt();
    // Așteaptă alegerea utilizatorului
    const { outcome } = await deferredPrompt.userChoice;
    // Resetează variabila
    deferredPrompt = null;
    // Ascunde butonul
    installButton.style.display = 'none';
  });
  
  // Adaugă butonul la document
  document.body.appendChild(installButton);
}

// Ascultă evenimentul de instalare completă
window.addEventListener('appinstalled', (evt) => {
  // Ascunde butonul dacă este vizibil
  const installButton = document.getElementById('install-button');
  if (installButton) installButton.style.display = 'none';
  
  // Opțional: salvează un flag în localStorage
  localStorage.setItem('appInstalled', 'true');
  console.log('Aplicația a fost instalată cu succes!');
});