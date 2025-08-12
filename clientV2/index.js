 // Application State Management
 class AppState {
    constructor() {
        this.currentScreen = 'contacts';
        this.currentContact = null;
        this.isInCall = false;
        this.callStartTime = null;
        this.callTimer = null;
        this.isMuted = false;
        this.isSpeakerOn = false;
        this.theme = 'light';
        this.messages = new Map(); // contactId -> messages array
        this.init();
    }

    init() {
        this.loadTheme();
        this.initializeMessages();
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('chatcall-theme') || 'light';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('chatcall-theme', theme);
        
        const themeIcon = document.querySelector('#themeToggle i');
        themeIcon.className = theme === 'light' ? 'bi bi-moon' : 'bi bi-sun';
    }

    initializeMessages() {
        // Initialize with some dummy messages for each contact
        CONTACTS.forEach(contact => {
            this.messages.set(contact.id, [
                {
                    id: 1,
                    text: `Hey! This is ${contact.name}`,
                    sent: false,
                    timestamp: new Date(Date.now() - 3600000)
                },
                {
                    id: 2,
                    text: "Hello! Nice to hear from you.",
                    sent: true,
                    timestamp: new Date(Date.now() - 3300000)
                }
            ]);
        });
    }

    addMessage(contactId, text, sent = true) {
        if (!this.messages.has(contactId)) {
            this.messages.set(contactId, []);
        }
        
        const messages = this.messages.get(contactId);
        const newMessage = {
            id: Date.now(),
            text,
            sent,
            timestamp: new Date()
        };
        
        messages.push(newMessage);
        return newMessage;
    }

    getMessages(contactId) {
        return this.messages.get(contactId) || [];
    }
}

// Dummy Data
const CONTACTS = [
    {
        id: 1,
        name: "Alice Johnson",
        status: "online",
        avatar: "AJ",
        lastSeen: "Active now"
    },
    {
        id: 2,
        name: "Bob Smith",
        status: "offline",
        avatar: "BS",
        lastSeen: "Last seen 2 hours ago"
    },
    {
        id: 3,
        name: "Carol Williams",
        status: "busy",
        avatar: "CW",
        lastSeen: "Busy"
    },
    {
        id: 4,
        name: "David Brown",
        status: "online",
        avatar: "DB",
        lastSeen: "Active now"
    },
    {
        id: 5,
        name: "Emma Davis",
        status: "offline",
        avatar: "ED",
        lastSeen: "Last seen yesterday"
    },
    {
        id: 6,
        name: "Frank Miller",
        status: "online",
        avatar: "FM",
        lastSeen: "Active now"
    }
];

// Screen Management
class ScreenManager {
    constructor() {
        this.screens = {
            contacts: document.getElementById('contactsScreen'),
            chat: document.getElementById('chatScreen'),
            call: document.getElementById('callScreen'),
            signIn: document.getElementById('signInScreen')
        };
    }

    showScreen(screenName) {
        Object.values(this.screens).forEach(screen => {
            screen.classList.add('hidden');
        });
        
        if (this.screens[screenName]) {
            this.screens[screenName].classList.remove('hidden');
        }

        // Update header
        this.updateHeader(screenName);
        appState.currentScreen = screenName;
    }

    updateHeader(screenName) {
        const backBtn = document.getElementById('backBtn');
        const headerTitle = document.getElementById('headerTitle');

        if (screenName === 'contacts') {
            backBtn.classList.add('d-none');
            headerTitle.textContent = 'ChatCall';
        } else {
            backBtn.classList.remove('d-none');
            if (screenName === 'chat') {
                headerTitle.textContent = appState.currentContact?.name || 'Chat';
            } else if (screenName === 'call') {
                headerTitle.textContent = 'Call';
            }
        }
    }
}

// UI Components
class UIComponents {
    static createContactItem(contact) {
        const statusClass = `status-${contact.status}`;
        
        return `
            <div class="contact-item" data-contact-id="${contact.id}">
                <div class="contact-avatar position-relative">
                    ${contact.avatar}
                    <div class="status-indicator ${statusClass}"></div>
                </div>
                <div class="contact-info">
                    <div class="contact-name">${contact.name}</div>
                    <div class="contact-status">${contact.lastSeen}</div>
                </div>
                <div class="contact-actions">
                    <button class="btn-icon btn-primary chat-btn" data-contact-id="${contact.id}">
                        <i class="bi bi-chat"></i>
                    </button>
                    <button class="btn-icon btn-success call-btn" data-contact-id="${contact.id}">
                        <i class="bi bi-telephone"></i>
                    </button>
                </div>
            </div>
        `;
    }

    static createMessage(message) {
        const messageClass = message.sent ? 'sent' : 'received';
        const time = message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        return `
            <div class="message ${messageClass}">
                <div class="message-bubble">
                    ${message.text}
                    <div class="message-time">${time}</div>
                </div>
            </div>
        `;
    }

    static renderContacts() {
        const contactsList = document.getElementById('contactsList');
        contactsList.innerHTML = CONTACTS.map(contact => 
            UIComponents.createContactItem(contact)
        ).join('');
    }

    static renderMessages(contactId) {
        const chatMessages = document.getElementById('chatMessages');
        const messages = appState.getMessages(contactId);
        
        chatMessages.innerHTML = messages.map(message => 
            UIComponents.createMessage(message)
        ).join('');
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    static updateChatHeader(contact) {
        document.getElementById('chatAvatar').textContent = contact.avatar;
        document.getElementById('chatContactName').textContent = contact.name;
        document.getElementById('chatContactStatus').textContent = contact.lastSeen;
    }

    static updateCallScreen(contact) {
        document.getElementById('callAvatar').textContent = contact.avatar;
        document.getElementById('callContactName').textContent = contact.name;
    }
}

// Call Management
class CallManager {
    constructor() {
        this.callTimer = null;
        this.startTime = null;
    }

    startCall(contact) {
        appState.isInCall = true;
        appState.callStartTime = new Date();
        
        UIComponents.updateCallScreen(contact);
        screenManager.showScreen('call');
        
        // Simulate call connection after 2 seconds
        setTimeout(() => {
            document.getElementById('callStatus').textContent = 'Connected';
            this.startTimer();
        }, 2000);
    }

    startTimer() {
        this.startTime = Date.now();
        this.callTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            document.getElementById('callDuration').textContent = `${minutes}:${seconds}`;
        }, 1000);
    }

    endCall() {
        appState.isInCall = false;
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
        
        // Reset call controls
        appState.isMuted = false;
        appState.isSpeakerOn = false;
        this.updateCallControls();
        
        screenManager.showScreen('chat');
    }

    toggleMute() {
        appState.isMuted = !appState.isMuted;
        this.updateCallControls();
    }

    toggleSpeaker() {
        appState.isSpeakerOn = !appState.isSpeakerOn;
        this.updateCallControls();
    }

    updateCallControls() {
        const muteBtn = document.getElementById('muteBtn');
        const speakerBtn = document.getElementById('speakerBtn');
        
        // Update mute button
        if (appState.isMuted) {
            muteBtn.classList.add('active');
            muteBtn.querySelector('i').className = 'bi bi-mic-mute';
        } else {
            muteBtn.classList.remove('active');
            muteBtn.querySelector('i').className = 'bi bi-mic';
        }
        
        // Update speaker button
        if (appState.isSpeakerOn) {
            speakerBtn.classList.add('active');
            speakerBtn.querySelector('i').className = 'bi bi-volume-up-fill';
        } else {
            speakerBtn.classList.remove('active');
            speakerBtn.querySelector('i').className = 'bi bi-volume-up';
        }
    }
}

// Message Management
class MessageManager {
    static sendMessage(text) {
        if (!text.trim() || !appState.currentContact) return;
        
        // Add user message
        appState.addMessage(appState.currentContact.id, text, true);
        UIComponents.renderMessages(appState.currentContact.id);
        
        // Simulate auto-reply after 1-2 seconds
        setTimeout(() => {
            const responses = [
                "Thanks for your message!",
                "I'll get back to you soon.",
                "That sounds great!",
                "Let me think about it.",
                "Sure, no problem!",
                "I understand."
            ];
            
            const randomResponse = responses[Math.floor(Math.random() * responses.length)];
            appState.addMessage(appState.currentContact.id, randomResponse, false);
            UIComponents.renderMessages(appState.currentContact.id);
        }, 1000 + Math.random() * 1000);
    }
}

// Event Handlers
class EventHandlers {
    static init() {
        // Back button
        document.getElementById('backBtn').addEventListener('click', () => {
            if (appState.currentScreen === 'call') {
                screenManager.showScreen('chat');
            } else {
                screenManager.showScreen('contacts');
                appState.currentContact = null;
            }
        });

        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => {
            const newTheme = appState.theme === 'light' ? 'dark' : 'light';
            appState.setTheme(newTheme);
        });

        // Contacts list
        document.getElementById('contactsList').addEventListener('click', (e) => {
            const contactId = parseInt(e.target.closest('[data-contact-id]')?.dataset.contactId);
            if (!contactId) return;

            const contact = CONTACTS.find(c => c.id === contactId);
            if (!contact) return;

            appState.currentContact = contact;

            if (e.target.closest('.chat-btn')) {
                UIComponents.updateChatHeader(contact);
                UIComponents.renderMessages(contactId);
                screenManager.showScreen('chat');
            } else if (e.target.closest('.call-btn')) {
                callManager.startCall(contact);
            }
        });

        // Chat screen call button
        document.getElementById('callBtn').addEventListener('click', () => {
            if (appState.currentContact) {
                callManager.startCall(appState.currentContact);
            }
        });

        // Message input
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');

        const sendMessage = () => {
            const text = messageInput.value.trim();
            if (text) {
                MessageManager.sendMessage(text);
                messageInput.value = '';
            }
        };

        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Call controls
        document.getElementById('endCallBtn').addEventListener('click', () => {
            callManager.endCall();
        });

        document.getElementById('muteBtn').addEventListener('click', () => {
            callManager.toggleMute();
        });

        document.getElementById('speakerBtn').addEventListener('click', () => {
            callManager.toggleSpeaker();
        });

        // PWA Installation
        this.initPWA();
    }

    static initPWA() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            const swCode = `
                const CACHE_NAME = 'chatcall-v1';
                const urlsToCache = ['/'];
                
                self.addEventListener('install', event => {
                    event.waitUntil(
                        caches.open(CACHE_NAME)
                            .then(cache => cache.addAll(urlsToCache))
                    );
                });
                
                self.addEventListener('fetch', event => {
                    event.respondWith(
                        caches.match(event.request)
                            .then(response => response || fetch(event.request))
                    );
                });
            `;
            
            const blob = new Blob([swCode], { type: 'application/javascript' });
            const swURL = URL.createObjectURL(blob);
            
            navigator.serviceWorker.register(swURL)
                .then(registration => {
                    console.log('ServiceWorker registered successfully');
                })
                .catch(error => {
                    console.log('ServiceWorker registration failed');
                });
        }

        // Handle PWA install prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Show install button or prompt
            console.log('PWA install prompt ready');
        });
    }
}

// Initialize Application
const appState = new AppState();
const screenManager = new ScreenManager();
const callManager = new CallManager();

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Render initial screen
    // UIComponents.renderContacts();
    // screenManager.showScreen('contacts');
    screenManager.showScreen('signIn');    
    // Initialize event handlers
    EventHandlers.init();
    
    console.log('ChatCall PWA initialized successfully!');
});

// Utility Functions
class Utils {
    static formatTime(date) {
        return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    static formatDate(date) {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString();
        }
    }

    static generateAvatar(name) {
        const words = name.split(' ');
        if (words.length >= 2) {
            return (words[0][0] + words[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }

    static createNotification(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            return new Notification(title, {
                icon: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgZmlsbD0iIzBkNmVmZCIvPjwvc3ZnPg==',
                badge: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCIgZmlsbD0iIzBkNmVmZCIvPjwvc3ZnPg==',
                ...options
            });
        }
        return null;
    }

    static requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
}

// Enhanced Features for Production Use
class EnhancedFeatures {
    static init() {
        // Request notification permission
        Utils.requestNotificationPermission();
        
        // Add keyboard shortcuts
        this.initKeyboardShortcuts();
        
        // Add visibility change handler
        this.initVisibilityHandler();
        
        // Add online/offline detection
        this.initNetworkDetection();
    }

    static initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Escape key to go back
            if (e.key === 'Escape') {
                if (appState.currentScreen === 'call') {
                    callManager.endCall();
                } else if (appState.currentScreen === 'chat') {
                    screenManager.showScreen('contacts');
                }
            }
            
            // Ctrl/Cmd + T for theme toggle
            if ((e.ctrlKey || e.metaKey) && e.key === 't') {
                e.preventDefault();
                const newTheme = appState.theme === 'light' ? 'dark' : 'light';
                appState.setTheme(newTheme);
            }
        });
    }

    static initVisibilityHandler() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // App went to background
                console.log('App backgrounded');
            } else {
                // App came to foreground
                console.log('App foregrounded');
            }
        });
    }

    static initNetworkDetection() {
        window.addEventListener('online', () => {
            console.log('Network connected');
            // Could show a toast notification
        });

        window.addEventListener('offline', () => {
            console.log('Network disconnected');
            // Could show offline indicator
        });
    }
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', () => {
    EnhancedFeatures.init();
});