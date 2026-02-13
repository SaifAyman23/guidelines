# Color and Typography Guidelines

## Table of Contents

1. [Introduction](#introduction)
2. [Color Theory Fundamentals](#color-theory-fundamentals)
3. [Creating Color Palettes](#creating-color-palettes)
4. [Color Contrast and Accessibility](#color-contrast-and-accessibility)
5. [Color Psychology and Usage](#color-psychology-and-usage)
6. [Typography Fundamentals](#typography-fundamentals)
7. [Typography Scales](#typography-scales)
8. [Font Pairing](#font-pairing)
9. [Spacing Systems](#spacing-systems)
10. [Practical Implementation](#practical-implementation)
11. [Common Patterns](#common-patterns)

---

## Introduction

Color and typography are two of the most powerful tools in a designer's toolkit. They communicate brand identity, establish visual hierarchy, create emotional connections, and ensure content is accessible and readable. This guide provides comprehensive principles and practical techniques for implementing effective color systems and typography in UI/UX design.

### Why Color and Typography Matter

**Color**
- Communicates brand identity and values
- Creates visual hierarchy and emphasis
- Evokes emotional responses
- Aids in information organization
- Improves user engagement

**Typography**
- Enhances readability and comprehension
- Establishes visual hierarchy
- Conveys tone and personality
- Affects user perception of quality
- Impacts user behavior and conversion

---

## Color Theory Fundamentals

### The Color Wheel

Understanding the color wheel is fundamental to creating effective color schemes.

**Primary Colors**
- Red, Yellow, Blue
- Cannot be created by mixing other colors

**Secondary Colors**
- Orange (Red + Yellow)
- Green (Yellow + Blue)
- Purple (Blue + Red)

**Tertiary Colors**
- Red-Orange, Yellow-Orange, Yellow-Green
- Blue-Green, Blue-Purple, Red-Purple

### Color Properties

#### Hue
The pure color without tint or shade (e.g., red, blue, green).

```css
/* Different hues */
.red { color: hsl(0, 100%, 50%); }      /* Pure red */
.blue { color: hsl(240, 100%, 50%); }   /* Pure blue */
.green { color: hsl(120, 100%, 50%); }  /* Pure green */
```

#### Saturation
The intensity or purity of a color.

```css
/* Same hue, different saturation */
.fully-saturated { color: hsl(210, 100%, 50%); } /* Vivid blue */
.medium-saturated { color: hsl(210, 50%, 50%); } /* Muted blue */
.desaturated { color: hsl(210, 20%, 50%); }      /* Gray-blue */
.grayscale { color: hsl(210, 0%, 50%); }         /* Pure gray */
```

#### Lightness/Value
How light or dark a color is.

```css
/* Same hue, different lightness */
.very-light { color: hsl(210, 80%, 90%); }  /* Light blue */
.medium { color: hsl(210, 80%, 50%); }      /* Medium blue */
.dark { color: hsl(210, 80%, 20%); }        /* Dark blue */
.very-dark { color: hsl(210, 80%, 10%); }   /* Very dark blue */
```

### Color Harmonies

#### Monochromatic
Variations of a single hue using different saturations and lightness values.

```css
:root {
  /* Monochromatic blue palette */
  --blue-50: hsl(210, 100%, 95%);
  --blue-100: hsl(210, 100%, 90%);
  --blue-200: hsl(210, 100%, 80%);
  --blue-300: hsl(210, 100%, 70%);
  --blue-400: hsl(210, 100%, 60%);
  --blue-500: hsl(210, 100%, 50%); /* Base color */
  --blue-600: hsl(210, 100%, 40%);
  --blue-700: hsl(210, 100%, 30%);
  --blue-800: hsl(210, 100%, 20%);
  --blue-900: hsl(210, 100%, 10%);
}
```

**Use cases:**
- Clean, professional designs
- Minimalist interfaces
- When brand color is fixed
- Subtle, sophisticated aesthetics

#### Analogous
Colors adjacent on the color wheel (within 30-60 degrees).

```css
:root {
  /* Analogous: Blue-Green harmony */
  --color-primary: hsl(210, 80%, 50%);    /* Blue */
  --color-secondary: hsl(180, 70%, 45%);  /* Cyan */
  --color-tertiary: hsl(150, 60%, 40%);   /* Green */
}
```

**Use cases:**
- Natural, harmonious designs
- Gradient backgrounds
- Subtle differentiation
- Comfortable viewing

#### Complementary
Colors opposite on the color wheel (180 degrees apart).

```css
:root {
  /* Complementary: Blue and Orange */
  --color-primary: hsl(210, 100%, 50%);   /* Blue */
  --color-accent: hsl(30, 100%, 50%);     /* Orange */
}
```

**Use cases:**
- High impact, vibrant designs
- Call-to-action buttons
- Creating strong contrast
- Drawing attention

#### Triadic
Three colors equally spaced on the color wheel (120 degrees apart).

```css
:root {
  /* Triadic: Red, Yellow, Blue */
  --color-primary: hsl(0, 100%, 50%);     /* Red */
  --color-secondary: hsl(120, 100%, 50%); /* Green */
  --color-tertiary: hsl(240, 100%, 50%);  /* Blue */
}
```

**Use cases:**
- Playful, energetic designs
- Children's applications
- Creative projects
- Diverse content categories

#### Split-Complementary
Base color plus two colors adjacent to its complement.

```css
:root {
  /* Split-complementary: Blue with Yellow-Orange and Red-Orange */
  --color-primary: hsl(210, 100%, 50%);   /* Blue */
  --color-accent-1: hsl(30, 100%, 50%);   /* Yellow-Orange */
  --color-accent-2: hsl(10, 100%, 50%);   /* Red-Orange */
}
```

**Use cases:**
- Balanced yet vibrant designs
- More nuanced than complementary
- Varied but harmonious palettes

#### Tetradic (Double-Complementary)
Two pairs of complementary colors.

```css
:root {
  /* Tetradic: Blue-Orange and Green-Red */
  --color-primary: hsl(210, 80%, 50%);    /* Blue */
  --color-secondary: hsl(120, 70%, 40%);  /* Green */
  --color-accent-1: hsl(30, 90%, 55%);    /* Orange */
  --color-accent-2: hsl(0, 85%, 50%);     /* Red */
}
```

---

## Creating Color Palettes

### Brand Color Palette

A complete brand palette should include:

```css
:root {
  /* Primary Brand Colors */
  --primary-50: #e3f2fd;
  --primary-100: #bbdefb;
  --primary-200: #90caf9;
  --primary-300: #64b5f6;
  --primary-400: #42a5f5;
  --primary-500: #2196f3;  /* Main brand color */
  --primary-600: #1e88e5;
  --primary-700: #1976d2;
  --primary-800: #1565c0;
  --primary-900: #0d47a1;
  
  /* Secondary Brand Colors */
  --secondary-50: #fce4ec;
  --secondary-100: #f8bbd0;
  --secondary-200: #f48fb1;
  --secondary-300: #f06292;
  --secondary-400: #ec407a;
  --secondary-500: #e91e63;  /* Secondary brand color */
  --secondary-600: #d81b60;
  --secondary-700: #c2185b;
  --secondary-800: #ad1457;
  --secondary-900: #880e4f;
  
  /* Neutral Colors */
  --gray-50: #fafafa;
  --gray-100: #f5f5f5;
  --gray-200: #eeeeee;
  --gray-300: #e0e0e0;
  --gray-400: #bdbdbd;
  --gray-500: #9e9e9e;
  --gray-600: #757575;
  --gray-700: #616161;
  --gray-800: #424242;
  --gray-900: #212121;
  
  /* Semantic Colors */
  --success-light: #81c784;
  --success: #4caf50;
  --success-dark: #388e3c;
  
  --warning-light: #ffb74d;
  --warning: #ff9800;
  --warning-dark: #f57c00;
  
  --error-light: #e57373;
  --error: #f44336;
  --error-dark: #d32f2f;
  
  --info-light: #64b5f6;
  --info: #2196f3;
  --info-dark: #1976d2;
}
```

### Functional Color System

```css
:root {
  /* Text Colors */
  --text-primary: rgba(0, 0, 0, 0.87);
  --text-secondary: rgba(0, 0, 0, 0.60);
  --text-disabled: rgba(0, 0, 0, 0.38);
  --text-hint: rgba(0, 0, 0, 0.38);
  
  /* Background Colors */
  --bg-default: #ffffff;
  --bg-paper: #f5f5f5;
  --bg-overlay: rgba(0, 0, 0, 0.5);
  
  /* Border Colors */
  --border-light: #e0e0e0;
  --border-medium: #bdbdbd;
  --border-dark: #757575;
  
  /* Interactive States */
  --hover-overlay: rgba(0, 0, 0, 0.04);
  --active-overlay: rgba(0, 0, 0, 0.12);
  --selected-overlay: rgba(33, 150, 243, 0.12);
  --focus-outline: #2196f3;
}

/* Dark mode variant */
[data-theme="dark"] {
  --text-primary: rgba(255, 255, 255, 0.87);
  --text-secondary: rgba(255, 255, 255, 0.60);
  --text-disabled: rgba(255, 255, 255, 0.38);
  
  --bg-default: #121212;
  --bg-paper: #1e1e1e;
  --bg-overlay: rgba(255, 255, 255, 0.1);
  
  --border-light: rgba(255, 255, 255, 0.12);
  --border-medium: rgba(255, 255, 255, 0.24);
  --border-dark: rgba(255, 255, 255, 0.36);
  
  --hover-overlay: rgba(255, 255, 255, 0.04);
  --active-overlay: rgba(255, 255, 255, 0.12);
}
```

### Generating Color Scales

#### Mathematical Approach

```javascript
// Generate color scale from base color
function generateColorScale(baseHue, baseSaturation) {
  return {
    50:  `hsl(${baseHue}, ${baseSaturation}%, 95%)`,
    100: `hsl(${baseHue}, ${baseSaturation}%, 90%)`,
    200: `hsl(${baseHue}, ${baseSaturation}%, 80%)`,
    300: `hsl(${baseHue}, ${baseSaturation}%, 70%)`,
    400: `hsl(${baseHue}, ${baseSaturation}%, 60%)`,
    500: `hsl(${baseHue}, ${baseSaturation}%, 50%)`,
    600: `hsl(${baseHue}, ${baseSaturation}%, 40%)`,
    700: `hsl(${baseHue}, ${baseSaturation}%, 30%)`,
    800: `hsl(${baseHue}, ${baseSaturation}%, 20%)`,
    900: `hsl(${baseHue}, ${baseSaturation}%, 10%)`,
  };
}

// Usage
const blueScale = generateColorScale(210, 100);
```

#### Perceptual Approach (Better)

```javascript
// More perceptually uniform scale
function generatePerceptualScale(baseHue, baseSaturation) {
  return {
    50:  `hsl(${baseHue}, ${baseSaturation * 0.9}%, 96%)`,
    100: `hsl(${baseHue}, ${baseSaturation * 0.95}%, 92%)`,
    200: `hsl(${baseHue}, ${baseSaturation}%, 83%)`,
    300: `hsl(${baseHue}, ${baseSaturation}%, 74%)`,
    400: `hsl(${baseHue}, ${baseSaturation * 1.05}%, 62%)`,
    500: `hsl(${baseHue}, ${baseSaturation * 1.1}%, 50%)`,
    600: `hsl(${baseHue}, ${baseSaturation * 1.15}%, 42%)`,
    700: `hsl(${baseHue}, ${baseSaturation * 1.2}%, 33%)`,
    800: `hsl(${baseHue}, ${baseSaturation * 1.25}%, 24%)`,
    900: `hsl(${baseHue}, ${baseSaturation * 1.3}%, 15%)`,
  };
}
```

---

## Color Contrast and Accessibility

### WCAG Contrast Requirements

**Normal Text (< 24px)**
- AA: 4.5:1 minimum
- AAA: 7:1 minimum

**Large Text (≥ 24px or 18.5px bold)**
- AA: 3:1 minimum
- AAA: 4.5:1 minimum

**UI Components**
- 3:1 minimum against adjacent colors

### Calculating Contrast Ratios

```javascript
// Calculate relative luminance
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Calculate contrast ratio
function getContrastRatio(rgb1, rgb2) {
  const lum1 = getLuminance(...rgb1);
  const lum2 = getLuminance(...rgb2);
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  return (brightest + 0.05) / (darkest + 0.05);
}

// Check if contrast passes WCAG
function meetsWCAG(ratio, level = 'AA', size = 'normal') {
  if (level === 'AAA') {
    return size === 'large' ? ratio >= 4.5 : ratio >= 7;
  }
  return size === 'large' ? ratio >= 3 : ratio >= 4.5;
}

// Usage
const textColor = [0, 0, 0];       // Black
const bgColor = [255, 255, 255];   // White
const ratio = getContrastRatio(textColor, bgColor);
console.log(ratio); // 21 - Excellent!
```

### Accessible Color Combinations

```css
/* AA Compliant Text Colors on White */
.text-primary {
  color: #1a1a1a;  /* 16.1:1 - AAA */
  background: #ffffff;
}

.text-secondary {
  color: #595959;  /* 7.0:1 - AAA */
  background: #ffffff;
}

.text-tertiary {
  color: #757575;  /* 4.54:1 - AA */
  background: #ffffff;
}

/* AA Compliant Colored Text */
.link-color {
  color: #0066cc;  /* 4.54:1 on white - AA */
}

.error-color {
  color: #d32f2f;  /* 4.52:1 on white - AA */
}

.success-color {
  color: #2e7d32;  /* 4.56:1 on white - AA */
}

/* AA Compliant Buttons */
.button-primary {
  background-color: #1976d2;  /* 4.53:1 with white text */
  color: #ffffff;
}

.button-secondary {
  background-color: #ffffff;
  color: #1976d2;
  border: 2px solid #1976d2;  /* 4.53:1 against white bg */
}

/* Text on Colored Backgrounds */
.card-blue {
  background-color: #2196f3;
  color: #ffffff;  /* 4.53:1 - AA */
}

.card-dark {
  background-color: #1a1a1a;
  color: #ffffff;  /* 16.1:1 - AAA */
}
```

### Testing Contrast

```css
/* Ensure sufficient contrast in all states */
.button {
  background-color: #2196f3;
  color: #ffffff;
  border: 2px solid transparent;
}

.button:hover {
  background-color: #1976d2;  /* Still 4.53:1 with white */
}

.button:focus {
  outline: 3px solid #0d47a1;  /* High contrast outline */
  outline-offset: 2px;
}

.button:disabled {
  background-color: #e0e0e0;
  color: #9e9e9e;  /* 2.84:1 - Intentionally low for disabled state */
  opacity: 0.6;
}
```

---

## Color Psychology and Usage

### Color Meanings and Applications

#### Red
**Associations**: Energy, passion, danger, urgency, excitement
**Use for**: Error messages, urgent notifications, sale badges, CTAs

```css
:root {
  --red-error: #d32f2f;
  --red-urgent: #f44336;
  --red-sale: #e53935;
}

.error-message {
  color: var(--red-error);
  border-left: 4px solid var(--red-error);
}

.urgent-notification {
  background-color: #ffebee;
  color: var(--red-urgent);
}

.sale-badge {
  background-color: var(--red-sale);
  color: #ffffff;
}
```

#### Blue
**Associations**: Trust, stability, professionalism, calm, technology
**Use for**: Primary buttons, links, corporate branding, technology products

```css
:root {
  --blue-primary: #2196f3;
  --blue-trust: #1976d2;
  --blue-link: #0066cc;
}

.primary-button {
  background-color: var(--blue-primary);
  color: #ffffff;
}

.link {
  color: var(--blue-link);
}

.professional-header {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
}
```

#### Green
**Associations**: Success, growth, nature, health, wealth
**Use for**: Success messages, confirmation, eco-friendly, financial

```css
:root {
  --green-success: #4caf50;
  --green-confirm: #2e7d32;
  --green-eco: #66bb6a;
}

.success-message {
  background-color: #e8f5e9;
  color: var(--green-success);
  border-left: 4px solid var(--green-success);
}

.confirmation-check {
  color: var(--green-confirm);
  font-size: 48px;
}
```

#### Yellow/Orange
**Associations**: Warning, optimism, creativity, energy
**Use for**: Warning messages, highlights, playful elements

```css
:root {
  --yellow-warning: #ff9800;
  --yellow-caution: #ffa726;
  --orange-accent: #ff6f00;
}

.warning-message {
  background-color: #fff3e0;
  color: #e65100;
  border-left: 4px solid var(--yellow-warning);
}

.highlight {
  background-color: #fff59d;
  padding: 2px 4px;
}
```

#### Purple
**Associations**: Luxury, creativity, wisdom, spirituality
**Use for**: Premium features, creative tools, special offers

```css
:root {
  --purple-luxury: #9c27b0;
  --purple-premium: #7b1fa2;
  --purple-creative: #ab47bc;
}

.premium-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}

.pro-feature {
  border: 2px solid var(--purple-luxury);
  background-color: #f3e5f5;
}
```

### Semantic Color System

```css
:root {
  /* Semantic intentions */
  --color-success: #4caf50;
  --color-success-bg: #e8f5e9;
  --color-success-border: #81c784;
  
  --color-warning: #ff9800;
  --color-warning-bg: #fff3e0;
  --color-warning-border: #ffb74d;
  
  --color-error: #f44336;
  --color-error-bg: #ffebee;
  --color-error-border: #e57373;
  
  --color-info: #2196f3;
  --color-info-bg: #e3f2fd;
  --color-info-border: #64b5f6;
}

/* Alert Components */
.alert {
  padding: 16px;
  border-radius: 4px;
  border-left: 4px solid;
}

.alert-success {
  background-color: var(--color-success-bg);
  color: #1b5e20;
  border-color: var(--color-success);
}

.alert-warning {
  background-color: var(--color-warning-bg);
  color: #e65100;
  border-color: var(--color-warning);
}

.alert-error {
  background-color: var(--color-error-bg);
  color: #b71c1c;
  border-color: var(--color-error);
}

.alert-info {
  background-color: var(--color-info-bg);
  color: #0d47a1;
  border-color: var(--color-info);
}
```

---

## Typography Fundamentals

### Font Categories

#### Serif
Fonts with decorative strokes (serifs) at the ends of letterforms.

```css
/* Serif Fonts */
.serif-traditional {
  font-family: 'Georgia', 'Times New Roman', serif;
  /* Use for: Long-form content, traditional brands, print-like aesthetics */
}

.serif-modern {
  font-family: 'Playfair Display', 'Merriweather', serif;
  /* Use for: Editorial content, elegant headings, luxury brands */
}
```

**Characteristics:**
- More traditional and formal
- Better for print (historically)
- Can be harder to read at small sizes on screens
- Conveys trustworthiness and authority

#### Sans-Serif
Clean fonts without decorative strokes.

```css
/* Sans-Serif Fonts */
.sans-modern {
  font-family: 'Helvetica Neue', 'Arial', sans-serif;
  /* Use for: UI elements, modern brands, clean interfaces */
}

.sans-geometric {
  font-family: 'Montserrat', 'Raleway', sans-serif;
  /* Use for: Headlines, tech brands, minimalist designs */
}

.sans-humanist {
  font-family: 'Open Sans', 'Lato', sans-serif;
  /* Use for: Body text, friendly interfaces, accessible designs */
}
```

**Characteristics:**
- Clean and modern
- Excellent screen readability
- Versatile and neutral
- Professional and approachable

#### Monospace
Fixed-width fonts where each character occupies the same horizontal space.

```css
.monospace {
  font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
  /* Use for: Code blocks, technical content, tabular data */
}

.code-block {
  font-family: 'Fira Code', 'Source Code Pro', monospace;
  font-size: 14px;
  line-height: 1.5;
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
}
```

#### Display/Decorative
Distinctive fonts for headlines and special purposes.

```css
.display-heading {
  font-family: 'Bebas Neue', 'Oswald', sans-serif;
  font-size: 72px;
  font-weight: 700;
  letter-spacing: 0.02em;
  /* Use sparingly for impact */
}
```

### Typography Properties

#### Font Size

```css
/* Base font size */
html {
  font-size: 16px; /* 1rem = 16px */
}

/* Relative sizing */
body {
  font-size: 1rem; /* 16px */
}

h1 { font-size: 3rem; }    /* 48px */
h2 { font-size: 2.25rem; } /* 36px */
h3 { font-size: 1.75rem; } /* 28px */
h4 { font-size: 1.25rem; } /* 20px */
h5 { font-size: 1rem; }    /* 16px */
h6 { font-size: 0.875rem; }/* 14px */

/* Responsive font sizes */
@media (max-width: 768px) {
  html {
    font-size: 14px; /* Smaller base on mobile */
  }
}

@media (min-width: 1440px) {
  html {
    font-size: 18px; /* Larger base on large screens */
  }
}
```

#### Font Weight

```css
.font-weights {
  font-weight: 100; /* Thin */
  font-weight: 200; /* Extra Light */
  font-weight: 300; /* Light */
  font-weight: 400; /* Normal/Regular */
  font-weight: 500; /* Medium */
  font-weight: 600; /* Semi Bold */
  font-weight: 700; /* Bold */
  font-weight: 800; /* Extra Bold */
  font-weight: 900; /* Black */
}

/* Practical usage */
.heading {
  font-weight: 700; /* Bold for headings */
}

.body {
  font-weight: 400; /* Regular for body text */
}

.label {
  font-weight: 600; /* Semi-bold for labels */
}

.emphasis {
  font-weight: 500; /* Medium for subtle emphasis */
}
```

#### Line Height (Leading)

```css
/* Optimal line heights */
body {
  line-height: 1.6; /* 1.5-1.7 for body text */
}

h1, h2, h3 {
  line-height: 1.2; /* 1.1-1.3 for headings */
}

.compact-text {
  line-height: 1.4; /* For UI elements */
}

.spacious-text {
  line-height: 1.8; /* For enhanced readability */
}

/* Unitless values scale with font size */
.responsive-height {
  font-size: 1rem;
  line-height: 1.5; /* 1.5 × current font size */
}
```

#### Letter Spacing (Tracking)

```css
/* Default is 0 */
.heading-condensed {
  letter-spacing: -0.02em; /* Tighter for large headings */
}

.heading-expanded {
  letter-spacing: 0.05em; /* Looser for all-caps */
}

.all-caps {
  text-transform: uppercase;
  letter-spacing: 0.1em; /* Essential for uppercase */
  font-size: 0.875em; /* Slightly smaller */
}

.body-text {
  letter-spacing: 0; /* Normal for body text */
}

.small-text {
  letter-spacing: 0.01em; /* Slightly open for legibility */
}
```

---

## Typography Scales

### Major Third Scale (1.250)

```css
:root {
  --scale-ratio: 1.250;
  
  --text-xs: 0.64rem;    /* 10.24px */
  --text-sm: 0.8rem;     /* 12.8px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.25rem;    /* 20px */
  --text-xl: 1.563rem;   /* 25px */
  --text-2xl: 1.953rem;  /* 31.25px */
  --text-3xl: 2.441rem;  /* 39px */
  --text-4xl: 3.052rem;  /* 48.83px */
  --text-5xl: 3.815rem;  /* 61.04px */
}

.heading-1 { font-size: var(--text-5xl); }
.heading-2 { font-size: var(--text-4xl); }
.heading-3 { font-size: var(--text-3xl); }
.heading-4 { font-size: var(--text-2xl); }
.heading-5 { font-size: var(--text-xl); }
.heading-6 { font-size: var(--text-lg); }
.body { font-size: var(--text-base); }
.small { font-size: var(--text-sm); }
.tiny { font-size: var(--text-xs); }
```

### Perfect Fourth Scale (1.333)

```css
:root {
  --text-xs: 0.563rem;   /* 9px */
  --text-sm: 0.75rem;    /* 12px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.333rem;   /* 21.33px */
  --text-xl: 1.777rem;   /* 28.43px */
  --text-2xl: 2.369rem;  /* 37.90px */
  --text-3xl: 3.157rem;  /* 50.52px */
  --text-4xl: 4.209rem;  /* 67.34px */
  --text-5xl: 5.610rem;  /* 89.76px */
}
```

### Golden Ratio Scale (1.618)

```css
:root {
  --text-xs: 0.382rem;   /* 6.11px */
  --text-sm: 0.618rem;   /* 9.89px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.618rem;   /* 25.89px */
  --text-xl: 2.618rem;   /* 41.89px */
  --text-2xl: 4.236rem;  /* 67.77px */
  --text-3xl: 6.854rem;  /* 109.66px */
}
```

### Responsive Typography Scale

```css
/* Fluid typography using clamp() */
:root {
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);
  --text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.625vw, 1.5rem);
  --text-xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.875rem);
  --text-2xl: clamp(1.5rem, 1.2rem + 1.5vw, 2.25rem);
  --text-3xl: clamp(1.875rem, 1.5rem + 1.875vw, 3rem);
  --text-4xl: clamp(2.25rem, 1.8rem + 2.25vw, 3.75rem);
  --text-5xl: clamp(3rem, 2.4rem + 3vw, 4.5rem);
}

/* Scales smoothly between min and max viewport widths */
h1 { font-size: var(--text-5xl); }
h2 { font-size: var(--text-4xl); }
h3 { font-size: var(--text-3xl); }
```

---

## Font Pairing

### Pairing Principles

1. **Contrast**: Pair fonts that are different but complementary
2. **Hierarchy**: Create clear visual distinction
3. **Mood**: Fonts should support the same emotional tone
4. **Limit**: Use 2-3 fonts maximum

### Classic Pairings

#### Serif Heading + Sans-Serif Body

```css
/* Elegant and readable */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Playfair Display', Georgia, serif;
  font-weight: 700;
  line-height: 1.2;
}

body, p, li {
  font-family: 'Source Sans Pro', 'Helvetica Neue', sans-serif;
  font-weight: 400;
  line-height: 1.6;
}
```

#### Sans-Serif Heading + Serif Body

```css
/* Modern editorial */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Montserrat', 'Helvetica Neue', sans-serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

body, p, li {
  font-family: 'Merriweather', Georgia, serif;
  font-weight: 400;
  line-height: 1.7;
}
```

#### Sans-Serif Contrasting Weights

```css
/* Clean and modern */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Inter', 'Helvetica Neue', sans-serif;
  font-weight: 800; /* Extra bold */
  line-height: 1.1;
}

body, p, li {
  font-family: 'Inter', 'Helvetica Neue', sans-serif;
  font-weight: 400; /* Regular */
  line-height: 1.6;
}
```

### Complete Typography System

```css
/* Typography Scale with Font Pairing */
:root {
  /* Font Families */
  --font-display: 'Playfair Display', Georgia, serif;
  --font-heading: 'Poppins', 'Helvetica Neue', sans-serif;
  --font-body: 'Inter', 'Helvetica Neue', sans-serif;
  --font-mono: 'Fira Code', 'Consolas', monospace;
  
  /* Font Sizes */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;
  --text-5xl: 3rem;
  --text-6xl: 3.75rem;
  
  /* Font Weights */
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  --font-extrabold: 800;
  
  /* Line Heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
}

/* Display Headings */
.display-1 {
  font-family: var(--font-display);
  font-size: var(--text-6xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
}

/* Standard Headings */
h1 {
  font-family: var(--font-heading);
  font-size: var(--text-5xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
}

h2 {
  font-family: var(--font-heading);
  font-size: var(--text-4xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
}

h3 {
  font-family: var(--font-heading);
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
}

h4 {
  font-family: var(--font-heading);
  font-size: var(--text-2xl);
  font-weight: var(--font-medium);
  line-height: var(--leading-snug);
}

/* Body Text */
body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-relaxed);
}

p {
  margin-bottom: 1em;
}

.lead {
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
  font-weight: var(--font-normal);
}

.small {
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
}

/* Special Elements */
strong, b {
  font-weight: var(--font-bold);
}

em, i {
  font-style: italic;
}

code {
  font-family: var(--font-mono);
  font-size: 0.875em;
  background-color: #f5f5f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
}

pre {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  background-color: #1e1e1e;
  color: #e0e0e0;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
}
```

---

## Spacing Systems

### The 8-Point Grid

```css
:root {
  /* Base unit: 8px */
  --space-0: 0;
  --space-1: 0.5rem;   /* 8px */
  --space-2: 1rem;     /* 16px */
  --space-3: 1.5rem;   /* 24px */
  --space-4: 2rem;     /* 32px */
  --space-5: 2.5rem;   /* 40px */
  --space-6: 3rem;     /* 48px */
  --space-7: 3.5rem;   /* 56px */
  --space-8: 4rem;     /* 64px */
  --space-9: 4.5rem;   /* 72px */
  --space-10: 5rem;    /* 80px */
  --space-12: 6rem;    /* 96px */
  --space-16: 8rem;    /* 128px */
  --space-20: 10rem;   /* 160px */
  --space-24: 12rem;   /* 192px */
}

/* Component spacing */
.card {
  padding: var(--space-4);
  margin-bottom: var(--space-4);
}

.section {
  padding: var(--space-12) 0;
}

.button {
  padding: var(--space-2) var(--space-4);
}
```

### Vertical Rhythm

```css
/* Establish baseline grid */
:root {
  --baseline: 1.5rem; /* 24px with 16px base font */
}

h1 {
  font-size: 3rem;
  line-height: calc(var(--baseline) * 2); /* 48px */
  margin-bottom: var(--baseline);
}

h2 {
  font-size: 2.25rem;
  line-height: var(--baseline);
  margin-top: calc(var(--baseline) * 2);
  margin-bottom: var(--baseline);
}

p {
  font-size: 1rem;
  line-height: var(--baseline);
  margin-bottom: var(--baseline);
}

/* Elements snap to baseline grid */
.element {
  margin-bottom: calc(var(--baseline) * 2); /* 48px */
}
```

### Content Spacing

```css
/* Optimal reading width */
.content {
  max-width: 65ch; /* 65 characters per line */
  margin-left: auto;
  margin-right: auto;
  padding: 0 var(--space-4);
}

/* Article spacing */
.article h2 {
  margin-top: var(--space-8);
  margin-bottom: var(--space-3);
}

.article p {
  margin-bottom: var(--space-4);
}

.article ul, 
.article ol {
  margin-bottom: var(--space-4);
  padding-left: var(--space-6);
}

.article li {
  margin-bottom: var(--space-2);
}

/* Sibling spacing */
h2 + p {
  margin-top: calc(var(--space-3) * -0.5); /* Tighter after heading */
}

p + h3 {
  margin-top: var(--space-6); /* More space before subheading */
}
```

---

## Practical Implementation

### Complete Design System

```css
/* Design System - Colors & Typography */
:root {
  /* ===== COLORS ===== */
  
  /* Primary Palette */
  --primary-50: #e3f2fd;
  --primary-500: #2196f3;
  --primary-700: #1976d2;
  --primary-900: #0d47a1;
  
  /* Gray Palette */
  --gray-50: #fafafa;
  --gray-100: #f5f5f5;
  --gray-300: #e0e0e0;
  --gray-500: #9e9e9e;
  --gray-700: #616161;
  --gray-900: #212121;
  
  /* Semantic Colors */
  --success: #4caf50;
  --warning: #ff9800;
  --error: #f44336;
  --info: #2196f3;
  
  /* ===== TYPOGRAPHY ===== */
  
  /* Fonts */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-display: 'Playfair Display', Georgia, serif;
  --font-mono: 'Fira Code', monospace;
  
  /* Sizes */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;
  --text-5xl: 3rem;
  
  /* Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  /* ===== SPACING ===== */
  --space-1: 0.5rem;
  --space-2: 1rem;
  --space-3: 1.5rem;
  --space-4: 2rem;
  --space-6: 3rem;
  --space-8: 4rem;
  --space-12: 6rem;
}

/* Base Styles */
body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--gray-900);
  background-color: var(--gray-50);
}

/* Typography */
h1, h2, h3 {
  font-family: var(--font-display);
  color: var(--gray-900);
  font-weight: var(--font-bold);
  line-height: 1.2;
}

h1 { font-size: var(--text-5xl); margin-bottom: var(--space-3); }
h2 { font-size: var(--text-4xl); margin-bottom: var(--space-3); }
h3 { font-size: var(--text-3xl); margin-bottom: var(--space-2); }

p { margin-bottom: var(--space-4); }

/* Components */
.button {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  padding: var(--space-2) var(--space-4);
  border-radius: 4px;
  transition: all 0.2s ease;
}

.button-primary {
  background-color: var(--primary-500);
  color: white;
}

.button-primary:hover {
  background-color: var(--primary-700);
}

.card {
  background-color: white;
  border-radius: 8px;
  padding: var(--space-4);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

---

## Common Patterns

### Color Pattern: Status Indicators

```css
.status {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-success {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.status-warning {
  background-color: #fff3e0;
  color: #e65100;
}

.status-error {
  background-color: #ffebee;
  color: #c62828;
}

.status-info {
  background-color: #e3f2fd;
  color: #1565c0;
}
```

### Typography Pattern: Article Layout

```css
.article {
  max-width: 65ch;
  margin: 0 auto;
  padding: var(--space-8) var(--space-4);
}

.article-title {
  font-size: var(--text-5xl);
  font-weight: var(--font-bold);
  line-height: 1.1;
  margin-bottom: var(--space-2);
}

.article-meta {
  font-size: var(--text-sm);
  color: var(--gray-600);
  margin-bottom: var(--space-6);
}

.article-content h2 {
  margin-top: var(--space-8);
  margin-bottom: var(--space-3);
}

.article-content p {
  font-size: var(--text-lg);
  line-height: 1.7;
  margin-bottom: var(--space-4);
}
```

### Color Pattern: Dark Mode

```css
/* Light mode (default) */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
  --border-color: #e0e0e0;
}

/* Dark mode */
[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2a2a2a;
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --border-color: #404040;
}

/* Usage */
body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
}
```

---

## Conclusion

Effective use of color and typography is essential for creating professional, accessible, and engaging user interfaces. By understanding color theory, implementing systematic approaches to color palettes, choosing appropriate typefaces, and maintaining consistent spacing systems, designers can create cohesive and user-friendly experiences.

### Key Takeaways

**Color:**
- Use systematic color scales (50-900)
- Ensure WCAG AA compliance minimum (4.5:1 for text)
- Implement semantic color systems
- Consider color psychology
- Support dark mode
- Test with colorblind simulators

**Typography:**
- Establish a modular scale
- Pair fonts thoughtfully (2-3 maximum)
- Maintain appropriate line heights (1.5-1.7 for body)
- Use relative units (rem, em)
- Optimize for readability (60-80 characters per line)
- Create clear visual hierarchy

**Spacing:**
- Use 8-point grid system
- Maintain vertical rhythm
- Be consistent with spacing values
- Provide adequate whitespace
- Scale appropriately for different screen sizes

Remember: Good design is systematic, accessible, and purposeful. Every color choice and typographic decision should serve your users and support your product's goals.
