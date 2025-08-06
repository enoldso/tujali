/**
 * Tujali Telehealth - Cultural Loading Animations
 * Provides loading screens with animated cultural motifs from various African traditions
 */

class CulturalLoader {
  constructor() {
    this.motifs = [
      {
        name: 'sankofa',
        culture: 'Akan (Ghana)',
        description: 'The Sankofa symbol represents the importance of learning from the past',
        html: '<div class="loading-symbol-sankofa"></div>'
      },
      {
        name: 'maasai',
        culture: 'Maasai (Kenya/Tanzania)',
        description: 'Inspired by Maasai shield designs representing protection and strength',
        html: '<div class="loading-symbol-maasai"></div>'
      },
      {
        name: 'kente',
        culture: 'Ashanti (Ghana)',
        description: 'Based on Kente cloth patterns symbolizing wealth and prestige',
        html: `<div class="loading-symbol-kente">
                ${Array(9).fill('<div class="kente-cell"></div>').join('')}
               </div>`
      },
      {
        name: 'ndebele',
        culture: 'Ndebele (South Africa)',
        description: 'Inspired by Ndebele house painting traditions',
        html: `<div class="loading-symbol-ndebele">
                ${Array(4).fill('<div class="ndebele-line"></div>').join('')}
               </div>`
      }
    ];
    
    // Create the loader element if it doesn't exist
    this.createLoaderElement();
    
    // Bind methods to this
    this.show = this.show.bind(this);
    this.hide = this.hide.bind(this);
    this.setMessage = this.setMessage.bind(this);
  }
  
  createLoaderElement() {
    // Check if loader already exists
    if (document.getElementById('cultural-loader')) {
      return;
    }
    
    // Create loader container
    const loaderContainer = document.createElement('div');
    loaderContainer.id = 'cultural-loader';
    loaderContainer.className = 'loading-container';
    
    // Create inner content
    const loaderContent = document.createElement('div');
    loaderContent.className = 'loading-content';
    
    // Placeholder for animation
    const animationContainer = document.createElement('div');
    animationContainer.id = 'loader-animation';
    loaderContent.appendChild(animationContainer);
    
    // Loading text
    const loadingText = document.createElement('div');
    loadingText.id = 'loading-text';
    loadingText.className = 'loading-text';
    loadingText.textContent = 'Loading...';
    loaderContent.appendChild(loadingText);
    
    // Cultural description
    const culturalMessage = document.createElement('div');
    culturalMessage.id = 'cultural-message';
    culturalMessage.className = 'cultural-message';
    loaderContent.appendChild(culturalMessage);
    
    // Add content to container
    loaderContainer.appendChild(loaderContent);
    
    // Add to document
    document.body.appendChild(loaderContainer);
  }
  
  /**
   * Show the loading screen with a random cultural motif
   * @param {string} message - Optional message to display
   */
  show(message = 'Loading...') {
    // Get random motif
    const randomIndex = Math.floor(Math.random() * this.motifs.length);
    const motif = this.motifs[randomIndex];
    
    // Set the animation
    const animationContainer = document.getElementById('loader-animation');
    animationContainer.innerHTML = motif.html;
    
    // Set the message
    this.setMessage(message);
    
    // Set cultural information
    const culturalMessage = document.getElementById('cultural-message');
    culturalMessage.textContent = `${motif.culture}: ${motif.description}`;
    
    // Show the loader
    const loader = document.getElementById('cultural-loader');
    loader.classList.add('active');
    
    return motif.name;
  }
  
  /**
   * Hide the loading screen
   */
  hide() {
    const loader = document.getElementById('cultural-loader');
    loader.classList.remove('active');
  }
  
  /**
   * Update the loading message
   * @param {string} message - New message to display
   */
  setMessage(message) {
    const loadingText = document.getElementById('loading-text');
    loadingText.textContent = message;
  }
  
  /**
   * Show a specific cultural motif
   * @param {string} motifName - Name of the motif to display
   * @param {string} message - Optional message to display
   */
  showSpecific(motifName, message = 'Loading...') {
    const motif = this.motifs.find(m => m.name === motifName);
    if (!motif) {
      return this.show(message);
    }
    
    // Set the animation
    const animationContainer = document.getElementById('loader-animation');
    animationContainer.innerHTML = motif.html;
    
    // Set the message
    this.setMessage(message);
    
    // Set cultural information
    const culturalMessage = document.getElementById('cultural-message');
    culturalMessage.textContent = `${motif.culture}: ${motif.description}`;
    
    // Show the loader
    const loader = document.getElementById('cultural-loader');
    loader.classList.add('active');
    
    return motif.name;
  }
}

// Initialize the loader when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Create global instance
  window.culturalLoader = new CulturalLoader();
  
  // Add mini loaders to elements with data-loading="true"
  document.querySelectorAll('[data-loading="true"]').forEach(element => {
    const loaderEl = document.createElement('span');
    loaderEl.className = 'mini-loader';
    element.prepend(loaderEl);
  });
  
  // Add loading behavior to elements with data-ajax="true"
  document.querySelectorAll('[data-ajax="true"]').forEach(element => {
    element.addEventListener('click', (e) => {
      if (element.getAttribute('data-prevent-default') === 'true') {
        e.preventDefault();
      }
      
      const message = element.getAttribute('data-loading-message') || 'Loading...';
      const motif = element.getAttribute('data-loading-motif');
      
      if (motif) {
        window.culturalLoader.showSpecific(motif, message);
      } else {
        window.culturalLoader.show(message);
      }
      
      // If element has data-timeout, hide after timeout
      const timeout = element.getAttribute('data-timeout');
      if (timeout) {
        setTimeout(() => {
          window.culturalLoader.hide();
          
          // If has redirect, go there
          const redirect = element.getAttribute('data-redirect');
          if (redirect) {
            window.location.href = redirect;
          }
        }, parseInt(timeout));
      }
    });
  });
});

// Helper functions to use from other scripts
function showLoader(message) {
  if (window.culturalLoader) {
    return window.culturalLoader.show(message);
  }
}

function hideLoader() {
  if (window.culturalLoader) {
    window.culturalLoader.hide();
  }
}

function updateLoaderMessage(message) {
  if (window.culturalLoader) {
    window.culturalLoader.setMessage(message);
  }
}

// Loading Animation Manager for easier use in templates
class LoadingAnimationManager {
  constructor() {
    // Make sure underlying loader exists
    if (!window.culturalLoader) {
      window.culturalLoader = new CulturalLoader();
    }
  }
  
  /**
   * Show loading with specific cultural motif
   * @param {string} motif - The cultural motif to use (akan, maasai, etc.)
   * @param {string} message - Loading message to display
   */
  showLoading(motif, message) {
    if (window.culturalLoader) {
      return window.culturalLoader.showSpecific(motif, message);
    }
    return null;
  }
  
  /**
   * Hide the loading animation
   */
  hideLoading() {
    if (window.culturalLoader) {
      window.culturalLoader.hide();
    }
  }
  
  /**
   * Show a random cultural loading animation
   * @param {string} message - Loading message to display
   */
  showRandomLoading(message) {
    if (window.culturalLoader) {
      return window.culturalLoader.show(message);
    }
    return null;
  }
  
  /**
   * Update the loading message
   * @param {string} message - New message to display
   */
  updateMessage(message) {
    if (window.culturalLoader) {
      window.culturalLoader.setMessage(message);
    }
  }
}