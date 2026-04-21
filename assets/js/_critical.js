const html = document.documentElement;
const storedTheme = localStorage.getItem('theme');

if (storedTheme) {
    html.classList.add(storedTheme);
} else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    html.classList.add('theme-light');
} else {
    html.classList.add('theme-dark'); // Default theme
}