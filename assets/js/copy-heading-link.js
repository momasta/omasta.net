;(function () {
    const anchors = document.querySelectorAll(".heading-link");

    for (const anchor of anchors) {
        anchor.addEventListener('click', async () => {
            const href = anchor.getAttribute('href');
            const id = href && href.startsWith('#') ? href.slice(1) : anchor.closest('h2,h3')?.id;
            if (!id) return;

            const url = `${location.origin}${location.pathname}${location.search}#${id}`;

            try {
                await navigator.clipboard.writeText(url);
                anchor.classList.add('state-success');
                anchor.innerText = '✓';
                setTimeout(() => {
                    anchor.classList.remove('state-success');
                    anchor.innerText = '#';
                }, 1200);
            } catch (error) {
                console.error('Copying to clipboard failed', error);
            }
        });
    }
})();
