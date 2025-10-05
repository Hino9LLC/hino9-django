/**
 * News search page functionality
 * - Radio button styling and interaction
 */
(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    const radioInputs = document.querySelectorAll('input[type="radio"]');

    if (radioInputs.length === 0) return;

    function updateRadioStyles() {
      radioInputs.forEach(function(input) {
        const indicator = input.parentElement.querySelector('.w-2.h-2');
        if (!indicator) return;

        if (input.checked) {
          indicator.style.opacity = '1';
          input.parentElement.classList.add('border-primary-500', 'bg-primary-600/20');
        } else {
          indicator.style.opacity = '0';
          input.parentElement.classList.remove('border-primary-500', 'bg-primary-600/20');
        }
      });
    }

    radioInputs.forEach(function(input) {
      input.addEventListener('change', updateRadioStyles);
    });

    // Initial styling
    updateRadioStyles();
  });

})();