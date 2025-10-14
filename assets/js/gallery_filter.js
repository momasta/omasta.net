const hideTimeout = 200; // Animation delay to hide images, keep in sync with var(--ease)

const galleryFilterForm = document.querySelector('.gallery form');
const galleryFilterInput = document.querySelector('.gallery-filter-input');
const images = document.querySelectorAll('.gallery-image');

let lastFilterQuery = '';

function debounce(fn, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
}

function showResult(element) {
    element.style.display = 'block';
    element.offsetHeight;
    element.classList.remove('state-hidden');
    element.classList.add('state-visible');
}

function hideResult(element) {
    element.classList.remove('state-visible');
    element.classList.add('state-hidden');

    setTimeout(function () {
        element.style.display = 'none';
    }, hideTimeout);
}

function resetGallery() {
    images.forEach(function (image) {
        showResult(image);
    });
}

function filterGallery(query) {
    let queryFormatted = '';

    if (typeof query !== 'undefined' && query.trim()) {
        if (lastFilterQuery !== query) {
            let firstImageFound = null;

            queryFormatted = query
                .trim()
                .toLowerCase()
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "");
            images.forEach(function (image) {
                let imageTitleRaw = image.querySelector('img').getAttribute('alt');

                // If we still have a filter query after formatting it
                if (queryFormatted && queryFormatted !== '') {
                    if (imageTitleRaw) {
                        let imageTitle = imageTitleRaw
                            .trim()
                            .toLowerCase()
                            .normalize("NFD")
                            .replace(/[\u0300-\u036f]/g, "");

                        // If it contains a space, look for individual words
                        if (queryFormatted.indexOf(' ') !== -1) {
                            let notFound = false;
                            let queryWords = queryFormatted.split(' ');

                            queryWords.forEach(function (word) {
                                if (imageTitle.indexOf(word) === -1) {
                                    notFound = true;
                                }
                            });

                            if (notFound) {
                                hideResult(image);
                            } else {
                                showResult(image);
                            }

                            // If the query contains a single word
                        } else if (imageTitle.indexOf(queryFormatted) === -1) {
                            hideResult(image);
                        } else {
                            if (image && !firstImageFound) {
                                firstImageFound = image;
                            }
                            showResult(image);
                        }
                    }

                }
            });
        }
    } else {
        // If query is empty, make images re-appear
        resetGallery();
    }

    lastFilterQuery = query;
}

function applyFilter() {
    filterGallery(galleryFilterInput.value);
}

const debouncedApplyFilter = debounce(applyFilter, 200);

function keyEventHandler(event) {
    switch (event.key) {
        case "Escape":
            galleryFilterForm.reset();
            resetGallery();
            break;
        default:
            return;
    }

    event.preventDefault();
}

// When DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    applyFilter();

    galleryFilterForm.addEventListener('submit', function (event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        applyFilter();
    }, false);

    [
        'keyup',
        'paste',
        'input',
        'change',
        'search',
        'propertychange',
        'autocompleteSelect'
    ].forEach(eventName => {
        galleryFilterInput.addEventListener(eventName, debouncedApplyFilter, false);
    });

    document.addEventListener('keydown', keyEventHandler, false);
    document.addEventListener('backbutton', resetGallery, false);
});
