/* GL030 Vorschau-Lader: lädt alle aktuellen Design-Vorschauen (Karte im Feed, Vertrauenszeile im Kopf). */
(function(){var B='https://gl030.github.io/gl030-sitemap/live/',v=Date.now();['feed-karte.js','hero-trust.js'].forEach(function(f){var s=document.createElement('script');s.src=B+f+'?'+v;document.head.appendChild(s);});})();
