window.addEventListener('load', () => document.body.classList.add('loaded'));

const themeColorLight = '#b8b8b8';
const themeColorDark = '#000000';

const themePreference = () => {
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme) return storedTheme;
    if (window.matchMedia('(prefers-color-scheme: light)').matches) return 'theme-light';
    return 'theme-dark'; // Default theme
};

document.addEventListener('DOMContentLoaded', () => {
    const toggleThemeLight = document.querySelector('.toggle-theme-light');
    const toggleThemeDark = document.querySelector('.toggle-theme-dark');
    const metaThemeColor = document.querySelectorAll('meta[name="theme-color"]');
    const html = document.documentElement;

    const setTheme = (theme) => {
        html.classList.remove('theme-dark', 'theme-light');
        html.classList.add(theme);
        metaThemeColor.forEach(tag => tag.setAttribute('content', theme === 'theme-light' ? themeColorLight : themeColorDark));
    };

    const applyTheme = () => setTheme(themePreference());

    // Initial theme
    applyTheme();

    // Listen for system preference changes, but only if no override is set
    const systemChangeHandler = () => {
        if (!localStorage.getItem('theme')) applyTheme();
    };
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', systemChangeHandler);
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', systemChangeHandler);

    // Manual toggle - dark theme (override)
    toggleThemeDark.addEventListener('click', () => {
        setTheme('theme-dark');
        
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            localStorage.removeItem('theme'); // Back to auto
        } else {
            localStorage.setItem('theme', 'theme-dark');
        }
    }, false);

    // Manual toggle - light theme (override)
    toggleThemeLight.addEventListener('click', () => {
        setTheme('theme-light');
        
        if (window.matchMedia('(prefers-color-scheme: light)').matches) {
            localStorage.removeItem('theme'); // Back to auto
        } else {
            localStorage.setItem('theme', 'theme-light');
        }
    }, false);
}, false);