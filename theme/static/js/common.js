/**
 * Common JavaScript functionality shared across all pages
 * - Mobile menu toggle
 * - Scroll restoration for highlighted articles
 */
(function() {
  'use strict';

  // Simple tracking - just remember what we highlighted
  var alreadyHighlighted = null;
  var isHighlightingInProgress = false; // Prevent concurrent highlighting

  /**
   * Cancel any existing highlight for an article
   */
  function cancelExistingHighlight(articleId) {
    const targetElement = document.getElementById('article-' + articleId);
    if (targetElement) {
      targetElement.style.outline = '';
      targetElement.style.boxShadow = '';
      targetElement.style.transition = '';
    }
  }

  // Prevent browser's automatic scroll restoration
  if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
  }

  // Fast initialization - check immediately for highlights
  function simpleInit() {
    if (document.querySelector('[data-page-type="listing"]')) {
      // Check for highlights right away - no delay
      setTimeout(function() {
        checkArticleHighlightData();
      }, 100); // Just enough time for DOM to be ready
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', simpleInit);
  } else {
    simpleInit();
  }

  // Handle browser back/forward navigation (more strict)
  window.addEventListener('pageshow', function(event) {
    // Only run on actual back/forward navigation AND only if page was from cache
    if (event.persisted && document.querySelector('[data-page-type="listing"]')) {
      // Add a small delay to ensure the page is fully loaded
      setTimeout(function() {
        checkArticleHighlightData();
      }, 200);
    }
  });

  function initializePage() {
    // Keep this for compatibility but make it simple
    simpleInit();
  }

  /**
   * Checks for article highlight data and scrolls to article if present.
   */
  function checkArticleHighlightData() {
    // Prevent concurrent highlighting
    if (isHighlightingInProgress) {
      return;
    }

    const articleId = localStorage.getItem('article_highlight');

    if (articleId && articleId !== '' && articleId !== alreadyHighlighted) {
      isHighlightingInProgress = true;
      alreadyHighlighted = articleId;
      scrollToAndHighlightArticle(articleId);

      // Clear localStorage after a delay
      setTimeout(function() {
        localStorage.removeItem('article_highlight');
        isHighlightingInProgress = false;
      }, 2000);
    }
  }

  /**
   * Scrolls to an article and applies temporary highlight effect.
   */
  function scrollToAndHighlightArticle(articleId) {
    const targetElement = document.getElementById('article-' + articleId);

    if (!targetElement) {
      isHighlightingInProgress = false; // Reset flag if element not found
      return;
    }

    // Scroll to the article
    targetElement.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    });

    // Box shadow highlight - no layout shift
    setTimeout(function() {
      targetElement.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.3)';

      // Remove highlight after delay
      setTimeout(function() {
        targetElement.style.boxShadow = '';
      }, 1500);
    }, 500);
  }

})();