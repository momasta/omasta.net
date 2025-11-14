# omasta.net
My personal website  

Live URL: https://omasta.net(https://omasta.net)

Built using [Hugo](https://gohugo.io), an open-source static site generator.

Features:
- Multi-lingual
- Automatic light/dark mode switching
- Image gallery with [Photoswipe](https://github.com/dimsemenov/PhotoSwipe)
- A single RSS feed per language
- Custom Hugo theme based on [vimux/blank](https://github.com/vimux/blank/)
- Valid [HTML](https://validator.w3.org/nu/?doc=https%3A%2F%2Fmarek.omasta.net%2F), [CSS](https://jigsaw.w3.org/css-validator/validator?uri=marek.omasta.net&profile=css3svg&usermedium=all&warning=1&vextwarning=&lang=en) and [RSS](https://validator.w3.org/feed/check.cgi?url=https%3A%2F%2Fmarek.omasta.net%2Fposts%2Findex.xml).
- Optimised for Google's [PageSpeed Insights](https://pagespeed.web.dev)

## Image Gallery
A Hugo shortcode based on [this article by Christian Specht](https://www.codeproject.com/articles/Creating-an-Image-Gallery-with-Hugo-and-Lightbox2#comments-section).

- Source: [themes/blank/layouts/shortcodes/gallery.html](themes/blank/layouts/shortcodes/gallery.html)
- Live Demo: [omasta.net/memes/](https://omasta.net/memes/)

### Usage in Markdown Files:
`{{< gallery "memes" >}}`
  - Takes a  single parameter: subdirectory of assets/images 

### Modifications and Added Features:
- Replaced Lightbox2 with [Photoswipe](https://github.com/dimsemenov/PhotoSwipe).
- Captions based on filenames.
- Images sorted by date.
- WebP thumbnails
  - Short hashes for filenames.
  - Stored in a "t/" subdirectory, out of the way.
  - 1x and 2x variants for srcset.
  - loading="eager" for the first 12 thumbnails, lazy loading for the rest.
  - GIF support (uses the actual file as a thumbnail).
- Accessibility markup
- "?lightbox=" URL param to open an image on page load.
- Gallery Filter
  - Search-as-you-type image filtering.
  - Source: [assets/js/gallery-filter.js](assets/js/gallery-filter.js)
  - Fast and debounced.
  - Uses normalised strings to find matches, while giving priority to exact matches and "starts with".
  - Supports a ?q= URL param to prepopulate the search input.

## Thanks
### [Hugo](https://gohugo.io)
A fast open-source static site generator.

### [WebStorm](https://www.jetbrains.com/webstorm/)  
My favourite IDE, free for non-commercial use.

### [Photoswipe](https://github.com/dimsemenov/PhotoSwipe)
JavaScript image gallery for mobile and desktop, modular, framework independent.

### [vimux/blank](https://github.com/vimux/blank/)
Starter [Hugo](https://gohugo.io) theme.

### [KittyGiraudel/sass-boilerplate](https://github.com/KittyGiraudel/sass-boilerplate)
The base for my stylesheets.

### [Meteocons](https://demo.alessioatzeni.com/meteocons/)
SVG sun and moon icons I'm using for light/dark mode switching.