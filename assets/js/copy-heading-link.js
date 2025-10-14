;(function () {
    const anchors = document.querySelectorAll(
        'h1[id] a[href^="#"],' +
        'h2[id] a[href^="#"],' +
        'h3[id] a[href^="#"]'
    );

    for (const anchor of anchors) {
        anchor.addEventListener('click', async (event) => {
            const href = anchor.getAttribute('href');
            const id = href && href.startsWith('#') ? href.slice(1) : anchor.closest('h1,h2,h3')?.id;
            if (!id) return;

            const url = `${location.origin}${location.pathname}${location.search}#${id}`;

            try {
                await navigator.clipboard.writeText(url);
                const oldTitle = anchor.getAttribute('title') || '';
                anchor.setAttribute('title', '✓');
                setTimeout(() => anchor.setAttribute('title', oldTitle), 1200);
            } catch (error) {
                console.error('Copying to clipboard failed', error);
            }
        });
    }
})();
