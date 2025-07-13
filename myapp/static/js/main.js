document.addEventListener('DOMContentLoaded', function() {
  console.log('Aplicația Nutrition Planner s-a încărcat.');
  
  // Verifică dacă aplicația este instalată ca PWA
  const isInStandaloneMode = window.matchMedia('(display-mode: standalone)').matches || 
                            window.navigator.standalone || 
                            document.referrer.includes('android-app://');
  
  if (isInStandaloneMode) {
    console.log('Aplicația rulează ca PWA instalată');
  }
  
  // Inițializează funcționalități interactive aici
  initializeInteractiveElements();
});

function initializeInteractiveElements() {
  // Aici poți adăuga inițializări pentru butoanele și interacțiunile din UI
  const buttons = document.querySelectorAll('.action-button');
  if (buttons) {
    buttons.forEach(button => {
      button.addEventListener('click', function(e) {
        const action = this.getAttribute('data-action');
        if (action === 'generate-plan') {
          console.log('Generare plan alimentar...');
        } else if (action === 'save-meal') {
          console.log('Salvare masă...');
        }
        // etc.
      });
    });
  }
}