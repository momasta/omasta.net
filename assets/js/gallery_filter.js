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

    // ===== Utility: Text normalization =====
    function normalizeText(text) {
        return (text || "")
            .toLowerCase()
            .trim()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, ""); // strip accents/diacritics
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

    function makeUnfocusable(el) {
        const focusables = el.querySelectorAll(FOCUSABLE_SELECTOR);
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
        if ("inert" in el) {
            el.inert = true;
        }
    }

    function restoreFocusability(el) {
        const focusables = el.querySelectorAll(FOCUSABLE_SELECTOR);
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
        if ("inert" in el) {
            el.inert = false;
        }
    }

    // ===== Visibility management =====
    function showImage(el) {
        el.classList.remove("state-hidden");
        el.removeAttribute("aria-hidden");
        restoreFocusability(el);
    }

    function hideImage(el) {
        el.classList.add("state-hidden");
        el.setAttribute("aria-hidden", "true");
        makeUnfocusable(el);
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

        const altNorm = normalizeText(altRaw);
        const qNorm = normalizeText(qRaw);

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
    function setQueryParamInURL(q) {
        const url = new URL(window.location.href);
        if (q && q.length > 0) {
            url.searchParams.set("q", q);
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

    // ===== Initialization & main wiring =====
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
            const q = queryRaw || "";
            const trimmed = q.trim();

            if (trimmed.length === 0) {
                let anyVisible = false;
                originalOrder.forEach((el) => {
                    showImage(el);
                    galleryParent.appendChild(el);
                    anyVisible = true;
                });
                updateNoResultsMessage(noResultsEl, anyVisible);
                return;
            }

            const classified = images.map((el) => {
                const img = el.querySelector("img");
                const altText = img ? img.getAttribute("alt") || "" : "";
                const category = classifyImageByAlt(altText, trimmed);
                return {el, category};
            });

            let anyVisible = false;
            classified.forEach(({el, category}) => {
                if (category === MatchCategory.NO_MATCH) {
                    hideImage(el);
                } else {
                    showImage(el);
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
                .forEach(({el}) => galleryParent.appendChild(el));

            updateNoResultsMessage(noResultsEl, anyVisible);
        }

        const debouncedApply = debounce(() => applyFilter(input.value), 180);

        form.addEventListener("submit", (e) => {
            e.preventDefault();
            applyFilter(input.value);
            setQueryParamInURL(input.value.trim()); // URL updated only here
        });

        // ===== Input events apply filter (debounced) =====
        ["input", "keyup", "paste", "change", "search"].forEach((evt) => {
            input.addEventListener(evt, () => {
                debouncedApply();
                if (input.value.trim() === "") {
                    setQueryParamInURL(""); // clear q param when input is empty
                }
            });
        });

        // ===== Keyboard shortcuts =====
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                if (window.pswpLightbox && window.pswpLightbox.pswp && window.pswpLightbox.pswp.isOpen) {
                    // If PhotoSwipe is open, let it close first
                    return;
                }
                input.value = "";
                applyFilter("");
                setQueryParamInURL(""); // clear q param on Escape reset
                return;
            }
            if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) {
                const ae = document.activeElement;
                const isEditable =
                    ae &&
                    (ae.tagName === "INPUT" ||
                        ae.tagName === "TEXTAREA" ||
                        ae.isContentEditable);
                if (!isEditable) {
                    e.preventDefault();
                    input.focus();
                }
            }
        });

        const initialQ = getQueryParamFromURL();
        if (initialQ && initialQ.length > 0) {
            input.value = initialQ;
            applyFilter(initialQ);
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
