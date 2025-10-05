/**
 * News detail page functionality
 * - Image size detection and responsive display
 */
(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    const articleImage = document.getElementById('article-image');

    if (!articleImage) return;

    // Wait for image to load to get natural dimensions
    articleImage.onload = function() {
      const naturalWidth = this.naturalWidth;
      const naturalHeight = this.naturalHeight;
      const minDisplayWidth = 300; // Minimum width threshold
      const minDisplayHeight = 200; // Minimum height threshold

      // If image is smaller than our thresholds, display at natural size
      if (naturalWidth < minDisplayWidth || naturalHeight < minDisplayHeight) {
        // Small image - display at natural size, centered
        this.style.width = naturalWidth + 'px';
        this.style.height = naturalHeight + 'px';
        this.style.maxWidth = 'none';
        this.style.maxHeight = 'none';
        this.style.objectFit = 'none';

        // Add some visual indication it's a small image
        this.style.border = '1px solid rgba(148, 163, 184, 0.3)';
        this.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1)';
      } else {
        // Normal sized image - apply responsive styling
        this.classList.add('w-full', 'h-auto', 'object-contain');
      }
    };

    // Handle case where image might already be loaded (cached)
    if (articleImage.complete && articleImage.naturalWidth > 0) {
      articleImage.onload();
    }
  });

})();