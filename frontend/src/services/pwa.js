// PWA Service Management
class PWAService {
  constructor() {
    this.registration = null;
    this.isOnline = navigator.onLine;
    this.setupEventListeners();
  }

  // Initialize PWA features
  async init() {
    if ('serviceWorker' in navigator) {
      try {
        this.registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered successfully');
        
        // Handle updates
        this.registration.addEventListener('updatefound', () => {
          this.handleServiceWorkerUpdate();
        });

        // Check for existing service worker
        if (this.registration.active) {
          console.log('Service Worker is active');
        }

        // Setup push notifications
        await this.setupPushNotifications();
        
        return true;
      } catch (error) {
        console.error('Service Worker registration failed:', error);
        return false;
      }
    } else {
      console.log('Service Worker not supported');
      return false;
    }
  }

  // Setup event listeners
  setupEventListeners() {
    // Online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.handleOnlineStatusChange(true);
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.handleOnlineStatusChange(false);
    });

    // App install prompt
    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault();
      this.handleInstallPrompt(event);
    });

    // App installed
    window.addEventListener('appinstalled', () => {
      console.log('PWA was installed');
      this.trackEvent('pwa_installed');
    });
  }

  // Handle service worker updates
  handleServiceWorkerUpdate() {
    const newWorker = this.registration.installing;
    
    newWorker.addEventListener('statechange', () => {
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        // New version available
        this.showUpdateNotification();
      }
    });
  }

  // Show update notification
  showUpdateNotification() {
    const updateBanner = document.createElement('div');
    updateBanner.className = 'update-banner';
    updateBanner.innerHTML = `
      <div class="update-content">
        <span>A new version of MigrateIQ is available!</span>
        <button id="update-btn" class="update-button">Update Now</button>
        <button id="dismiss-btn" class="dismiss-button">Later</button>
      </div>
    `;
    
    document.body.appendChild(updateBanner);

    // Handle update button click
    document.getElementById('update-btn').addEventListener('click', () => {
      this.applyUpdate();
      updateBanner.remove();
    });

    // Handle dismiss button click
    document.getElementById('dismiss-btn').addEventListener('click', () => {
      updateBanner.remove();
    });
  }

  // Apply service worker update
  applyUpdate() {
    if (this.registration && this.registration.waiting) {
      this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }

  // Handle online/offline status changes
  handleOnlineStatusChange(isOnline) {
    const statusBanner = document.getElementById('connection-status');
    
    if (isOnline) {
      if (statusBanner) {
        statusBanner.remove();
      }
      this.syncOfflineData();
    } else {
      this.showOfflineBanner();
    }
  }

  // Show offline banner
  showOfflineBanner() {
    if (document.getElementById('connection-status')) {
      return; // Banner already exists
    }

    const offlineBanner = document.createElement('div');
    offlineBanner.id = 'connection-status';
    offlineBanner.className = 'offline-banner';
    offlineBanner.innerHTML = `
      <div class="offline-content">
        <span>You're currently offline. Some features may be limited.</span>
      </div>
    `;
    
    document.body.insertBefore(offlineBanner, document.body.firstChild);
  }

  // Sync offline data when back online
  async syncOfflineData() {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        await this.registration.sync.register('background-sync');
        console.log('Background sync registered');
      } catch (error) {
        console.error('Background sync registration failed:', error);
      }
    }
  }

  // Setup push notifications
  async setupPushNotifications() {
    if (!('Notification' in window) || !('PushManager' in window)) {
      console.log('Push notifications not supported');
      return false;
    }

    // Check current permission
    let permission = Notification.permission;
    
    if (permission === 'default') {
      permission = await Notification.requestPermission();
    }

    if (permission === 'granted') {
      try {
        const subscription = await this.registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(process.env.REACT_APP_VAPID_PUBLIC_KEY)
        });

        // Send subscription to server
        await this.sendSubscriptionToServer(subscription);
        return true;
      } catch (error) {
        console.error('Push subscription failed:', error);
        return false;
      }
    }

    return false;
  }

  // Convert VAPID key
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Send subscription to server
  async sendSubscriptionToServer(subscription) {
    try {
      const response = await fetch('/api/notifications/subscribe/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          subscription: subscription.toJSON()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send subscription to server');
      }

      console.log('Push subscription sent to server');
    } catch (error) {
      console.error('Error sending subscription to server:', error);
    }
  }

  // Handle install prompt
  handleInstallPrompt(event) {
    // Store the event for later use
    window.deferredPrompt = event;
    
    // Show custom install button
    this.showInstallButton();
  }

  // Show install button
  showInstallButton() {
    const installButton = document.createElement('button');
    installButton.id = 'install-button';
    installButton.className = 'install-button';
    installButton.textContent = 'Install MigrateIQ';
    installButton.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #1976d2;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      cursor: pointer;
      z-index: 1000;
      font-size: 14px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    `;

    installButton.addEventListener('click', () => {
      this.promptInstall();
    });

    document.body.appendChild(installButton);

    // Auto-hide after 10 seconds
    setTimeout(() => {
      if (installButton.parentNode) {
        installButton.remove();
      }
    }, 10000);
  }

  // Prompt app installation
  async promptInstall() {
    if (window.deferredPrompt) {
      window.deferredPrompt.prompt();
      
      const { outcome } = await window.deferredPrompt.userChoice;
      console.log(`User response to install prompt: ${outcome}`);
      
      this.trackEvent('install_prompt_response', { outcome });
      
      window.deferredPrompt = null;
      
      // Remove install button
      const installButton = document.getElementById('install-button');
      if (installButton) {
        installButton.remove();
      }
    }
  }

  // Check if app is installed
  isInstalled() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }

  // Get installation status
  getInstallationStatus() {
    return {
      isInstalled: this.isInstalled(),
      canInstall: !!window.deferredPrompt,
      isOnline: this.isOnline,
      hasServiceWorker: !!this.registration,
      notificationsEnabled: Notification.permission === 'granted'
    };
  }

  // Track PWA events
  trackEvent(eventName, data = {}) {
    // Send analytics event
    if (window.gtag) {
      window.gtag('event', eventName, {
        event_category: 'PWA',
        ...data
      });
    }
    
    console.log('PWA Event:', eventName, data);
  }

  // Cache important data for offline use
  async cacheImportantData() {
    if (!this.registration) return;

    try {
      // Cache user profile
      await fetch('/api/auth/user/');
      
      // Cache tenant information
      await fetch('/api/core/tenants/current/');
      
      // Cache recent projects
      await fetch('/api/orchestrator/projects/?limit=10');
      
      console.log('Important data cached for offline use');
    } catch (error) {
      console.error('Failed to cache important data:', error);
    }
  }

  // Show notification
  async showNotification(title, options = {}) {
    if (Notification.permission === 'granted' && this.registration) {
      return this.registration.showNotification(title, {
        icon: '/logo192.png',
        badge: '/logo192.png',
        ...options
      });
    }
  }
}

// Create and export PWA service instance
const pwaService = new PWAService();

export default pwaService;
