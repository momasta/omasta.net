(() => {
    "use strict";

    // ===== Utility: Debounce =====
    function debounce(fn, delay = 180) {
        let t;
        return (...args) => {
            clearTimeout(t);
            t = setTimeout(() => fn(...args), delay);
        };
    }

    // ===== Utility: Text normalisation =====
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

    // ===== Focusable elements handling =====
    const FOCUSABLE_SELECTOR = [
        "a[href]",
        "button",
        "input",
        "textarea",
        "select",
        "[tabindex]"
    ].join(",");

    function makeUnfocusable(element) {
        const focusables = element.querySelectorAll(FOCUSABLE_SELECTOR);
        focusables.forEach((node) => {
            if (!node.hasAttribute("data-tabindex-original")) {
                const original = node.getAttribute("tabindex");
                if (original !== null) {
                    node.setAttribute("data-tabindex-original", original);
                } else {
                    node.setAttribute("data-tabindex-original", "");
                }
            }
            node.setAttribute("tabindex", "-1");
        });
        if ("inert" in element) {
            element.inert = true;
        }
    }

    function restoreFocusability(element) {
        const focusables = element.querySelectorAll(FOCUSABLE_SELECTOR);
        focusables.forEach((node) => {
            const original = node.getAttribute("data-tabindex-original");
            if (original !== null) {
                if (original === "") {
                    node.removeAttribute("tabindex");
                } else {
                    node.setAttribute("tabindex", original);
                }
                node.removeAttribute("data-tabindex-original");
            } else {
                if (node.getAttribute("tabindex") === "-1") {
                    node.removeAttribute("tabindex");
                }
            }
        });
        if ("inert" in element) {
            element.inert = false;
        }
    }

    // ===== Visibility management =====
    function showImage(element) {
        element.classList.remove("state-hidden");
        element.removeAttribute("aria-hidden");
        restoreFocusability(element);
    }

    function hideImage(element) {
        element.classList.add("state-hidden");
        element.setAttribute("aria-hidden", "true");
        makeUnfocusable(element);
    }

    // ===== Classification logic =====
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

        // Improved multi‑word match: allow partial substring matches
        const words = qNorm.split(/\s+/).filter(Boolean);
        if (words.length > 0) {
            const ok = words.every((w) => altNorm.includes(w));
            if (ok) return MatchCategory.MULTI_WORD;
        }

        return MatchCategory.NO_MATCH;
    }

    // ===== URL integration =====
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

    // ===== No results message =====
    function updateNoResultsMessage(noResultsEl, anyVisible) {
        if (!noResultsEl) return;
        if (anyVisible) {
            noResultsEl.setAttribute("aria-hidden", "true");
            noResultsEl.classList.add("state-hidden");
        } else {
            noResultsEl.removeAttribute("aria-hidden");
            noResultsEl.classList.remove("state-hidden");
        }
    }

    // ===== Initialisation =====
    function initGalleryFiltering() {
        const container = document.querySelector(".gallery");
        if (!container) throw new Error("Gallery container (.gallery) not found.");

        const form = document.querySelector("form");
        const input = document.querySelector(".gallery-filter-input");
        const images = Array.from(container.querySelectorAll(".gallery-image"));

        if (!form) throw new Error("Filter form inside .gallery not found.");
        if (!input) throw new Error("Filter input (.gallery-filter-input) inside .gallery not found.");
        if (images.length === 0) throw new Error("No .gallery-image elements found.");

        const galleryParent = images[0].parentElement;
        if (!galleryParent) throw new Error("Gallery parent element could not be determined.");

        const originalOrder = images.slice();
        images.forEach((imgWrap) => {
            if (!imgWrap.classList.contains("state-hidden")) {
                imgWrap.classList.remove("state-hidden");
                imgWrap.removeAttribute("aria-hidden");
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

        // ===== Input events apply filter (debounced) =====
        ["input", "keyup", "paste", "change", "search"].forEach((evt) => {
            input.addEventListener(evt, () => {
                debouncedApply();
                if (input.value.trim() === "") {
                    setQueryParamInURL(""); // Clear q param when input is empty
                }
            });
        });

        // ===== Keyboard shortcuts =====
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                if (window.pswpLightbox && window.pswpLightbox.pswp && window.pswpLightbox.pswp.isOpen) {
                    // If PhotoSwipe is open, let it close first
                    return;
                }
                input.value = "";
                applyFilter("");
                setQueryParamInURL(""); // Clear q param on Escape reset
                return;
            }
            if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey) {
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
