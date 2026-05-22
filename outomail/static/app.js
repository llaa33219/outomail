const API_BASE = '/api';
const API_KEY_STORAGE = 'outomail_api_key';
const THEME_STORAGE = 'outomail_theme';
const REFRESH_INTERVAL = 30000;

let currentRoute = null;
let refreshTimer = null;
let searchDebounce = null;

function getApiKey() {
    return localStorage.getItem(API_KEY_STORAGE);
}

function setApiKey(key) {
    localStorage.setItem(API_KEY_STORAGE, key);
}

function getTheme() {
    return localStorage.getItem(THEME_STORAGE) || 'light';
}

function setTheme(theme) {
    localStorage.setItem(THEME_STORAGE, theme);
    document.documentElement.setAttribute('data-theme', theme);
}

async function apiFetch(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    const apiKey = getApiKey();
    if (apiKey) {
        headers['X-API-Key'] = apiKey;
    }
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });
    if (response.status === 401) {
        localStorage.removeItem(API_KEY_STORAGE);
        navigate('login');
        throw new Error('Unauthorized');
    }
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
}

function navigate(route) {
    window.location.hash = route;
}

function getRoute() {
    const hash = window.location.hash.slice(1) || 'login';
    const parts = hash.split('/');
    return {
        route: parts[0] || 'login',
        params: parts.slice(1)
    };
}

function render() {
    const { route, params } = getRoute();
    const app = document.getElementById('app');
    const apiKey = getApiKey();

    if (!apiKey && route !== 'login') {
        navigate('login');
        return;
    }

    if (apiKey && route === 'login') {
        navigate('mailbox');
        return;
    }

    currentRoute = route;

    switch (route) {
        case 'login':
            renderLogin(app);
            break;
        case 'mailbox':
            renderMailbox(app, params[0]);
            break;
        case 'message':
            renderMessage(app, params[0]);
            break;
        case 'compose':
            renderCompose(app, params[0]);
            break;
        case 'settings':
            renderSettings(app);
            break;
        case 'search':
            renderSearch(app, params[0]);
            break;
        default:
            navigate('mailbox');
    }
}

function renderLogin(container) {
    container.innerHTML = `
        <div class="auth-container">
            <div class="auth-card fade-in" id="auth-card">
                <div class="auth-logo">
                    <h1>Outomail</h1>
                    <p id="auth-subtitle">Sign in to your mailbox</p>
                </div>
                <form id="auth-form">
                    <div class="form-group" id="display-name-group" style="display: none;">
                        <label for="display_name">Display Name</label>
                        <input type="text" id="display_name" autocomplete="name">
                    </div>
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" required autocomplete="email">
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" required autocomplete="current-password">
                    </div>
                    <div id="auth-error" class="alert alert-error hidden"></div>
                    <button type="submit" class="btn btn-primary btn-block" id="auth-submit-btn">Sign In</button>
                </form>
                <div class="auth-toggle">
                    <a id="auth-toggle-link">Don't have an account? Register</a>
                </div>
            </div>
        </div>
    `;

    let isRegisterMode = false;

    const authForm = document.getElementById('auth-form');
    const authError = document.getElementById('auth-error');
    const authToggleLink = document.getElementById('auth-toggle-link');
    const authSubtitle = document.getElementById('auth-subtitle');
    const authSubmitBtn = document.getElementById('auth-submit-btn');
    const displayNameGroup = document.getElementById('display-name-group');

    authToggleLink.addEventListener('click', () => {
        isRegisterMode = !isRegisterMode;
        if (isRegisterMode) {
            authSubtitle.textContent = 'Create your account';
            authSubmitBtn.textContent = 'Register';
            authToggleLink.textContent = 'Already have an account? Sign in';
            displayNameGroup.style.display = 'block';
        } else {
            authSubtitle.textContent = 'Sign in to your mailbox';
            authSubmitBtn.textContent = 'Sign In';
            authToggleLink.textContent = "Don't have an account? Register";
            displayNameGroup.style.display = 'none';
        }
        authError.classList.add('hidden');
    });

    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const displayName = document.getElementById('display_name').value;

        if (isRegisterMode) {
            try {
                await apiFetch('/auth/register', {
                    method: 'POST',
                    body: JSON.stringify({ email, password, display_name: displayName })
                });
                isRegisterMode = false;
                authSubtitle.textContent = 'Sign in to your mailbox';
                authSubmitBtn.textContent = 'Sign In';
                authToggleLink.textContent = "Don't have an account? Register";
                displayNameGroup.style.display = 'none';
                authError.textContent = 'Registration successful! Please sign in.';
                authError.classList.remove('hidden');
                authError.classList.remove('alert-error');
                authError.classList.add('alert-success');
            } catch (err) {
                authError.textContent = 'Registration failed. Email may already be in use.';
                authError.classList.remove('hidden');
                authError.classList.remove('alert-success');
                authError.classList.add('alert-error');
            }
        } else {
            try {
                const data = await apiFetch('/auth/login', {
                    method: 'POST',
                    body: JSON.stringify({ email, password })
                });
                setApiKey(data.api_key);
                navigate('mailbox');
            } catch (err) {
                authError.textContent = 'Invalid email or password';
                authError.classList.remove('hidden');
            }
        }
    });
}

async function renderMailbox(container, mailboxId = 'inbox') {
    container.innerHTML = `
        <div class="main-layout">
            <div class="sidebar-overlay" id="sidebar-overlay"></div>
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <span class="sidebar-logo">Outomail</span>
                </div>
                <nav class="sidebar-nav">
                    <a class="nav-item ${mailboxId === 'inbox' ? 'active' : ''}" data-route="mailbox/inbox">
                        <span>Inbox</span>
                        <span class="badge" id="unread-badge"></span>
                    </a>
                    <a class="nav-item" data-route="mailbox/sent">
                        <span>Sent</span>
                    </a>
                    <a class="nav-item" data-route="compose">
                        <span>Compose</span>
                    </a>
                </nav>
                <div class="sidebar-footer">
                    <div class="theme-toggle">
                        <span>Dark Mode</span>
                        <div class="toggle-switch" id="theme-toggle"></div>
                    </div>
                </div>
            </aside>
            <main class="content-area">
                <header class="content-header">
                    <button class="mobile-menu-btn" id="mobile-menu-btn">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                    </button>
                    <h2>${mailboxId === 'inbox' ? 'Inbox' : 'Sent'}</h2>
                    <div class="search-bar">
                        <input type="text" placeholder="Search messages..." id="search-input">
                    </div>
                </header>
                <div class="content-body">
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                    </div>
                    <div id="mailbox-content"></div>
                </div>
            </main>
        </div>
    `;

    setupThemeToggle();
    setupMobileMenu();
    setupNavListeners();
    setupSearch();

    try {
        const mailboxes = await apiFetch('/mailboxes');
        const currentMailbox = mailboxes.find(m => m.id === mailboxId) || mailboxes[0];
        const messages = await apiFetch(`/mailboxes/${currentMailbox.id}/messages`);
        renderMailboxList(messages, currentMailbox.id);
        updateUnreadBadge(mailboxes);
    } catch (err) {
        document.getElementById('mailbox-content').innerHTML = `
            <div class="mailbox-empty">
                <p>Failed to load messages</p>
            </div>
        `;
    }

    document.getElementById('loading').classList.add('hidden');
    startRefreshTimer();
}

function renderMailboxList(messages, mailboxId) {
    const container = document.getElementById('mailbox-content');
    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="mailbox-empty">
                <svg fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                    <path d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/>
                </svg>
                <p>No messages yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="mailbox-list fade-in">
            ${messages.map((msg, index) => `
                <div>
                    <div class="mail-item ${msg.read ? '' : 'unread'}" data-id="${msg.id}">
                        <div class="mail-checkbox">
                            <input type="checkbox">
                        </div>
                        <div class="mail-avatar">${getInitials(msg.from)}</div>
                        <div class="mail-content">
                            <span class="mail-from">${msg.from.name || msg.from.email}</span>
                            <span class="mail-subject">${msg.subject}</span>
                            <span class="mail-date">${formatDate(msg.date)}</span>
                        </div>
                        <div class="mail-actions">
                            <button class="btn btn-icon delete-btn" data-id="${msg.id}" title="Delete">
                                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                                    <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                    ${index < messages.length - 1 ? '<div class="mail-item-divider"></div>' : ''}
                </div>
            `).join('')}
        </div>
    `;

    container.querySelectorAll('.mail-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('.mail-checkbox') || e.target.closest('.mail-actions')) return;
            const id = item.dataset.id;
            apiFetch(`/messages/${id}/read`, { method: 'POST' }).catch(() => {});
            navigate(`message/${id}`);
        });
    });

    container.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            if (confirm('Delete this message?')) {
                try {
                    await apiFetch(`/messages/${id}`, { method: 'DELETE' });
                    item.classList.add('hidden');
                    render();
                } catch (err) {
                    alert('Failed to delete message');
                }
            }
        });
    });
}

async function renderMessage(container, messageId) {
    container.innerHTML = `
        <div class="main-layout">
            <div class="sidebar-overlay" id="sidebar-overlay"></div>
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <span class="sidebar-logo">Outomail</span>
                </div>
                <nav class="sidebar-nav">
                    <a class="nav-item" data-route="mailbox/inbox">Inbox</a>
                    <a class="nav-item" data-route="mailbox/sent">Sent</a>
                    <a class="nav-item" data-route="compose">Compose</a>
                </nav>
                <div class="sidebar-footer">
                    <div class="theme-toggle">
                        <span>Dark Mode</span>
                        <div class="toggle-switch" id="theme-toggle"></div>
                    </div>
                </div>
            </aside>
            <main class="content-area">
                <header class="content-header">
                    <button class="mobile-menu-btn" id="mobile-menu-btn">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                    </button>
                    <h2>Message</h2>
                    <div class="search-bar">
                        <input type="text" placeholder="Search messages..." id="search-input">
                    </div>
                </header>
                <div class="content-body">
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                    </div>
                    <div id="message-content"></div>
                </div>
            </main>
        </div>
    `;

    setupThemeToggle();
    setupMobileMenu();
    setupNavListeners();
    setupSearch();

    try {
        const message = await apiFetch(`/messages/${messageId}`);
        renderMessageView(message);
    } catch (err) {
        document.getElementById('message-content').innerHTML = `
            <div class="mailbox-empty">
                <p>Failed to load message</p>
            </div>
        `;
    }

    document.getElementById('loading').classList.add('hidden');
}

function renderMessageView(message) {
    const container = document.getElementById('message-content');
    container.innerHTML = `
        <div class="message-view fade-in">
            <div class="message-header">
                <h1>${message.subject}</h1>
                <div class="message-meta">
                    <div class="avatar">${getInitials(message.from)}</div>
                    <div class="message-from-info">
                        <div class="message-from-name">${message.from.name || message.from.email}</div>
                        <div class="message-from-email">${message.from.email}</div>
                    </div>
                    <span class="mail-date">${formatDate(message.date)}</span>
                </div>
            </div>
            <div class="message-body">${message.body}</div>
        </div>
    `;
}

async function renderCompose(container, replyToId = null) {
    container.innerHTML = `
        <div class="main-layout">
            <div class="sidebar-overlay" id="sidebar-overlay"></div>
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <span class="sidebar-logo">Outomail</span>
                </div>
                <nav class="sidebar-nav">
                    <a class="nav-item" data-route="mailbox/inbox">Inbox</a>
                    <a class="nav-item" data-route="mailbox/sent">Sent</a>
                    <a class="nav-item active" data-route="compose">Compose</a>
                </nav>
                <div class="sidebar-footer">
                    <div class="theme-toggle">
                        <span>Dark Mode</span>
                        <div class="toggle-switch" id="theme-toggle"></div>
                    </div>
                </div>
            </aside>
            <main class="content-area">
                <header class="content-header">
                    <button class="mobile-menu-btn" id="mobile-menu-btn">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                    </button>
                    <h2>Compose</h2>
                </header>
                <div class="content-body">
                    <div class="compose-form fade-in">
                        <form id="compose-form">
                            <div class="form-row">
                                <label>To</label>
                                <input type="email" id="compose-to" required>
                            </div>
                            <div class="form-row">
                                <label>Subject</label>
                                <input type="text" id="compose-subject" required>
                            </div>
                            <div class="editor">
                                <textarea id="compose-body" required></textarea>
                            </div>
                            <div id="compose-error" class="alert alert-error hidden"></div>
                            <div class="compose-actions">
                                <button type="button" class="btn btn-secondary" onclick="navigate('mailbox/inbox')">Cancel</button>
                                <button type="submit" class="btn btn-primary">Send</button>
                            </div>
                        </form>
                    </div>
                </div>
            </main>
        </div>
    `;

    setupThemeToggle();
    setupMobileMenu();
    setupNavListeners();

    if (replyToId) {
        try {
            const message = await apiFetch(`/messages/${replyToId}`);
            document.getElementById('compose-to').value = message.from.email;
            document.getElementById('compose-subject').value = message.subject.startsWith('Re:') ? message.subject : `Re: ${message.subject}`;
        } catch (err) {}
    }

    document.getElementById('compose-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const to = document.getElementById('compose-to').value;
        const subject = document.getElementById('compose-subject').value;
        const body = document.getElementById('compose-body').value;
        const errorEl = document.getElementById('compose-error');

        try {
            await apiFetch('/messages', {
                method: 'POST',
                body: JSON.stringify({ to, subject, body })
            });
            navigate('mailbox/sent');
        } catch (err) {
            errorEl.textContent = 'Failed to send message';
            errorEl.classList.remove('hidden');
        }
    });
}

async function renderSettings(container) {
    container.innerHTML = `
        <div class="main-layout">
            <div class="sidebar-overlay" id="sidebar-overlay"></div>
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <span class="sidebar-logo">Outomail</span>
                </div>
                <nav class="sidebar-nav">
                    <a class="nav-item" data-route="mailbox/inbox">Inbox</a>
                    <a class="nav-item" data-route="mailbox/sent">Sent</a>
                    <a class="nav-item" data-route="compose">Compose</a>
                </nav>
                <div class="sidebar-footer">
                    <div class="theme-toggle">
                        <span>Dark Mode</span>
                        <div class="toggle-switch" id="theme-toggle"></div>
                    </div>
                </div>
            </aside>
            <main class="content-area">
                <header class="content-header">
                    <button class="mobile-menu-btn" id="mobile-menu-btn">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                    </button>
                    <h2>DNS Settings</h2>
                </header>
                <div class="content-body">
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                    </div>
                    <div id="settings-content"></div>
                </div>
            </main>
        </div>
    `;

    setupThemeToggle();
    setupMobileMenu();
    setupNavListeners();

    try {
        const dns = await apiFetch('/settings/dns');
        renderDnsRecords(dns);
    } catch (err) {
        document.getElementById('settings-content').innerHTML = `
            <div class="settings-section">
                <div class="settings-content">
                    <p>Failed to load DNS settings</p>
                </div>
            </div>
        `;
    }

    document.getElementById('loading').classList.add('hidden');
}

function renderDnsRecords(dns) {
    const container = document.getElementById('settings-content');
    container.innerHTML = `
        <div class="settings-section fade-in">
            <div class="settings-header">
                <h3>Configure your domain's DNS records</h3>
            </div>
            <div class="settings-content">
                ${dns.records.map(record => `
                    <div class="dns-record">
                        <span class="dns-type">${record.type}</span>
                        <span class="dns-name">${record.name}</span>
                        <span class="dns-value">${record.value}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

async function renderSearch(container, query = '') {
    container.innerHTML = `
        <div class="main-layout">
            <div class="sidebar-overlay" id="sidebar-overlay"></div>
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <span class="sidebar-logo">Outomail</span>
                </div>
                <nav class="sidebar-nav">
                    <a class="nav-item" data-route="mailbox/inbox">Inbox</a>
                    <a class="nav-item" data-route="mailbox/sent">Sent</a>
                    <a class="nav-item" data-route="compose">Compose</a>
                </nav>
                <div class="sidebar-footer">
                    <div class="theme-toggle">
                        <span>Dark Mode</span>
                        <div class="toggle-switch" id="theme-toggle"></div>
                    </div>
                </div>
            </aside>
            <main class="content-area">
                <header class="content-header">
                    <button class="mobile-menu-btn" id="mobile-menu-btn">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12h18M3 6h18M3 18h18"/>
                        </svg>
                    </button>
                    <h2>Search</h2>
                    <div class="search-bar">
                        <input type="text" placeholder="Search messages..." id="search-input" value="${query}">
                    </div>
                </header>
                <div class="content-body">
                    <div id="search-content">
                        <div class="search-results-header">Enter a search term</div>
                    </div>
                </div>
            </main>
        </div>
    `;

    setupThemeToggle();
    setupMobileMenu();
    setupNavListeners();
    setupSearch();

    if (query) {
        performSearch(query);
    }

    document.getElementById('loading')?.classList.add('hidden');
}

async function performSearch(query) {
    const container = document.getElementById('search-content');
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
        </div>
    `;

    try {
        const results = await apiFetch(`/search?q=${encodeURIComponent(query)}`);
        if (!results || results.length === 0) {
            container.innerHTML = `
                <div class="search-results">
                    <div class="search-results-header">No results for "${query}"</div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="search-results fade-in">
                <div class="search-results-header">${results.length} result${results.length !== 1 ? 's' : ''} for "${query}"</div>
                ${results.map(msg => `
                    <div class="mail-item ${msg.read ? '' : 'unread'}" data-id="${msg.id}">
                        <div class="mail-avatar">${getInitials(msg.from)}</div>
                        <div class="mail-content">
                            <span class="mail-from">${msg.from.name || msg.from.email}</span>
                            <span class="mail-subject">${msg.subject}</span>
                            <span class="mail-date">${formatDate(msg.date)}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        container.querySelectorAll('.mail-item').forEach(item => {
            item.addEventListener('click', () => {
                navigate(`message/${item.dataset.id}`);
            });
        });
    } catch (err) {
        container.innerHTML = `
            <div class="search-results">
                <div class="search-results-header">Search failed</div>
            </div>
        `;
    }
}

function setupThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    toggle.addEventListener('click', () => {
        const current = getTheme();
        setTheme(current === 'light' ? 'dark' : 'light');
    });
}

function setupMobileMenu() {
    const btn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (!btn || !sidebar) return;

    btn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay?.classList.toggle('open');
    });

    overlay?.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
    });
}

function setupNavListeners() {
    document.querySelectorAll('.nav-item[data-route]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const route = item.dataset.route;
            navigate(route);
            document.getElementById('sidebar')?.classList.remove('open');
            document.getElementById('sidebar-overlay')?.classList.remove('open');
        });
    });
}

function setupSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;

    input.addEventListener('input', (e) => {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                navigate(`search/${encodeURIComponent(query)}`);
            }
        }, 300);
    });
}

function startRefreshTimer() {
    clearInterval(refreshTimer);
    if (currentRoute === 'mailbox') {
        refreshTimer = setInterval(() => {
            if (currentRoute === 'mailbox') {
                render();
            }
        }, REFRESH_INTERVAL);
    }
}

async function updateUnreadBadge(mailboxes) {
    const badge = document.getElementById('unread-badge');
    if (!badge) return;
    const inbox = mailboxes.find(m => m.id === 'inbox');
    if (inbox && inbox.unread_count > 0) {
        badge.textContent = inbox.unread_count;
    } else {
        badge.textContent = '';
    }
}

function getInitials(from) {
    if (!from) return '?';
    const name = from.name || from.email;
    const parts = name.split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const oneDay = 24 * 60 * 60 * 1000;

    if (diff < oneDay && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    }
    if (diff < 7 * oneDay) {
        return date.toLocaleDateString('en-US', { weekday: 'short' });
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

window.addEventListener('hashchange', render);
window.addEventListener('load', () => {
    setTheme(getTheme());
    render();
});
window.addEventListener('beforeunload', () => {
    clearInterval(refreshTimer);
});