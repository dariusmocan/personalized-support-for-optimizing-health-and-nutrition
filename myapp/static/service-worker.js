const CACHE_NAME = 'nutrition-app-v1';
const API_CACHE_NAME = 'api-cache-v1';

// Static resources that will always be available offline
const urlsToCache = [
  '/',
  '/static/css/base.css',
  '/static/js/main.js',
  '/static/js/offline.js',
  '/static/js/install-prompt.js',
  '/static/images/icon-192x192.png',
  '/static/images/icon-512x512.png',
  '/offline/',  // Page for when user is offline

];

// List of API URLs that will be cached separately
const API_URLS = [
  '/api/user-profile/',
  '/api/meal-plan/',
  '/api/food-database/',
  '/api/journal-entries/'
];

// Service Worker installation
self.addEventListener('install', event => {
  // Skip waiting forces immediate activation
  self.skipWaiting();
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache opened for static resources');
        
        // More robust caching that doesn't fail if a single resource fails
        return Promise.all(
          urlsToCache.map(url => {
            return cache.add(url).catch(error => {
              console.error(`Could not add to cache: ${url}`, error);
              // Continue with other resources even if one fails
            });
          })
        );
      })
  );
});

// Activation and cleanup of old caches
self.addEventListener('activate', event => {
  // Take immediate control of all pages in scope
  event.waitUntil(clients.claim());
  
  // List of caches that should be kept
  const cacheWhitelist = [CACHE_NAME, API_CACHE_NAME];
  
  // Delete old caches
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Network request handling
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Different strategies for APIs vs static resources
  if (API_URLS.some(apiUrl => url.pathname.startsWith(apiUrl))) {
    // Strategy for APIs: Network first, then cache
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache the API response for offline use
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(API_CACHE_NAME).then(cache => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // In case of error, try to return from cache
          return caches.match(event.request)
            .then(cachedResponse => {
              // If we have it in cache, return it, otherwise show offline message
              if (cachedResponse) {
                return cachedResponse;
              }
              
              // If it's an API we don't have cached, return a standard offline response
              return new Response(JSON.stringify({
                error: 'You are offline. This action requires an internet connection.'
              }), {
                headers: { 'Content-Type': 'application/json' }
              });
            });
        })
    );
  } 
  // For requests to the main route, ensure it works offline
  else if (url.pathname === '/' || url.pathname === '/index.html') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache the main page
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Return from cache or offline page
          return caches.match(event.request)
            .then(cachedResponse => {
              return cachedResponse || caches.match('/offline/');
            });
        })
    );
  }
  // For other resources (CSS, JS, images)
  else {
    event.respondWith(
      // Try cache first, then network
      caches.match(event.request)
        .then(cachedResponse => {
          if (cachedResponse) {
            // If it's in cache, return directly
            return cachedResponse;
          }
          
          // Otherwise, try to get from network
          return fetch(event.request)
            .then(response => {
              // Cache for future use
              if (response && response.status === 200) {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                  cache.put(event.request, responseClone);
                });
              }
              return response;
            })
            .catch(error => {
              // Check if it's a request for an image and return a placeholder image
              if (event.request.url.match(/\.(jpg|jpeg|png|gif|svg)$/)) {
                return caches.match('/static/images/offline-placeholder.png');
              }
              throw error;
            });
        })
    );
  }
});

// Background sync support
self.addEventListener('sync', event => {
  if (event.tag === 'sync-journal-entries') {
    event.waitUntil(syncJournalEntries());
  } else if (event.tag === 'sync-meal-plan-updates') {
    event.waitUntil(syncMealPlanUpdates());
  }
});

// Food journal synchronization
async function syncJournalEntries() {
  try {
    // Get data saved locally in indexedDB
    const db = await openDB('nutritionAppDB', 1, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('pendingJournalEntries')) {
          db.createObjectStore('pendingJournalEntries', { keyPath: 'id', autoIncrement: true });
        }
      }
    });
    
    // Get pending entries
    const tx = db.transaction('pendingJournalEntries', 'readonly');
    const store = tx.objectStore('pendingJournalEntries');
    const pendingEntries = await store.getAll();
    
    // If we have nothing to sync, exit
    if (!pendingEntries || pendingEntries.length === 0) {
      return;
    }
    
    console.log(`Syncing ${pendingEntries.length} journal entries`);
    
    // Try to sync each entry
    for (const entry of pendingEntries) {
      try {
        const response = await fetch('/api/add-food-to-journal/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': entry.csrfToken
          },
          body: JSON.stringify(entry.data)
        });
        
        if (response.ok) {
          // Delete the synced entry
          const deleteTx = db.transaction('pendingJournalEntries', 'readwrite');
          const deleteStore = deleteTx.objectStore('pendingJournalEntries');
          await deleteStore.delete(entry.id);
          console.log(`Journal entry synced and deleted: ID ${entry.id}`);
        } else {
          console.error(`Error syncing entry: ${await response.text()}`);
        }
      } catch (error) {
        console.error('Error syncing journal entry:', error);
      }
    }
  } catch (error) {
    console.error('Error accessing local database:', error);
  }
}

// Meal plan updates synchronization
async function syncMealPlanUpdates() {
  try {
    // Similar logic for meal plan synchronization
    const db = await openDB('nutritionAppDB', 1);
    const tx = db.transaction('pendingMealPlanUpdates', 'readonly');
    const store = tx.objectStore('pendingMealPlanUpdates');
    const pendingUpdates = await store.getAll();
    
    for (const update of pendingUpdates) {
      try {
        const response = await fetch('/api/update-meal-plan/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': update.csrfToken
          },
          body: JSON.stringify(update.data)
        });
        
        if (response.ok) {
          const deleteTx = db.transaction('pendingMealPlanUpdates', 'readwrite');
          const deleteStore = deleteTx.objectStore('pendingMealPlanUpdates');
          await deleteStore.delete(update.id);
        }
      } catch (error) {
        console.error('Error syncing meal plan update:', error);
      }
    }
  } catch (error) {
    console.error('Error accessing local database for meal plan:', error);
  }
}

// Helper for indexedDB management
async function openDB(name, version, upgradeCallback) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, version);
    
    if (upgradeCallback) {
      request.onupgradeneeded = e => upgradeCallback(e.target.result);
    }
    
    request.onsuccess = e => resolve(e.target.result);
    request.onerror = e => reject(e.target.error);
  });
}

// Handle push notifications
self.addEventListener('push', event => {
  if (!event.data) return;
  
  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/icon-512x512.png',
    data: data.url ? { url: data.url } : {}
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Nutrition Planner', options)
  );
});

// Handle notification click
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  // Open the specified URL or the main page
  const urlToOpen = event.notification.data && event.notification.data.url
    ? event.notification.data.url
    : '/';
    
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(windowClients => {
      // Check if there's already an open window and navigate to URL
      for (const client of windowClients) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      // Otherwise open a new window
      return clients.openWindow(urlToOpen);
    })
  );
});