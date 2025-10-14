;(function () {
    const anchors = document.querySelectorAll(
        'h1[id] a[href^="#"],' +
        'h2[id] a[href^="#"],' +
        'h3[id] a[href^="#"]')

    for (const a of anchors) {
        a.addEventListener('click', async (event) => {
            const href = a.getAttribute('href')
            const id = href && href.startsWith('#') ? href.slice(1) : a.closest('h1,h2,h3')?.id
            if (!id) return
            const url = '${location.origin}${location.pathname}${location.search}#${id}'

            try {
                await navigator.clipboard.writeText(url)
                const oldTitle = a.getAttribute('title') || ''
                a.setAttribute('title', '✓')
                setTimeout(() => a.setAttribute('title', oldTitle), 1200)
            } catch (err) {
                console.error('Copying to clipboard failed', err)
            }
        })
    }
})()
