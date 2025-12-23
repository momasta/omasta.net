# omasta.net
My Personal Website  

* Live URL: [omasta.net](https://omasta.net)
* Built using [Hugo](https://gohugo.io), an open-source static site generator.

## Table of Contents
- [Features](#features)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Image Gallery](#image-gallery)
    - [Usage](#usage)
    - [Modifications and Added Features](#modifications-and-added-features)
- [Thanks](#thanks)

## Features
* Multi-lingual site
* Automatic light/dark mode switching
* [Image gallery](#image-gallery) with [Photoswipe](https://github.com/dimsemenov/PhotoSwipe)
* A single RSS feed per language (limited to type: posts)
* Custom Hugo theme based on [vimux/blank](https://github.com/vimux/blank/)
* Valid [HTML](https://validator.w3.org/nu/?doc=https%3A%2F%2Fmarek.omasta.net%2F), [CSS](https://jigsaw.w3.org/css-validator/validator?uri=marek.omasta.net&profile=css3svg&usermedium=all&warning=1&vextwarning=&lang=en) and [RSS](https://validator.w3.org/feed/check.cgi?url=https%3A%2F%2Fmarek.omasta.net%2Fposts%2Findex.xml).
* Optimised for Google's [PageSpeed Insights](https://pagespeed.web.dev)

## Dependencies
- Hugo
  - Installed locally as a CLI tool.
  - Builds the site.
  - See [gohugoio/hugo on GitHub – Installation](https://github.com/gohugoio/hugo?tab=readme-ov-file#installation)
- PhotoSwipe
  - Downloaded manually to [assets/](assets):
    - [photoswipe.css](https://github.com/dimsemenov/PhotoSwipe/blob/master/dist/photoswipe.css)
    - [photoswipe.esm.min.js](https://github.com/dimsemenov/PhotoSwipe/blob/master/dist/photoswipe.esm.min.js)
    - [photoswipe-lightbox.esm.min.js](https://github.com/dimsemenov/PhotoSwipe/blob/master/dist/photoswipe-lightbox.esm.min.js)

## Installation
* [Install Hugo](https://github.com/gohugoio/hugo?tab=readme-ov-file#installation)

* Clone this repository:  
  ```Shell
  git clone https://github.com/momasta/omasta.net.git
  ```

* Enter the project directory:  
  ```Shell
  cd omasta.net
  ```

* Test the site locally:  
  ```Shell
  killall hugo; hugo server --minify --bind 0.0.0.0 --baseURL="http://$(hostname -f):1313" --port 1313
  ```

* Build the site:  
  ```Shell
  killall hugo; hugo --minify --cleanDestinationDir --gc
  ```

## Image Gallery
A Hugo shortcode based on [this article by Christian Specht](https://www.codeproject.com/articles/Creating-an-Image-Gallery-with-Hugo-and-Lightbox2#comments-section).

* Source: [themes/blank/layouts/_shortcodes/gallery.html](themes/blank/layouts/_shortcodes/gallery.html)
* Live Demo: [omasta.net/memes/](https://omasta.net/memes/)
* Live Demo (`.size-s`): [omasta.net/posts/tech-spurt-quotes/](https://omasta.net/posts/tech-spurt-quotes/)

### Usage
* In a Markdown file:  
  ```
  {{< gallery "memes" >}}
  ```
  
  ```
  {{< gallery "tech-spurt" "size-s" "name" >}}
  ```

* Arguments:
  * Path (optional)
    * Where to look for images
    * Supports: subpath of [assets/images/](assets/images)
    * Default: `"/"`
  * Class (optional)
    * Additional classes for `.gallery`
    * Space-separated, just like in HTML's `class=""` attribute.
    * Supports:
      * `size-s`: smaller thumbnails, no gallery filter input.
    * Default: `""`
  * Sort By (optional)
    * Supports: `"date"`, `"name"`
    * Default: `"date"`

### Modifications and Added Features
* Replaced Lightbox2 with [Photoswipe](https://github.com/dimsemenov/PhotoSwipe).
* Captions based on filenames.
* Images sorted by date.
* WebP thumbnails
  - Short hashes for filenames.
  - Stored in a `t/` subdirectory, out of the way.
  - 1x and 2x DPR variants for srcset.
  - Adds `loading="eager"` to the first 12 thumbnails, and `loading="lazy"` for the rest.
  - GIF support (uses the actual file as a thumbnail).
* Accessibility markup
* `?lightbox=` URL param to open an image on page load.
* Gallery Filter
  - Search-as-you-type image filtering.
  - Source: [assets/js/gallery-filter.js](assets/js/gallery-filter.js)
  - Fast and debounced.
  - Uses normalised strings to find matches, while giving priority to exact matches and "starts with".
  - Supports a `?q=` URL param to prepopulate the search input.

## Thanks
### Hugo
* A fast open-source static site generator.
* [Hugo Homepage and Docs](https://gohugo.io)
* [gohugoio/hugo on GitHub](https://github.com/gohugoio/hugo)

### WebStorm
* My favourite IDE.
* Free for non-commercial use.
* [WebStorm Homepage](https://www.jetbrains.com/webstorm/)

### PhotoSwipe
* JavaScript image gallery for mobile and desktop, modular, framework independent.
* [PhotoSwipe Homepage](https://photoswipe.com)
* [dimsemenov/PhotoSwipe on GitHub](https://github.com/dimsemenov/PhotoSwipe)

### ai.robots.txt
* A list of AI-related crawlers to block.
* Added to [robots.txt](themes/blank/layouts/robots.txt) and [.htaccess](static/.htaccess)
* My website was made by a human, for humans.  
  Not for half-baked hallucinating Cleverbot-like LLM chatbots, such as ChatGPT.
* [ai.robots.txt on GitHub](https://github.com/ai-robots-txt/ai.robots.txt)

### Blank
* Starter [Hugo](https://gohugo.io) theme.
* [Vimux/blank on GitHub](https://github.com/vimux/blank)

### sass-boilerplate
* The base for my stylesheets.
* [KittyGiraudel/sass-boilerplate on GitHub](https://github.com/KittyGiraudel/sass-boilerplate)

### Meteocons
* SVG sun and moon icons I'm using for light/dark mode switching.
* [Meteocons Homepage](https://demo.alessioatzeni.com/meteocons/)