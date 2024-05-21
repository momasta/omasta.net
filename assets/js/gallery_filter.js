const hideTimeout = 200; // Animation delay to hide gallery images (keep in sync with $gallery-transition-delay)

let lastFilterQuery = '';
let galleryFilterForm = document.querySelector('.gallery form');
let galleryFilterInput = document.querySelector('.gallery-filter-input');
let images = document.querySelectorAll('.gallery-image');

function show(element) {
	element.style.display = 'block';
	element.classList.remove('state-hidden');
	element.classList.add('state-visible');
}

function hide(element) {
	element.classList.remove('state-visible');
	element.classList.add('state-hidden');

    setTimeout(function() {
		element.style.display = 'none';
	}, hideTimeout);
}

function resetGallery() {
    images.forEach(function (image) {
        show(image);
    });
}

function filterGallery(query) {
    let queryFormatted = '';

    if (typeof query !== 'undefined' && query.trim()) {
        if (lastFilterQuery !== query) {
            let firstImageFound = null;

            queryFormatted = query.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            images.forEach(function (image) {
                let imageTitleRaw = image.querySelector('img').getAttribute('alt');

                // If we still have a filter query after formatting it
                if (queryFormatted && queryFormatted !== '') {
                    if (imageTitleRaw) {
                        let imageTitle = imageTitleRaw.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

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
                                hide(image);
                            } else {
                            	show(image);
                            }

                        // If the query contains a single word
                        } else if (imageTitle.indexOf(queryFormatted) === -1) {
                            hide(image);
                        } else {
                            if (image && !firstImageFound) {
                                firstImageFound = image;
                            }
                            show(image);
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

function stupidCallback() {
    filterGallery(galleryFilterInput.value);
}

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

// Filter images on load if a query remained in place
stupidCallback();

// When DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    stupidCallback();

    galleryFilterForm.addEventListener('submit', function (event) {
        event.preventDefault();
        event.stopImmediatePropagation();

        stupidCallback();
    }, false);
    galleryFilterInput.addEventListener('keyup', stupidCallback, false);
    galleryFilterInput.addEventListener('paste', stupidCallback, false);
    galleryFilterInput.addEventListener('propertychange', stupidCallback, false);
    galleryFilterInput.addEventListener('change', stupidCallback, false);
    galleryFilterInput.addEventListener('search', stupidCallback, false);
    galleryFilterInput.addEventListener('input', stupidCallback, false);
    galleryFilterInput.addEventListener('autocompleteSelect', stupidCallback, false);
    document.addEventListener('keydown', keyEventHandler, false);
    document.addEventListener('backbutton', resetGallery, false);
});
