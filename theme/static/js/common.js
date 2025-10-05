/**
 * Common JavaScript functionality shared across all pages
 * - Mobile menu toggle
 * - Scroll restoration for highlighted articles
 */
(function() {
  'use strict';

  /**
   * Sets up mobile menu toggle functionality
   */
  function setupMobileMenu() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (!mobileMenuButton || !mobileMenu) return;

    // Toggle menu on button click
    mobileMenuButton.addEventListener('click', function() {
      mobileMenu.classList.toggle('hidden');
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
      if (!mobileMenu.contains(event.target) && !mobileMenuButton.contains(event.target)) {
        mobileMenu.classList.add('hidden');
      }
    });
  }

  /**
   * Restores scroll position and highlights an article based on URL parameters
   * Used when navigating back from detail pages, tag pages, or search results
   */
  function restoreScrollAndHighlight() {
    const urlParams = new URLSearchParams(window.location.search);
    const highlightArticleId = urlParams.get('highlight_article');

    if (!highlightArticleId) return;

    const targetElement = document.getElementById('article-' + highlightArticleId);
    if (!targetElement) return;

    // Wait a bit for the page to fully load, then scroll smoothly
    setTimeout(function() {
      targetElement.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });

      // Add a temporary highlight effect
      targetElement.style.transition = 'all 0.3s ease';
      targetElement.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.5)';

      // Remove the highlight after animation
      setTimeout(function() {
        targetElement.style.boxShadow = '';
      }, 2000);
    }, 100);

    // Clean up the URL parameter after highlighting
    const page = urlParams.get('page');
    const query = urlParams.get('q');
    const type = urlParams.get('type');

    let newUrl = window.location.pathname;
    const params = [];

    if (page) params.push('page=' + encodeURIComponent(page));
    if (query) params.push('q=' + encodeURIComponent(query));
    if (type) params.push('type=' + encodeURIComponent(type));

    if (params.length > 0) {
      newUrl += '?' + params.join('&');
    }

    window.history.replaceState({}, '', newUrl);
  }

  // Auto-initialize on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function() {
    setupMobileMenu();

    // Only run scroll restore on pages with articles
    if (document.querySelector('[id^="article-"]')) {
      restoreScrollAndHighlight();
    }
  });

  // Optional: Expose utilities for manual calls if needed
  window.NewsApp = window.NewsApp || {};
  window.NewsApp.scrollRestore = restoreScrollAndHighlight;
  window.NewsApp.setupMobileMenu = setupMobileMenu;

})();