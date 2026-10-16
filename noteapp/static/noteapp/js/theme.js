(() => {
    const root = document.documentElement;
    const storageKey = 'notebook-theme';
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    let savedTheme = null;
    try {
        savedTheme = window.localStorage.getItem(storageKey);
    } catch (error) {
        // The toggle still works for this page if browser storage is unavailable.
    }

    let hasSavedPreference = savedTheme === 'light' || savedTheme === 'dark';
    let theme = hasSavedPreference ? savedTheme : (media.matches ? 'dark' : 'light');
    let toggle;

    function applyTheme(nextTheme, savePreference) {
        theme = nextTheme;
        root.dataset.theme = theme;
        if (themeMeta) {
            themeMeta.setAttribute('content', theme === 'dark' ? '#151927' : '#f7f8fc');
        }
        if (savePreference) {
            hasSavedPreference = true;
            try {
                window.localStorage.setItem(storageKey, theme);
            } catch (error) {
                // Keep the selected theme for this page even without browser storage.
            }
        }
        updateToggle();
    }

    function updateToggle() {
        if (!toggle) return;
        toggle.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
        toggle.setAttribute('aria-pressed', String(theme === 'dark'));
    }

    function initializeToggle() {
        toggle = document.getElementById('theme-toggle');
        updateToggle();
        if (toggle) {
            toggle.addEventListener('click', () => {
                applyTheme(theme === 'dark' ? 'light' : 'dark', true);
                toggle.closest('.nav-menu')?.removeAttribute('open');
            });
        }

        document.querySelectorAll('[data-password-toggle]').forEach((button) => {
            const input = document.getElementById(button.dataset.passwordToggle);
            if (!input) return;

            button.addEventListener('click', () => {
                const showPassword = input.type === 'password';
                input.type = showPassword ? 'text' : 'password';
                button.textContent = showPassword ? 'Hide' : 'Show';
                button.setAttribute('aria-label', `${showPassword ? 'Hide' : 'Show'} password`);
            });
        });

        const menu = document.querySelector('.nav-menu');
        if (menu) {
            document.addEventListener('click', (event) => {
                if (!menu.contains(event.target)) {
                    menu.removeAttribute('open');
                }
            });
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && menu.open) {
                    menu.removeAttribute('open');
                    menu.querySelector('summary')?.focus();
                }
            });
        }
    }

    applyTheme(theme, false);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeToggle, { once: true });
    } else {
        initializeToggle();
    }

    if (!hasSavedPreference) {
        media.addEventListener('change', (event) => {
            if (!hasSavedPreference) {
                applyTheme(event.matches ? 'dark' : 'light', false);
            }
        });
    }
})();
