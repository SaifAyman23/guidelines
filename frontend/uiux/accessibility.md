# UI/UX Accessibility Guidelines

## Table of Contents

1. [Introduction to Web Accessibility](#introduction-to-web-accessibility)
2. [WCAG Guidelines](#wcag-guidelines)
3. [ARIA Labels and Roles](#aria-labels-and-roles)
4. [Keyboard Navigation](#keyboard-navigation)
5. [Screen Reader Support](#screen-reader-support)
6. [Color and Contrast](#color-and-contrast)
7. [Inclusive Design Principles](#inclusive-design-principles)
8. [Form Accessibility](#form-accessibility)
9. [Media and Content Accessibility](#media-and-content-accessibility)
10. [Testing and Validation](#testing-and-validation)
11. [Common Accessibility Patterns](#common-accessibility-patterns)

---

## Introduction to Web Accessibility

Web accessibility means designing and developing websites, tools, and technologies so that people with disabilities can use them. Specifically, people can perceive, understand, navigate, interact with, and contribute to the web.

### Why Accessibility Matters

**Legal and Ethical**
- Required by law in many countries (ADA, Section 508, EAA)
- Ensures equal access to information and services
- Fundamental human right

**Business Benefits**
- Expands market reach (15% of global population has disabilities)
- Improves SEO and findability
- Enhances overall user experience
- Reduces legal risk

**Technical Benefits**
- Better code quality and semantics
- Improved performance
- Enhanced mobile experience
- Future-proof designs

### Types of Disabilities to Consider

1. **Visual**: Blindness, low vision, color blindness
2. **Auditory**: Deafness, hard of hearing
3. **Motor**: Limited fine motor control, inability to use mouse
4. **Cognitive**: Learning disabilities, memory impairments, attention disorders
5. **Seizure**: Photosensitive epilepsy
6. **Speech**: Difficulty or inability to speak

---

## WCAG Guidelines

The Web Content Accessibility Guidelines (WCAG) are organized around four core principles, known as POUR:

### Perceivable

Information and UI components must be presentable to users in ways they can perceive.

#### 1.1 Text Alternatives

Provide text alternatives for non-text content.

```html
<!-- Images -->
<img src="chart.png" alt="Sales growth chart showing 25% increase in Q4 2024">

<!-- Decorative images -->
<img src="decorative-line.png" alt="" role="presentation">

<!-- Icons with labels -->
<button aria-label="Close dialog">
  <span class="icon-close" aria-hidden="true"></span>
</button>

<!-- Complex images -->
<figure>
  <img src="complex-diagram.png" alt="System architecture diagram">
  <figcaption>
    <details>
      <summary>Detailed description</summary>
      <p>The system consists of three layers: presentation, business logic, and data access...</p>
    </details>
  </figcaption>
</figure>
```

#### 1.2 Time-Based Media

Provide alternatives for time-based media (audio, video).

```html
<!-- Video with captions and transcript -->
<video controls>
  <source src="presentation.mp4" type="video/mp4">
  <track kind="captions" src="captions.vtt" srclang="en" label="English">
  <track kind="descriptions" src="descriptions.vtt" srclang="en">
</video>

<details>
  <summary>Video Transcript</summary>
  <p>Transcript content here...</p>
</details>

<!-- Audio alternative -->
<audio controls>
  <source src="podcast.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>
<a href="podcast-transcript.html">Read transcript</a>
```

#### 1.3 Adaptable Content

Create content that can be presented in different ways without losing information.

```html
<!-- Semantic HTML structure -->
<article>
  <header>
    <h1>Article Title</h1>
    <p class="byline">By Author Name</p>
    <time datetime="2024-01-15">January 15, 2024</time>
  </header>
  
  <section>
    <h2>Section Heading</h2>
    <p>Content...</p>
  </section>
  
  <aside>
    <h3>Related Information</h3>
  </aside>
</article>

<!-- Proper table structure -->
<table>
  <caption>Quarterly Sales Data</caption>
  <thead>
    <tr>
      <th scope="col">Quarter</th>
      <th scope="col">Revenue</th>
      <th scope="col">Growth</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Q1 2024</th>
      <td>$2.5M</td>
      <td>15%</td>
    </tr>
  </tbody>
</table>

<!-- Form labels and structure -->
<form>
  <fieldset>
    <legend>Personal Information</legend>
    
    <label for="name">Full Name</label>
    <input type="text" id="name" name="name" required>
    
    <label for="email">Email Address</label>
    <input type="email" id="email" name="email" required>
  </fieldset>
</form>
```

#### 1.4 Distinguishable

Make it easier for users to see and hear content.

```css
/* Sufficient color contrast */
.text-primary {
  color: #1a1a1a; /* Against white: 16.1:1 */
  background-color: #ffffff;
}

.text-secondary {
  color: #4a4a4a; /* Against white: 9.7:1 */
  background-color: #ffffff;
}

/* Don't rely solely on color */
.error-message {
  color: #d32f2f;
  border-left: 4px solid #d32f2f; /* Visual indicator */
}

.error-message::before {
  content: '⚠ '; /* Icon indicator */
}

/* Text resize support */
html {
  font-size: 16px; /* Base size */
}

body {
  font-size: 1rem; /* Scales with user preferences */
  line-height: 1.5; /* Minimum 1.5 for body text */
}

/* Focus indicators */
a:focus,
button:focus,
input:focus {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}

/* No content loss on zoom to 200% */
.container {
  max-width: 100%;
  overflow-x: auto;
}
```

### Operable

UI components and navigation must be operable.

#### 2.1 Keyboard Accessible

All functionality available via keyboard.

```html
<!-- Custom interactive elements need tabindex and keyboard handlers -->
<div 
  role="button" 
  tabindex="0"
  onclick="handleClick()"
  onkeydown="handleKeyDown(event)">
  Custom Button
</div>

<script>
function handleKeyDown(event) {
  // Space or Enter triggers button
  if (event.key === ' ' || event.key === 'Enter') {
    event.preventDefault();
    handleClick();
  }
}
</script>

<!-- Skip navigation link -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px;
  text-decoration: none;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
</style>

<!-- Keyboard trap prevention in modals -->
<div role="dialog" aria-modal="true">
  <button class="close" aria-label="Close">×</button>
  <h2>Modal Title</h2>
  <p>Content...</p>
  <button>Action</button>
</div>

<script>
// Trap focus within modal
const modal = document.querySelector('[role="dialog"]');
const focusableElements = modal.querySelectorAll(
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
);
const firstFocusable = focusableElements[0];
const lastFocusable = focusableElements[focusableElements.length - 1];

modal.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    if (e.shiftKey && document.activeElement === firstFocusable) {
      e.preventDefault();
      lastFocusable.focus();
    } else if (!e.shiftKey && document.activeElement === lastFocusable) {
      e.preventDefault();
      firstFocusable.focus();
    }
  }
});
</script>
```

#### 2.2 Enough Time

Provide users enough time to read and use content.

```html
<!-- Adjustable time limits -->
<div role="alert" aria-live="polite">
  <p>Your session will expire in <span id="timer">5:00</span></p>
  <button onclick="extendSession()">Extend Session</button>
</div>

<!-- Pause, stop, or hide moving content -->
<div class="carousel" aria-roledescription="carousel">
  <button aria-label="Pause carousel">⏸</button>
  <button aria-label="Play carousel">▶</button>
  <!-- Carousel content -->
</div>

<!-- No automatic refresh without warning -->
<meta http-equiv="refresh" content="300; url=timeout.html">
<!-- Better: Warn user before refresh -->
```

#### 2.3 Seizures and Physical Reactions

Don't design content that could cause seizures.

```css
/* No flashing more than 3 times per second */
.safe-animation {
  animation: fade 2s ease-in-out; /* Slow, gentle animation */
}

@keyframes fade {
  from { opacity: 0.8; }
  to { opacity: 1; }
}

/* Respect prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### 2.4 Navigable

Provide ways to help users navigate and find content.

```html
<!-- Descriptive page titles -->
<title>Contact Us - Acme Corporation</title>

<!-- Logical focus order -->
<form>
  <input type="text" tabindex="1"> <!-- Don't use positive tabindex -->
  <input type="email" tabindex="2">
  <button tabindex="3">Submit</button>
</form>

<!-- Better: Natural DOM order -->
<form>
  <input type="text">
  <input type="email">
  <button>Submit</button>
</form>

<!-- Descriptive link text -->
<!-- Bad -->
<a href="report.pdf">Click here</a>

<!-- Good -->
<a href="report.pdf">Download Q4 2024 Financial Report (PDF, 2.3 MB)</a>

<!-- Multiple navigation methods -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</nav>

<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/products">Products</a></li>
    <li aria-current="page">Laptops</li>
  </ol>
</nav>

<!-- Headings for structure -->
<h1>Main Page Title</h1>
  <h2>Section Title</h2>
    <h3>Subsection</h3>
    <h3>Another Subsection</h3>
  <h2>Another Section</h2>
```

### Understandable

Information and UI operation must be understandable.

#### 3.1 Readable

Make text content readable and understandable.

```html
<!-- Language declaration -->
<html lang="en">

<!-- Language changes within content -->
<p>The French word for hello is <span lang="fr">bonjour</span>.</p>

<!-- Unusual words explained -->
<p>
  The <dfn>hypotenuse</dfn> (the longest side of a right triangle) 
  can be calculated using the Pythagorean theorem.
</p>

<!-- Abbreviations -->
<p>
  The <abbr title="World Wide Web Consortium">W3C</abbr> 
  develops web standards.
</p>
```

#### 3.2 Predictable

Web pages appear and operate in predictable ways.

```html
<!-- Consistent navigation -->
<header>
  <nav aria-label="Main navigation">
    <!-- Same navigation on every page in same order -->
  </nav>
</header>

<!-- Consistent identification -->
<!-- Search icon means search everywhere -->
<button aria-label="Search">
  <svg class="icon-search" aria-hidden="true">...</svg>
</button>

<!-- No context changes on focus -->
<input type="text" onfocus="showHelp()">  <!-- Good: Shows help -->
<input type="text" onfocus="submitForm()"> <!-- Bad: Unexpected action -->

<!-- Warn before context changes -->
<a href="external-site.com" target="_blank" rel="noopener">
  Visit external site
  <span class="visually-hidden">(opens in new window)</span>
</a>
```

#### 3.3 Input Assistance

Help users avoid and correct mistakes.

```html
<!-- Error identification -->
<form>
  <label for="email">
    Email Address
    <span aria-live="polite" class="error" id="email-error"></span>
  </label>
  <input 
    type="email" 
    id="email" 
    aria-describedby="email-error email-help"
    aria-invalid="false">
  <span id="email-help" class="help-text">
    We'll never share your email
  </span>
</form>

<script>
function validateEmail(input) {
  const errorEl = document.getElementById('email-error');
  if (!input.value.includes('@')) {
    input.setAttribute('aria-invalid', 'true');
    errorEl.textContent = 'Please enter a valid email address';
  } else {
    input.setAttribute('aria-invalid', 'false');
    errorEl.textContent = '';
  }
}
</script>

<!-- Labels and instructions -->
<label for="password">
  Password
  <span class="required" aria-label="required">*</span>
</label>
<input 
  type="password" 
  id="password" 
  aria-describedby="password-requirements"
  required>
<div id="password-requirements">
  Must be at least 8 characters with one number and one special character
</div>

<!-- Error prevention for legal/financial actions -->
<form>
  <h2>Delete Account</h2>
  <p>This action cannot be undone.</p>
  
  <label for="confirm">
    Type "DELETE" to confirm
  </label>
  <input type="text" id="confirm">
  
  <button 
    type="submit" 
    disabled 
    id="delete-btn">
    Delete Account
  </button>
</form>

<!-- Confirmation for reversible actions -->
<button onclick="showConfirmation()">Delete Item</button>

<div role="alertdialog" aria-labelledby="confirm-title" hidden>
  <h2 id="confirm-title">Confirm Deletion</h2>
  <p>Are you sure you want to delete this item?</p>
  <button onclick="confirmDelete()">Yes, Delete</button>
  <button onclick="cancelDelete()">Cancel</button>
</div>
```

### Robust

Content must be robust enough to be interpreted by assistive technologies.

#### 4.1 Compatible

Maximize compatibility with current and future tools.

```html
<!-- Valid, semantic HTML -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
</head>
<body>
  <!-- Well-formed, nested properly -->
  <main>
    <article>
      <h1>Title</h1>
      <p>Content</p>
    </article>
  </main>
</body>
</html>

<!-- Unique IDs -->
<label for="username">Username</label>
<input type="text" id="username">

<!-- Not: Multiple elements with same ID -->

<!-- Status messages -->
<div role="status" aria-live="polite">
  <p>Item added to cart</p>
</div>

<div role="alert" aria-live="assertive">
  <p>Error: Payment failed</p>
</div>
```

---

## ARIA Labels and Roles

ARIA (Accessible Rich Internet Applications) enhances HTML accessibility for dynamic content and custom widgets.

### ARIA Principles

**First Rule of ARIA**: Don't use ARIA if you can use native HTML.

```html
<!-- Bad: Custom button with ARIA -->
<div role="button" tabindex="0" onclick="submit()">Submit</div>

<!-- Good: Native button -->
<button onclick="submit()">Submit</button>

<!-- Bad: Custom checkbox -->
<div role="checkbox" aria-checked="false"></div>

<!-- Good: Native checkbox -->
<input type="checkbox">
```

**Second Rule**: Don't change native semantics unless you really have to.

```html
<!-- Bad -->
<h1 role="button">Don't do this</h1>

<!-- Good -->
<h1>Heading</h1>
<button>Button</button>
```

### Common ARIA Roles

```html
<!-- Landmark Roles -->
<header role="banner">
  <nav role="navigation" aria-label="Main">...</nav>
</header>

<main role="main">...</main>

<aside role="complementary">...</aside>

<footer role="contentinfo">...</footer>

<!-- Widget Roles -->
<div role="dialog" aria-labelledby="dialog-title" aria-modal="true">
  <h2 id="dialog-title">Dialog Title</h2>
  <!-- Content -->
</div>

<div role="tablist">
  <button role="tab" aria-selected="true" aria-controls="panel1">Tab 1</button>
  <button role="tab" aria-selected="false" aria-controls="panel2">Tab 2</button>
</div>
<div role="tabpanel" id="panel1">Panel 1 content</div>
<div role="tabpanel" id="panel2" hidden>Panel 2 content</div>

<ul role="tree">
  <li role="treeitem" aria-expanded="true">
    Parent Item
    <ul role="group">
      <li role="treeitem">Child Item</li>
    </ul>
  </li>
</ul>

<!-- Live Regions -->
<div role="status" aria-live="polite" aria-atomic="true">
  Processing request...
</div>

<div role="alert" aria-live="assertive">
  Error: Invalid input
</div>

<div aria-live="polite" aria-relevant="additions">
  <!-- Announces new items added -->
</div>
```

### ARIA Properties and States

```html
<!-- aria-label: Provides accessible name -->
<button aria-label="Close dialog">
  <span class="icon-x" aria-hidden="true">×</span>
</button>

<!-- aria-labelledby: References element(s) for label -->
<section aria-labelledby="section-heading">
  <h2 id="section-heading">Products</h2>
  <!-- Content -->
</section>

<!-- aria-describedby: Provides additional description -->
<input 
  type="text" 
  aria-labelledby="name-label" 
  aria-describedby="name-help">
<label id="name-label">Full Name</label>
<span id="name-help">First and last name</span>

<!-- aria-expanded: Indicates expandable element state -->
<button 
  aria-expanded="false" 
  aria-controls="menu">
  Menu
</button>
<ul id="menu" hidden>
  <li>Item 1</li>
</ul>

<!-- aria-selected: Current selection in group -->
<div role="tablist">
  <button role="tab" aria-selected="true">Active Tab</button>
  <button role="tab" aria-selected="false">Inactive Tab</button>
</div>

<!-- aria-current: Current item in set -->
<nav>
  <a href="/" aria-current="page">Home</a>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
</nav>

<!-- aria-hidden: Hides from assistive tech -->
<span aria-hidden="true" class="decorative-icon">🎉</span>

<!-- aria-invalid: Indicates validation state -->
<input 
  type="email" 
  aria-invalid="true" 
  aria-errormessage="email-error">
<span id="email-error" role="alert">Invalid email format</span>

<!-- aria-required: Indicates required field -->
<input type="text" aria-required="true" required>

<!-- aria-disabled: Indicates disabled state -->
<button aria-disabled="true" disabled>Submit</button>

<!-- aria-busy: Loading state -->
<div aria-busy="true">
  <span class="spinner" aria-label="Loading"></span>
</div>

<!-- aria-pressed: Toggle button state -->
<button aria-pressed="false" onclick="toggleBold()">
  <strong>B</strong> Bold
</button>

<!-- aria-haspopup: Indicates popup type -->
<button aria-haspopup="menu" aria-expanded="false">
  Options
</button>

<!-- aria-controls: Identifies controlled element -->
<button 
  aria-expanded="false" 
  aria-controls="accordion-panel">
  Expand Section
</button>
<div id="accordion-panel" hidden>Content</div>
```

### ARIA Live Regions

```html
<!-- Polite: Announces when user is idle -->
<div aria-live="polite">
  <p id="status">Ready</p>
</div>

<!-- Assertive: Announces immediately -->
<div role="alert" aria-live="assertive">
  <p>Error: Connection lost</p>
</div>

<!-- Atomic: Announces entire region -->
<div aria-live="polite" aria-atomic="true">
  <span id="time">2:30</span> remaining
</div>

<!-- Relevant: What changes to announce -->
<ul aria-live="polite" aria-relevant="additions removals">
  <!-- Announces when items added/removed -->
</ul>

<!-- Status updates -->
<div role="status" aria-live="polite">
  <p>Saving... <span class="visually-hidden">Please wait</span></p>
</div>

<script>
// Update status
const status = document.querySelector('[role="status"]');
status.textContent = 'Saved successfully';
// Screen reader announces the change
</script>
```

---

## Keyboard Navigation

### Tab Order and Focus Management

```html
<!-- Natural tab order (no tabindex) -->
<form>
  <input type="text" placeholder="First">  <!-- Tab stop 1 -->
  <input type="text" placeholder="Second"> <!-- Tab stop 2 -->
  <button>Submit</button>                  <!-- Tab stop 3 -->
</form>

<!-- tabindex values -->
<!-- tabindex="0": Includes in natural tab order -->
<div role="button" tabindex="0">Custom Button</div>

<!-- tabindex="-1": Programmatically focusable, not in tab order -->
<div id="target" tabindex="-1">Jump target</div>

<!-- tabindex="1+" : AVOID - Creates unpredictable tab order -->

<!-- Focus management in SPA navigation -->
<script>
function navigateTo(page) {
  // Load new page content
  loadContent(page);
  
  // Move focus to main content
  const main = document.querySelector('main');
  main.setAttribute('tabindex', '-1');
  main.focus();
  
  // Update page title for screen readers
  document.title = `${page} - Site Name`;
}
</script>

<!-- Skip links -->
<a href="#main" class="skip-link">Skip to main content</a>
<a href="#navigation" class="skip-link">Skip to navigation</a>

<nav id="navigation">...</nav>
<main id="main">...</main>
```

### Keyboard Event Handling

```javascript
// Standard keyboard interactions
const button = document.querySelector('[role="button"]');

button.addEventListener('keydown', (e) => {
  // Enter or Space activates buttons
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    button.click();
  }
});

// Arrow key navigation for lists
const listbox = document.querySelector('[role="listbox"]');
const options = listbox.querySelectorAll('[role="option"]');
let currentIndex = 0;

listbox.addEventListener('keydown', (e) => {
  switch(e.key) {
    case 'ArrowDown':
      e.preventDefault();
      currentIndex = Math.min(currentIndex + 1, options.length - 1);
      options[currentIndex].focus();
      break;
      
    case 'ArrowUp':
      e.preventDefault();
      currentIndex = Math.max(currentIndex - 1, 0);
      options[currentIndex].focus();
      break;
      
    case 'Home':
      e.preventDefault();
      currentIndex = 0;
      options[0].focus();
      break;
      
    case 'End':
      e.preventDefault();
      currentIndex = options.length - 1;
      options[currentIndex].focus();
      break;
  }
});

// Escape key to close modals/menus
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
  }
});

// Tab trapping in modal
function trapFocus(element) {
  const focusableElements = element.querySelectorAll(
    'a[href], button, textarea, input, select, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];
  
  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  });
}
```

### Focus Styles

```css
/* Visible focus indicators */
:focus {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}

/* Different styles for different elements */
button:focus {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}

input:focus,
select:focus,
textarea:focus {
  outline: 2px solid #0066cc;
  outline-offset: 0;
  border-color: #0066cc;
}

a:focus {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
  background-color: #e6f2ff;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  :focus {
    outline: 4px solid currentColor;
    outline-offset: 4px;
  }
}

/* Never remove focus outlines globally */
/* BAD: Don't do this */
*:focus {
  outline: none;
}

/* OK: Remove outline only if providing alternative */
button:focus {
  outline: none;
  box-shadow: 0 0 0 3px #0066cc;
}

/* Focus-visible for mouse vs keyboard */
button:focus-visible {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}

button:focus:not(:focus-visible) {
  outline: none;
}
```

---

## Screen Reader Support

### Screen Reader Only Content

```css
/* Visually hidden but available to screen readers */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Visually hidden but focusable (skip links) */
.visually-hidden-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

```html
<!-- Additional context for screen readers -->
<button>
  <span aria-hidden="true">×</span>
  <span class="visually-hidden">Close dialog</span>
</button>

<!-- Decorative content hidden from screen readers -->
<div class="card">
  <img src="decorative.png" alt="" role="presentation">
  <h3>Card Title</h3>
</div>

<!-- Icon with text label -->
<button>
  <svg aria-hidden="true" class="icon">...</svg>
  Save
</button>

<!-- Icon without text label -->
<button aria-label="Save document">
  <svg aria-hidden="true" class="icon">...</svg>
</button>
```

### Announcing Dynamic Content

```html
<!-- Status messages -->
<div role="status" aria-live="polite" class="visually-hidden">
  <span id="announcements"></span>
</div>

<script>
function announce(message) {
  const announcer = document.getElementById('announcements');
  announcer.textContent = message;
  
  // Clear after announcement
  setTimeout(() => {
    announcer.textContent = '';
  }, 1000);
}

// Usage
announce('Item added to cart');
announce('File uploaded successfully');
</script>

<!-- Loading states -->
<button aria-live="polite" aria-busy="false" id="submit-btn">
  <span class="btn-text">Submit</span>
</button>

<script>
function submitForm() {
  const btn = document.getElementById('submit-btn');
  btn.setAttribute('aria-busy', 'true');
  btn.disabled = true;
  btn.querySelector('.btn-text').textContent = 'Submitting...';
  
  // After submission
  setTimeout(() => {
    btn.setAttribute('aria-busy', 'false');
    btn.querySelector('.btn-text').textContent = 'Submitted';
  }, 2000);
}
</script>
```

### Meaningful Reading Order

```html
<!-- Visual order matches DOM order -->
<article>
  <h2>Article Title</h2>        <!-- Read first -->
  <p class="meta">Published...</p> <!-- Read second -->
  <p>Content...</p>               <!-- Read third -->
</article>

<!-- Flexbox/Grid doesn't affect reading order -->
<style>
.visual-reorder {
  display: flex;
  flex-direction: column-reverse; /* Visual change only */
}
</style>

<!-- DOM order is what screen readers follow -->
<div class="visual-reorder">
  <p>First in DOM, last visually</p>
  <h2>Second in DOM, first visually</h2>
</div>

<!-- Solution: Match DOM to desired reading order -->
<div>
  <h2>First in DOM and visually</h2>
  <p>Second in DOM and visually</p>
</div>
```

---

## Color and Contrast

### WCAG Color Contrast Requirements

**Level AA (Minimum)**
- Normal text: 4.5:1
- Large text (18pt+/14pt+ bold): 3:1
- UI components: 3:1

**Level AAA (Enhanced)**
- Normal text: 7:1
- Large text: 4.5:1

```css
/* Passing examples */
.aa-normal-text {
  color: #595959;            /* 7:1 against white */
  background-color: #ffffff;
}

.aa-large-text {
  color: #767676;            /* 4.54:1 against white */
  background-color: #ffffff;
  font-size: 24px;
}

.aaa-text {
  color: #4d4d4d;            /* 9:1 against white */
  background-color: #ffffff;
}

/* UI component contrast */
.button {
  background-color: #0066cc; /* 4.54:1 against white */
  color: #ffffff;
  border: 2px solid #0052a3; /* 6.5:1 against white */
}

.input-field {
  border: 1px solid #757575; /* 4.54:1 against white */
  background-color: #ffffff;
  color: #000000;
}

/* Focus indicators */
.element:focus {
  outline: 3px solid #0066cc; /* 4.54:1 against white */
}
```

### Don't Rely on Color Alone

```html
<!-- Bad: Color only -->
<style>
.error { color: red; }
.success { color: green; }
</style>
<p class="error">Error message</p>
<p class="success">Success message</p>

<!-- Good: Color plus icon/text -->
<style>
.error {
  color: #d32f2f;
  border-left: 4px solid #d32f2f;
}
.error::before {
  content: '⚠ Error: ';
  font-weight: bold;
}

.success {
  color: #2e7d32;
  border-left: 4px solid #2e7d32;
}
.success::before {
  content: '✓ Success: ';
  font-weight: bold;
}
</style>

<!-- Form validation -->
<label for="email">
  Email
  <span class="required" aria-label="required">*</span>
</label>
<input 
  type="email" 
  id="email" 
  aria-invalid="true"
  aria-describedby="email-error">
<span id="email-error" class="error-message">
  <span class="icon" aria-hidden="true">⚠</span>
  Please enter a valid email address
</span>

<!-- Charts and graphs -->
<svg role="img" aria-labelledby="chart-title chart-desc">
  <title id="chart-title">Sales Data</title>
  <desc id="chart-desc">
    Bar chart showing sales from Q1 to Q4...
    <!-- Detailed description of data -->
  </desc>
  <!-- Use patterns in addition to colors -->
  <rect fill="#0066cc" style="pattern: diagonal-lines" />
  <rect fill="#ff6b6b" style="pattern: dots" />
</svg>
```

### Color Blindness Considerations

```css
/* Use sufficient differentiation */
/* Red-green color blindness affects ~8% of men */

/* Bad: Red and green for different states */
.active { background-color: #00ff00; }
.inactive { background-color: #ff0000; }

/* Good: Different hues + brightness + patterns */
.active {
  background-color: #2196f3; /* Blue */
  border: 2px solid #1976d2;
}

.inactive {
  background-color: #f5f5f5; /* Light gray */
  border: 2px dashed #9e9e9e;
}

/* Color palettes for accessibility */
:root {
  /* Colorblind-safe palette */
  --color-blue: #0173B2;
  --color-orange: #DE8F05;
  --color-green: #029E73;
  --color-purple: #CC78BC;
  --color-red: #CA3542;
  --color-brown: #846836;
}
```

---

## Inclusive Design Principles

### 1. Provide Equivalent Experiences

```html
<!-- Video with multiple alternatives -->
<video controls>
  <source src="video.mp4">
  <track kind="captions" src="captions.vtt">
  <track kind="descriptions" src="audio-description.vtt">
</video>

<details>
  <summary>Video Transcript</summary>
  <p>Full text transcript...</p>
</details>

<a href="slides.pdf">Download presentation slides (PDF)</a>
```

### 2. Consider Situation

```css
/* High contrast mode */
@media (prefers-contrast: high) {
  body {
    background-color: #000000;
    color: #ffffff;
  }
  
  button {
    border: 2px solid currentColor;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  body {
    background-color: #1a1a1a;
    color: #e0e0e0;
  }
}

/* Touch-friendly targets on mobile */
@media (pointer: coarse) {
  button,
  a,
  input {
    min-height: 44px;
    min-width: 44px;
    padding: 12px;
  }
}
```

### 3. Be Consistent

```html
<!-- Consistent navigation across pages -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/" aria-current="page">Home</a></li>
    <li><a href="/products">Products</a></li>
    <li><a href="/about">About</a></li>
    <li><a href="/contact">Contact</a></li>
  </ul>
</nav>

<!-- Consistent form patterns -->
<div class="form-group">
  <label for="field">
    Field Label
    <span class="required" aria-label="required">*</span>
  </label>
  <input type="text" id="field" required aria-describedby="field-help">
  <span id="field-help" class="help-text">Helper text</span>
  <span class="error-message" role="alert"></span>
</div>
```

### 4. Give Control

```html
<!-- User controls for media -->
<video controls>
  <source src="video.mp4">
</video>

<!-- Pause/play for carousels -->
<div class="carousel">
  <button aria-label="Pause carousel">⏸</button>
  <!-- Carousel content -->
</div>

<!-- Adjustable text size -->
<div class="text-controls">
  <button onclick="decreaseTextSize()">A-</button>
  <button onclick="resetTextSize()">A</button>
  <button onclick="increaseTextSize()">A+</button>
</div>

<!-- Skip animations -->
<button onclick="skipAnimation()">
  Skip animation
</button>
```

### 5. Offer Choice

```html
<!-- Multiple ways to complete tasks -->
<!-- Via mouse -->
<button onclick="save()">Save</button>

<!-- Via keyboard -->
<button onclick="save()" accesskey="s">
  Save (Ctrl+S)
</button>

<!-- Via voice -->
<button onclick="save()" aria-label="Save document">
  Save
</button>

<!-- Multiple navigation methods -->
<nav aria-label="Primary">
  <ul>
    <li><a href="/products">Products</a></li>
  </ul>
</nav>

<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/category">Category</a></li>
    <li aria-current="page">Product</li>
  </ol>
</nav>

<form role="search">
  <input type="search" aria-label="Search">
  <button>Search</button>
</form>
```

---

## Form Accessibility

### Label Association

```html
<!-- Explicit labels -->
<label for="username">Username</label>
<input type="text" id="username" name="username">

<!-- Implicit labels -->
<label>
  Email
  <input type="email" name="email">
</label>

<!-- Multiple inputs need individual labels -->
<fieldset>
  <legend>Date of Birth</legend>
  <label for="month">Month</label>
  <select id="month"></select>
  
  <label for="day">Day</label>
  <select id="day"></select>
  
  <label for="year">Year</label>
  <select id="year"></select>
</fieldset>
```

### Form Instructions and Help

```html
<!-- General instructions -->
<form>
  <p id="form-instructions">
    All fields marked with * are required
  </p>
  
  <div class="form-group">
    <label for="password">
      Password
      <span class="required" aria-label="required">*</span>
    </label>
    <input 
      type="password" 
      id="password"
      aria-describedby="password-requirements"
      required>
    <div id="password-requirements" class="help-text">
      Must be at least 8 characters with one number
    </div>
  </div>
</form>

<!-- Contextual help -->
<label for="routing">
  Routing Number
  <button 
    type="button"
    aria-label="What is a routing number?"
    onclick="showHelp()">
    ?
  </button>
</label>
<input type="text" id="routing">
```

### Error Handling

```html
<!-- Error summary -->
<div role="alert" aria-labelledby="error-heading" class="error-summary">
  <h2 id="error-heading">There are 2 errors in this form</h2>
  <ul>
    <li><a href="#email">Email address is invalid</a></li>
    <li><a href="#password">Password is too short</a></li>
  </ul>
</div>

<!-- Individual field errors -->
<div class="form-group">
  <label for="email">Email Address</label>
  <input 
    type="email" 
    id="email"
    aria-invalid="true"
    aria-describedby="email-error">
  <span id="email-error" class="error-message" role="alert">
    Please enter a valid email address
  </span>
</div>

<!-- Success messages -->
<div role="status" aria-live="polite">
  <p>Form submitted successfully</p>
</div>
```

### Required Fields

```html
<!-- Visual and programmatic indication -->
<label for="name">
  Full Name
  <span class="required" aria-label="required">*</span>
</label>
<input type="text" id="name" required aria-required="true">

<!-- Required fieldset -->
<fieldset required>
  <legend>
    Contact Information
    <span class="required" aria-label="required">*</span>
  </legend>
  <!-- Fields -->
</fieldset>
```

---

## Testing and Validation

### Automated Testing Tools

```bash
# npm packages
npm install --save-dev @axe-core/cli pa11y eslint-plugin-jsx-a11y

# Run axe
axe https://example.com

# Run pa11y
pa11y https://example.com
```

```javascript
// Jest + jest-axe
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

test('should have no accessibility violations', async () => {
  const { container } = render(<App />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});

// Cypress + cypress-axe
describe('Accessibility', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.injectAxe();
  });
  
  it('should have no detectable a11y violations', () => {
    cy.checkA11y();
  });
});
```

### Manual Testing Checklist

- [ ] Keyboard only navigation (Tab, Shift+Tab, Arrow keys, Enter, Escape)
- [ ] Screen reader testing (NVDA, JAWS, VoiceOver)
- [ ] Color contrast checker
- [ ] Zoom to 200% without horizontal scrolling
- [ ] Browser with CSS disabled
- [ ] Browser with images disabled
- [ ] Form validation and error messages
- [ ] Skip links and landmarks
- [ ] Page titles and headings
- [ ] Alternative text for images

### Screen Reader Testing

**NVDA (Windows, Free)**
- NVDA + Down Arrow: Read next line
- NVDA + Up Arrow: Read previous line
- Insert + F7: List of elements
- H: Next heading
- K: Next link

**JAWS (Windows, Paid)**
- Down Arrow: Next line
- Insert + F6: List headings
- Insert + F7: List links
- T: Next table

**VoiceOver (Mac, Built-in)**
- VO + Right Arrow: Next item
- VO + Left Arrow: Previous item
- VO + U: Rotor menu
- VO + Command + H: Next heading

---

## Conclusion

Accessibility is not optional—it's a fundamental requirement for creating inclusive digital experiences. By following WCAG guidelines, implementing proper ARIA support, ensuring keyboard navigation, and designing with all users in mind, we create products that work for everyone.

### Key Takeaways

1. **Use semantic HTML** - It provides accessibility for free
2. **Test with real assistive technologies** - Automated tools catch only ~30% of issues
3. **Design for keyboard users** - Many people navigate without a mouse
4. **Provide text alternatives** - For all non-text content
5. **Ensure sufficient contrast** - Make content readable for everyone
6. **Make errors clear** - Help users recover from mistakes
7. **Think beyond compliance** - Aim for truly inclusive experiences

Accessibility benefits everyone: users with disabilities, users with temporary impairments, users in challenging situations, and users with older or slower devices. Building accessible interfaces is building better interfaces.
