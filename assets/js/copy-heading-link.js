;(function () {
    const anchors = document.querySelectorAll(
        'h1[id] a[href^="#"],' +
        'h2[id] a[href^="#"],' +
        'h3[id] a[href^="#"]'
    );

    function focusById(id) {
        const element = document.getElementById(id);
        if (!element) return;
        if (!element.hasAttribute('tabindex')) {
            element.setAttribute('tabindex', '-1');
        }
        element.focus({ preventScroll: true });
        element.scrollIntoView({ block: 'start' });
    }

    for (const anchor of anchors) {
        anchor.addEventListener('click', async () => {
            const href = anchor.getAttribute('href');
            const id = href && href.startsWith('#') ? href.slice(1) : anchor.closest('h1,h2,h3')?.id;
            if (!id) return;

            const url = `${location.origin}${location.pathname}${location.search}#${id}`;

            try {
                await navigator.clipboard.writeText(url);
                anchor.classList.add('state-success');
                setTimeout(() => anchor.classList.remove('state-success'), 1200);
            } catch (error) {
                console.error('Copying to clipboard failed', error);
            }

            // Focus target
            focusById(id);
        });
    }

    // Handle direct load with hash
    if (location.hash) {
        focusById(location.hash.slice(1));
    }

    // Handle manual hash changes
    window.addEventListener('hashchange', () => {
        if (location.hash) {
            focusById(location.hash.slice(1));
        }
    });
})();
