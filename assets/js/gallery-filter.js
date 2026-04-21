(() => {
    "use strict";

    // Utility: Debounce
    function debounce(fn, delay = 180) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn(...args), delay);
        };
    }

    // Utility: Text normalisation
    function normaliseText(text) {
        return (text || "")
            .toLowerCase()
            .trim()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")   // Remove accents/diacritics
            .replace(/['’`´]/g, "")            // Remove apostrophes and similar marks
            .replace(/[^a-z0-9\s]/g, "")       // Strip other punctuation/symbols
            .replace(/\s+/g, " ");             // Collapse multiple spaces
    }

    // Visibility management
    function showImage(element) {
        element.classList.remove("state-visually-hidden");
        element.removeAttribute("aria-hidden");
        element.inert = false;
    }

    function hideImage(element) {
        element.classList.add("state-visually-hidden");
        element.setAttribute("aria-hidden", "true");
        element.inert = true;
    }

    // Classification logic
    const MatchCategory = {
        EXACT_RAW: 1,
        RAW_STARTS_WITH: 2,
        NORMALIZED_STARTS_WITH: 3,
        MULTI_WORD: 4,
        NO_MATCH: 5
    };

    function classifyImageByAlt(altText, queryRaw) {
        const altRaw = altText || "";
        const qRaw = queryRaw || "";

        if (altRaw === qRaw) return MatchCategory.EXACT_RAW;
        if (altRaw.toLowerCase().startsWith(qRaw.toLowerCase())) {
            return MatchCategory.RAW_STARTS_WITH;
        }

        const altNorm = normaliseText(altRaw);
        const qNorm = normaliseText(qRaw);

        if (altNorm.startsWith(qNorm) && qNorm.length > 0) {
            return MatchCategory.NORMALIZED_STARTS_WITH;
        }

        const words = qNorm.split(/\s+/).filter(Boolean);
        if (words.length > 0) {
            const ok = words.every((w) => altNorm.includes(w));
            if (ok) return MatchCategory.MULTI_WORD;
        }

        return MatchCategory.NO_MATCH;
    }

    // URL integration
    function setQueryParamInURL(query) {
        const url = new URL(window.location.href);
        if (query && query.length > 0) {
            url.searchParams.set("q", query);
        } else {
            url.searchParams.delete("q");
        }
        history.replaceState(null, "", url);
    }

    function getQueryParamFromURL() {
        const url = new URL(window.location.href);
        return url.searchParams.get("q") || "";
    }

    // No results message
    function updateNoResultsMessage(noResultsEl, anyVisible) {
        if (!noResultsEl) return;
        if (anyVisible) {
            noResultsEl.setAttribute("aria-hidden", "true");
            noResultsEl.classList.add("state-visually-hidden");
        } else {
            noResultsEl.removeAttribute("aria-hidden");
            noResultsEl.classList.remove("state-visually-hidden");
        }
    }

    // Initialisation
    function initGalleryFiltering() {
        const container = document.querySelector(".gallery");
        if (!container) return;

        const form = document.querySelector("form");
        const input = document.querySelector(".gallery-filter-input");
        const images = Array.from(container.querySelectorAll(".gallery-image"));

        if (!form) return;
        if (!input) return;
        if (images.length === 0) return;

        const galleryParent = images[0].parentElement;
        if (!galleryParent) return;

        const originalOrder = images.slice();
        images.forEach((imgWrap) => {
            if (!imgWrap.classList.contains("state-visually-hidden")) {
                imgWrap.classList.remove("state-visually-hidden");
                imgWrap.removeAttribute("aria-hidden");
                imgWrap.inert = false;
            }
        });

        const noResultsEl = document.getElementById("gallery-no-results");

        function applyFilter(queryRaw) {
            const query = queryRaw || "";
            const trimmed = query.trim();

            if (trimmed.length === 0) {
                let anyVisible = false;
                originalOrder.forEach((element) => {
                    showImage(element);
                    galleryParent.appendChild(element);
                    anyVisible = true;
                });
                updateNoResultsMessage(noResultsEl, anyVisible);
                return;
            }

            const classified = images.map((element) => {
                const img = element.querySelector("img");
                const altText = img ? img.getAttribute("alt") || "" : "";
                const category = classifyImageByAlt(altText, trimmed);
                return {element, category};
            });

            let anyVisible = false;
            classified.forEach(({element, category}) => {
                if (category === MatchCategory.NO_MATCH) {
                    hideImage(element);
                } else {
                    showImage(element);
                    anyVisible = true;
                }
            });

            const priorityOrder = [
                MatchCategory.EXACT_RAW,
                MatchCategory.RAW_STARTS_WITH,
                MatchCategory.NORMALIZED_STARTS_WITH,
                MatchCategory.MULTI_WORD,
                MatchCategory.NO_MATCH
            ];

            classified
                .sort((a, b) => priorityOrder.indexOf(a.category) - priorityOrder.indexOf(b.category))
                .forEach(({element}) => galleryParent.appendChild(element));

            updateNoResultsMessage(noResultsEl, anyVisible);
        }

        const debouncedApply = debounce(() => applyFilter(input.value), 180);

        form.addEventListener("submit", (event) => {
            event.preventDefault();
            applyFilter(input.value);
            setQueryParamInURL(input.value.trim()); // URL updated only here
        });

        // Input events apply filter (debounced)
        ["input", "keyup", "paste", "change", "search"].forEach((evt) => {
            input.addEventListener(evt, () => {
                debouncedApply();
                if (input.value.trim() === "") {
                    setQueryParamInURL(""); // Clear q param when input is empty
                }
            });
        });

        // Keyboard shortcuts
        document.addEventListener("keydown", (event) => {
            /** @type {Object} */
            /** @property {Object} pswp */
            /** @property {boolean} pswp.isOpen */
            /** @property {Function} pswp.close */
            const pswp = window.pswpLightbox?.pswp;

            if (event.key === "Escape") {
                if (pswp?.isOpen) {
                    return; // If PhotoSwipe is open, let it close first
                }
                input.value = "";
                applyFilter("");
                setQueryParamInURL(""); // Clear q param on Escape reset
                return;
            }
            if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey) {
                if (pswp?.isOpen) {
                    pswp.close();
                }
                const activeElement = document.activeElement;
                const isEditable =
                    activeElement &&
                    (activeElement.tagName === "INPUT" ||
                        activeElement.tagName === "TEXTAREA" ||
                        activeElement.isContentEditable);
                if (!isEditable) {
                    event.preventDefault();
                    input.focus();
                }
            }
        });

        const initialQuery = getQueryParamFromURL();
        if (initialQuery && initialQuery.length > 0) {
            input.value = initialQuery;
            applyFilter(initialQuery);
        } else {
            updateNoResultsMessage(noResultsEl, images.length > 0);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initGalleryFiltering);
    } else {
        initGalleryFiltering();
    }
})();
