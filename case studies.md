# Case Studies - Reference Links

This document contains links to the original sources, engineering blogs, and documentation that formed the basis for each case study.

---

## 1. Instagram - Django at Scale

### Official Instagram Engineering Blog
- **Web Service Efficiency at Instagram with Python** (2016)  
  https://instagram-engineering.com/web-service-efficiency-at-instagram-with-python-4976d078e366
  
### Third-Party Analysis
- **How Instagram Scaled to 14 Million Users with Only 3 Engineers**  
  https://read.engineerscodex.com/p/how-instagram-scaled-to-14-million
  
- **How Instagram Scaled Its Infrastructure To Support a Billion Users**  
  https://blog.bytebytego.com/p/how-instagram-scaled-its-infrastructure
  
- **Instagram Scales on Python for 2 Billion Daily Users**  
  https://www.linkedin.com/pulse/instagram-scales-python-2-billion-daily-users-shrey-batra
  
- **How Instagram Uses Python: Scaling the World's Largest Django Application**  
  https://python.plainenglish.io/how-instagram-uses-python-scaling-the-worlds-largest-django-application-1fb274fdf3d6

### Key Technologies
- Django (Python web framework)
- PostgreSQL with sharding
- Memcached & Redis
- Celery for async processing
- AWS (then migrated to Facebook infrastructure)

---

## 2. Dropbox - Distributed File Storage

### System Design Resources
- **Dropbox Architecture Deep Dive**  
  https://www.chengchangyu.com/blog/Dropbox-Architecture-Deep-Dive
  
- **System Design Of Dropbox**  
  https://medium.com/@lazygeek78/system-design-of-dropbox-6edb397a0f67
  
- **Dropbox System Design (Educative)**  
  https://www.educative.io/blog/dropbox-system-design
  
- **Design Dropbox — A System Design Interview Question**  
  https://medium.com/@anuupadhyay1994/design-dropbox-a-system-design-interview-question-6b58b528214
  
- **Dropbox's Magic Pocket: Power of Software Defined Storage**  
  https://chansblog.com/dropboxs-magic-pocket-power-of-software-defined-storage/
  
- **How Dropbox Ensures Reliable File Sync Across Devices**  
  https://www.frugaltesting.com/blog/how-dropbox-ensures-reliable-file-sync-across-devices

### Key Technologies
- Block-level deduplication
- Metadata database (MySQL/NoSQL)
- Magic Pocket (custom storage system)
- Delta sync algorithms
- WebSockets for real-time sync
- AWS S3 (initially, then custom infrastructure)

---

## 3. Mozilla - Security-First API Design

### Official Mozilla Documentation
- **Firefox Security Guidelines**  
  https://developer.mozilla.org/en-US/docs/Web/Security/Firefox_Security_Guidelines
  
- **Security Principles (Mozilla InfoSec)**  
  https://infosec.mozilla.org/fundamentals/security_principles.html
  
- **Web Security Guidelines**  
  https://infosec.mozilla.org/guidelines/web_security
  
- **Authentication - MDN**  
  https://developer.mozilla.org/en-US/docs/Web/Security/Authentication
  
- **Web Authentication API**  
  https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API
  
- **Password Security Best Practices**  
  https://developer.mozilla.org/en-US/docs/Web/Security/Authentication/Passwords
  
- **Federated Identity**  
  https://developer.mozilla.org/en-US/docs/Web/Security/Authentication/Federated_identity
  
- **Firefox Accounts API Documentation**  
  https://mozilla.github.io/ecosystem-platform/api

### Blog Posts
- **A Look at Password Security, Part IV: WebAuthn**  
  https://blog.mozilla.org/en/mozilla/password-security-part-iv-webauthn/

### Key Topics
- WebAuthn / FIDO2
- OAuth 2.0 / OpenID Connect
- TLS configuration
- Content Security Policy (CSP)
- HTTP security headers
- Multi-factor authentication (MFA)

---

## 4. Netflix - React Performance Optimization

### Official Netflix Tech Blog
- **Performance Without Compromise - Netflix JavaScript Talks** (2017)  
  http://techblog.netflix.com/2016/03/performance-without-compromise.html

### Case Studies
- **A Netflix Web Performance Case Study** (by Addy Osmani, 2018)  
  https://medium.com/dev-channel/a-netflix-web-performance-case-study-c0bcde26a9d9
  
- **Why Netflix Ditched React.js for Faster Speeds**  
  https://medium.com/@miralkumbhani/why-netflix-ditched-react-js-for-faster-speeds-and-how-it-worked-wonders-188ba90b75e2
  
- **Why Netflix Replaced React with Vanilla JavaScript**  
  https://codingwithalex.com/why-in-some-cases-you-should-use-pure-javascript-instead-of-frameworks-like-react/
  
- **Frontend System Design: Netflix Architecture**  
  https://namastedev.com/blog/frontend-system-design-netflix-architecture-3/
  
- **Does Netflix use React?**  
  https://www.designgurus.io/answers/detail/does-netflix-use-react
  
- **Improving Time-to-Interactive in React Apps with Server-Side Rendering**  
  https://www.angularminds.com/blog/improving-time-to-interactive-in-react-apps-with-server-side-rendering

### Video Resources
- **Netflix JavaScript Talks on YouTube**  
  https://www.youtube.com/watch?v=V8oTJ8OZ5S0&t=11m30s

### Key Insights
- Removed React from landing page (200kB reduction)
- 50% improvement in Time-to-Interactive
- Server-side rendering with React
- Prefetching for subsequent pages
- Vanilla JavaScript for low-interactivity pages
- RxJS for reactive programming

---

## 5. Airbnb - Design System Architecture

### Coming Soon
Links will be added for:
- Design system documentation
- Component library architecture
- Design tokens implementation
- Storybook integration
- Accessibility standards

---

## 6. Stripe - Payment Processing Architecture

### Coming Soon
Links will be added for:
- Idempotency patterns
- Distributed transactions
- PCI compliance
- Webhook systems
- API versioning

---

## 7. Uber - Real-Time Geospatial Systems

### Coming Soon
Links will be added for:
- Geohashing implementation
- S2 geometry library
- Real-time matching algorithms
- Routing optimization
- ETA prediction

---

## 8. Slack - Real-Time Messaging Infrastructure

### Coming Soon
Links will be added for:
- WebSocket architecture
- Message ordering
- Presence systems
- Typing indicators
- Read receipts

---

## General System Design Resources

### Books
- "Designing Data-Intensive Applications" by Martin Kleppmann
- "System Design Interview" by Alex Xu
- "Building Microservices" by Sam Newman

### Online Resources
- **ByteByteGo Blog**  
  https://blog.bytebytego.com/
  
- **HighScalability Blog**  
  http://highscalability.com/
  
- **Engineering Blogs Collection**  
  https://github.com/kilimchoi/engineering-blogs

### YouTube Channels
- **Netflix UI Engineering**
- **InfoQ**
- **GOTO Conferences**
- **Strange Loop**

---

**Note**: All links were current as of February 2026. Some may have moved or been updated since then. For the most current information, please visit the companies' official engineering blogs.
