# User Flows and Research Guidelines

## Table of Contents

1. [Introduction to User Flows](#introduction-to-user-flows)
2. [User Journey Mapping](#user-journey-mapping)
3. [Wireframing](#wireframing)
4. [Prototyping](#prototyping)
5. [User Research Methods](#user-research-methods)
6. [Usability Testing](#usability-testing)
7. [Information Architecture](#information-architecture)
8. [Data Analysis and Iteration](#data-analysis-and-iteration)
9. [Tools and Resources](#tools-and-resources)
10. [Best Practices](#best-practices)

---

## Introduction to User Flows

User flows are visual representations of the complete path a user takes to accomplish a specific task within a product. They help teams understand user behavior, identify pain points, and optimize the user experience.

### What is a User Flow?

A user flow diagram shows:
- **Entry points**: Where users begin their journey
- **Steps**: Actions users take along the path
- **Decision points**: Choices users must make
- **End points**: Goals or exits from the flow

### Why User Flows Matter

**For Design Teams**
- Identifies gaps and redundancies in the experience
- Helps prioritize features and improvements
- Facilitates communication between designers and developers
- Serves as documentation for product decisions

**For Users**
- Ensures efficient task completion
- Reduces friction and confusion
- Creates predictable, learnable patterns
- Minimizes steps to reach goals

**For Business**
- Increases conversion rates
- Reduces support costs
- Improves user retention
- Enables data-driven decisions

### Types of User Flows

#### Task Flows
Focus on a single task with a specific entry and exit point.

```
Example: Purchase Flow
Entry → Browse Products → Select Product → Add to Cart → Checkout → Payment → Confirmation → Exit
```

#### User Flows
Show all possible paths a user might take, including variations and decision points.

```
Example: Shopping Flow
Entry → Logged in? 
  ├─ Yes → Browse → Find product? → Add to cart → Checkout
  └─ No → Create account? 
       ├─ Yes → Sign up → Browse
       └─ No → Browse as guest → Limited features
```

#### Wire Flows
Combine wireframes with flow diagrams to show both interface and navigation.

```
[Homepage Screen] → Click "Sign Up" → [Registration Form Screen] 
→ Fill form → Validate → Success? 
   ├─ Yes → [Welcome Screen]
   └─ No → [Error Message] → [Registration Form Screen]
```

---

## User Journey Mapping

User journey maps are comprehensive visualizations that show the entire experience a user has with your product, including emotions, pain points, and opportunities.

### Components of a Journey Map

#### 1. User Persona
**Who is this journey for?**

```
Persona: Sarah, Marketing Manager
Age: 32
Goals: 
- Increase campaign ROI
- Streamline workflow
- Generate reports quickly

Pain Points:
- Too many disconnected tools
- Manual data entry
- Slow report generation

Tech Savvy: High
Device Usage: Desktop (70%), Mobile (30%)
```

#### 2. Scenario
**What are they trying to accomplish?**

```
Scenario: Creating and launching a marketing email campaign

Context:
- Time constraint: Campaign must launch in 2 days
- Working remotely
- First time using the platform
- Needs approval from manager
```

#### 3. Phases
**Major stages of the journey**

```
Phases:
1. Awareness - Discovering the platform
2. Consideration - Evaluating features
3. Onboarding - Setting up account
4. Usage - Creating campaign
5. Evaluation - Reviewing results
```

#### 4. Actions, Thoughts, and Emotions

```
Phase: Onboarding

Actions:
- Signs up for account
- Receives welcome email
- Watches tutorial video
- Imports contact list
- Explores dashboard

Thoughts:
"Is this going to be complicated?"
"I hope I don't have to start from scratch"
"The interface looks clean"

Emotions:
Uncertain → Hopeful → Confident

Pain Points:
- Unclear where to start
- Import process requires CSV format
- Tutorial is too long
```

### Creating a Journey Map

#### Step 1: Define Scope

```
Scope Definition:
- Journey: From awareness to first campaign launch
- Timeframe: 1 week
- Touchpoints: Website, email, product, support
- Goal: Complete first campaign
```

#### Step 2: Gather Research Data

```
Research Sources:
✓ User interviews (5-10 users)
✓ Analytics data (signup → launch conversion)
✓ Support ticket analysis
✓ Session recordings
✓ Customer surveys
✓ Competitive analysis
```

#### Step 3: Map the Journey

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: AWARENESS                                              │
├─────────────────────────────────────────────────────────────────┤
│ Touchpoints: Google search, review sites, social media          │
│                                                                  │
│ Actions:                                                         │
│ • Searches "email marketing tools"                              │
│ • Reads reviews                                                 │
│ • Compares features                                             │
│                                                                  │
│ Thoughts:                                                        │
│ "Which tool is best for my needs?"                              │
│ "Can I afford this?"                                            │
│                                                                  │
│ Emotions: 😐 Overwhelmed → 🙂 Interested                        │
│                                                                  │
│ Opportunities:                                                   │
│ • Clear feature comparison                                      │
│ • Transparent pricing                                           │
│ • Customer testimonials                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: CONSIDERATION                                          │
├─────────────────────────────────────────────────────────────────┤
│ Touchpoints: Website, free trial, demo                          │
│                                                                  │
│ Actions:                                                         │
│ • Visits website                                                │
│ • Watches demo video                                            │
│ • Starts free trial                                             │
│                                                                  │
│ Thoughts:                                                        │
│ "Does this have what I need?"                                   │
│ "Will my team be able to use this?"                             │
│                                                                  │
│ Emotions: 🙂 Curious → 😊 Excited                               │
│                                                                  │
│ Pain Points:                                                     │
│ • Too many features shown at once                               │
│ • Unclear pricing structure                                     │
│                                                                  │
│ Opportunities:                                                   │
│ • Guided product tours                                          │
│ • Clear value proposition                                       │
│ • Quick wins in trial                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Journey Map Template

```
USER JOURNEY MAP
================

Persona: [Name and brief description]
Scenario: [What they're trying to accomplish]
Timeframe: [Duration of journey]

┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Phase    │ Phase 1  │ Phase 2  │ Phase 3  │ Phase 4  │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │          │
│Touch-    │          │          │          │          │
│points    │          │          │          │          │
│          │          │          │          │          │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │          │
│Actions   │          │          │          │          │
│          │          │          │          │          │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │          │
│Thoughts  │          │          │          │          │
│          │          │          │          │          │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │          │
│Emotions  │ 😐 → 🙂  │ 🙂 → 😊  │ 😊 → 😃  │ 😃 → 😍  │
│          │          │          │          │          │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │          │
│Pain      │          │          │          │          │
│Points    │          │          │          │          │
│          │          │          │          │          │
├──────────┼──────────┼──────────┼──────────┼──────────┤
│          │          │          │          │          │
│Opportuni-│          │          │          │          │
│ties      │          │          │          │          │
│          │          │          │          │          │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## Wireframing

Wireframes are low-fidelity visual guides that represent the skeletal framework of a website or application. They focus on structure, layout, and functionality rather than visual design.

### Types of Wireframes

#### Low-Fidelity Wireframes
Simple, rough sketches focusing on layout and structure.

```
┌─────────────────────────────────────────┐
│  [Logo]              [Search] [Profile] │
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────────────────────────────┐ │
│  │                                    │ │
│  │        [Hero Image]                │ │
│  │                                    │ │
│  │    [Headline]                      │ │
│  │    [Subheadline]                   │ │
│  │    [CTA Button]                    │ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │      │  │      │  │      │          │
│  │ Card │  │ Card │  │ Card │          │
│  │      │  │      │  │      │          │
│  └──────┘  └──────┘  └──────┘          │
│                                          │
└─────────────────────────────────────────┘
```

**Benefits:**
- Fast to create
- Easy to iterate
- Focuses on functionality
- Low commitment

**Use when:**
- Brainstorming ideas
- Early concept exploration
- Quick iterations needed
- Presenting general structure

#### Mid-Fidelity Wireframes
More detailed, showing actual content hierarchy and UI elements.

```
┌─────────────────────────────────────────────────────────┐
│ [Company Logo]                   [Home][About][Contact] │
│                                        [Search...] [🔍]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │                                                    │  │
│ │              Product Image Placeholder            │  │
│ │                   800 x 400                        │  │
│ │                                                    │  │
│ │        Discover the Perfect Solution               │  │
│ │     Transform your workflow with our platform      │  │
│ │                                                    │  │
│ │          [ Get Started Free ]  [ Learn More ]     │  │
│ │                                                    │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ Features                                                 │
│ ─────────                                                │
│                                                          │
│ ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│ │   [Icon]   │  │   [Icon]   │  │   [Icon]   │         │
│ │            │  │            │  │            │         │
│ │  Feature 1 │  │  Feature 2 │  │  Feature 3 │         │
│ │            │  │            │  │            │         │
│ │ Description│  │ Description│  │ Description│         │
│ │ text goes  │  │ text goes  │  │ text goes  │         │
│ │ here       │  │ here       │  │ here       │         │
│ │            │  │            │  │            │         │
│ │ [Link →]   │  │ [Link →]   │  │ [Link →]   │         │
│ └────────────┘  └────────────┘  └────────────┘         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Benefits:**
- Shows content hierarchy
- Defines component states
- Clarifies interactions
- Useful for developer handoff

**Use when:**
- Need to show content structure
- Testing layout variations
- Collaborating with developers
- Before visual design phase

#### High-Fidelity Wireframes
Detailed representations with actual content, spacing, and sizing.

```
┌───────────────────────────────────────────────────────────────┐
│ ⚡ BoltUI                          Home  Features  Pricing    │
│                                           [Search products...] │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │                                                          │  │
│ │                                                          │  │
│ │              [Professional Product Photo]                │  │
│ │                      1200 x 600                          │  │
│ │                                                          │  │
│ │        Build Amazing Products Faster                     │  │
│ │     The complete design system for modern applications   │  │
│ │                                                          │  │
│ │        [Start Free Trial]    [View Demo ▶]              │  │
│ │                                                          │  │
│ │    ✓ 14-day trial  ✓ No credit card  ✓ Cancel anytime   │  │
│ │                                                          │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                │
│ Why developers choose BoltUI                                  │
│ ───────────────────────────────                                │
│                                                                │
│ ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│ │    ⚡        │    │    🎨        │    │    📱        │     │
│ │              │    │              │    │              │     │
│ │ Lightning    │    │  Beautiful   │    │  Responsive  │     │
│ │ Fast         │    │  Design      │    │  First       │     │
│ │              │    │              │    │              │     │
│ │ Optimized    │    │ Pre-designed │    │ Works        │     │
│ │ components   │    │ templates    │    │ everywhere   │     │
│ │ that load    │    │ that look    │    │ from mobile  │     │
│ │ instantly    │    │ professional │    │ to desktop   │     │
│ │              │    │              │    │              │     │
│ │ Learn more → │    │ Learn more → │    │ Learn more → │     │
│ └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### Wireframing Best Practices

#### 1. Start with User Goals

```
User Goal: Purchase a product

Questions to answer:
✓ How does user find the product?
✓ What information do they need to decide?
✓ How many steps to checkout?
✓ What could go wrong?
✓ How do they track their order?
```

#### 2. Follow Design Patterns

```
Common Patterns:

Navigation:
- Top horizontal nav for main sections
- Hamburger menu for mobile
- Sidebar for complex hierarchies
- Tabs for related content

Forms:
- Labels above inputs
- Error messages below fields
- Required field indicators
- Progress indicators for multi-step

Cards:
- Image at top
- Title and description
- Actions at bottom
- Consistent sizing
```

#### 3. Establish Visual Hierarchy

```
Hierarchy Levels:

Level 1: Primary action or content
- Largest size
- Highest contrast
- Most prominent position

Level 2: Secondary content
- Medium size
- Medium contrast
- Supporting primary content

Level 3: Tertiary information
- Smallest size
- Lower contrast
- Helper text, metadata
```

#### 4. Annotate Wireframes

```
Annotations to Include:

Functionality:
- Click behavior
- Hover states
- Loading states
- Error states

Content:
- Character limits
- Content source
- Dynamic vs static

Interactions:
- Animations
- Transitions
- Gestures (mobile)

Technical Notes:
- API endpoints
- Validation rules
- Permissions
```

---

## Prototyping

Prototypes are interactive mockups that simulate the final product's functionality, allowing teams to test and validate designs before development.

### Fidelity Levels

#### Low-Fidelity Prototypes

```
Paper Prototype:
- Hand-drawn screens on paper
- User "clicks" by pointing
- Designer changes pages manually

Digital Low-Fi:
- Clickable wireframes
- Basic transitions
- No animations
- Placeholder content

Use cases:
✓ Early concept testing
✓ Stakeholder alignment
✓ Quick iteration
✓ Testing multiple approaches
```

#### Mid-Fidelity Prototypes

```
Interactive Wireframes:
- Clickable elements
- Screen transitions
- Basic interactions
- Some real content

Features:
✓ Navigation flow
✓ Form interactions
✓ Modal behaviors
✓ Simple animations

Use cases:
✓ User testing
✓ Developer handoff
✓ Design reviews
✓ Feature validation
```

#### High-Fidelity Prototypes

```
Polished Interactive Design:
- Full visual design
- Micro-interactions
- Animations
- Real content
- Responsive behavior

Features:
✓ Production-quality visuals
✓ Complex interactions
✓ State management
✓ Edge cases
✓ Error handling

Use cases:
✓ Final user testing
✓ Stakeholder presentations
✓ Marketing materials
✓ Developer specification
```

### Prototyping Workflow

#### Step 1: Define Scope

```
Prototype Scope Document:

Goal: Test checkout flow

Screens to include:
✓ Product page
✓ Cart
✓ Checkout (3 steps)
✓ Confirmation

Interactions to prototype:
✓ Add to cart
✓ Update quantity
✓ Apply coupon
✓ Form validation
✓ Payment processing

Out of scope:
✗ Account creation
✗ Product browsing
✗ Reviews
```

#### Step 2: Create User Scenarios

```
Scenario 1: Happy Path
User: Sarah, returning customer
Goal: Purchase a product with saved payment

Steps:
1. Arrives at product page from email
2. Clicks "Add to Cart"
3. Proceeds to checkout
4. Selects saved address
5. Selects saved payment method
6. Reviews order
7. Confirms purchase
8. Sees confirmation

Expected time: 2-3 minutes
```

```
Scenario 2: Error Recovery
User: John, new customer
Goal: Complete purchase despite errors

Steps:
1. Adds product to cart
2. Proceeds to checkout
3. Enters invalid email → sees error
4. Corrects email
5. Enters expired credit card → sees error
6. Updates payment method
7. Completes purchase

Expected friction points:
- Form validation
- Error messaging
- Error recovery
```

#### Step 3: Build Prototype

```
Component Checklist:

✓ Navigation
  - Main menu
  - Breadcrumbs
  - Back buttons

✓ Forms
  - All required fields
  - Validation states
  - Error messages
  - Success states

✓ Feedback
  - Loading indicators
  - Success messages
  - Error alerts
  - Empty states

✓ Interactions
  - Hover states
  - Click/tap states
  - Transitions
  - Animations
```

### Advanced Prototyping Techniques

#### Conditional Logic

```
Example: Dynamic Form Fields

IF user selects "Ship to different address"
THEN show address form
ELSE hide address form

IF cart total > $50
THEN hide shipping fee
ELSE show shipping fee: $5.99

IF payment fails
THEN show error message
AND disable submit button for 2 seconds
AND highlight payment fields
```

#### Variables and Data

```
Cart Prototype Variables:

itemCount = 2
subtotal = $89.99
shipping = $5.99
tax = $8.10
total = $104.08

When user adds item:
itemCount += 1
subtotal += itemPrice
tax = subtotal * 0.09
total = subtotal + shipping + tax
UPDATE cart badge
UPDATE totals display
SHOW success notification
```

#### State Management

```
Button States:

Default:
- Enabled
- Primary color
- Text: "Add to Cart"

Hover:
- Slightly darker
- Subtle shadow

Active/Clicked:
- Even darker
- Pressed appearance
- Text changes to "Adding..."

Loading:
- Disabled
- Spinner appears
- Text: "Adding..."

Success:
- Green background
- Checkmark appears
- Text: "Added!"
- After 2s, return to default

Error:
- Red background
- X icon appears
- Text: "Error - Try Again"
```

---

## User Research Methods

### Qualitative Research

#### User Interviews

```
Interview Structure:

1. Introduction (5 min)
   - Build rapport
   - Explain purpose
   - Get consent

2. Background (10 min)
   - Current process/tools
   - Pain points
   - Goals

3. Task Discussion (25 min)
   - Specific scenarios
   - Decision making
   - Workarounds

4. Product Feedback (15 min)
   - Show designs/prototype
   - Observe reactions
   - Ask open questions

5. Wrap-up (5 min)
   - Final thoughts
   - Thank participant

Total: 60 minutes
```

**Interview Questions Template:**

```
Opening Questions:
- "Tell me about your role and daily responsibilities"
- "What tools do you currently use for [task]?"
- "Walk me through your typical workflow"

Problem Discovery:
- "What frustrates you about [current process]?"
- "Tell me about a time when [problem] occurred"
- "How do you currently handle [challenge]?"

Behavioral Questions:
- "Show me how you would [complete task]"
- "What would you do if [scenario]?"
- "Why did you choose that approach?"

Product Feedback:
- "What are your first impressions?"
- "What would you expect to happen if you clicked here?"
- "Is there anything missing that you expected to see?"

Closing:
- "If you could change one thing, what would it be?"
- "Is there anything we didn't cover that you think is important?"
```

#### Contextual Inquiry

```
Observation Protocol:

Setting: User's natural environment

Approach:
1. Master-Apprentice model
   - User is the expert
   - Researcher observes and asks questions

2. Observe actual work
   - Not what they say they do
   - But what they actually do

3. Note:
   - Tools used
   - Workarounds
   - Interruptions
   - Collaboration
   - Environment factors

4. Ask "why" frequently
   - Understand motivations
   - Discover mental models
   - Uncover assumptions
```

#### Focus Groups

```
Focus Group Structure:

Participants: 6-8 people
Duration: 90-120 minutes
Moderator: 1 person
Note-taker: 1 person

Agenda:
1. Welcome & Introductions (10 min)
2. Warm-up Discussion (15 min)
3. Main Topics (60 min)
   - 3-4 topics, 15-20 min each
4. Prototype Feedback (20 min)
5. Wrap-up (15 min)

Benefits:
✓ Group dynamics
✓ Diverse perspectives
✓ Cost-effective
✓ Quick insights

Limitations:
✗ Groupthink
✗ Dominant participants
✗ Not representative
✗ Facilitator bias
```

### Quantitative Research

#### Surveys

```
Survey Best Practices:

Length:
- 5-10 minutes maximum
- 10-15 questions
- Mobile-friendly

Question Types:

Multiple Choice:
"How often do you use our product?"
○ Daily
○ Weekly
○ Monthly
○ Rarely
○ Never

Rating Scale:
"How satisfied are you with [feature]?"
Very Dissatisfied  1  2  3  4  5  Very Satisfied

Open-Ended:
"What could we improve?"
[Text box]

Demographic:
Age, role, industry, etc.

Net Promoter Score:
"How likely are you to recommend us to a colleague?"
0  1  2  3  4  5  6  7  8  9  10
(Not at all likely)     (Extremely likely)
```

#### Analytics Review

```
Key Metrics to Track:

Acquisition:
- Traffic sources
- Landing pages
- Sign-up conversion rate

Activation:
- Onboarding completion
- Time to first value
- Feature adoption

Engagement:
- Daily/Monthly active users
- Session duration
- Pages per session
- Feature usage

Retention:
- Churn rate
- Cohort analysis
- Return visitor rate

Revenue:
- Conversion rate
- Average order value
- Customer lifetime value

Funnel Analysis:
Homepage → Sign Up → Onboarding → First Action → Regular Use
100% → 35% → 60% → 45% → 25%
(Identify drop-off points)
```

#### A/B Testing

```
A/B Test Framework:

Hypothesis:
"Changing the CTA button from blue to green will increase click-through rate by 10%"

Variables:
- Control (A): Blue button
- Variant (B): Green button

Sample Size:
- Minimum 1,000 visitors per variant
- 95% statistical significance
- 80% statistical power

Duration:
- Run for at least 1 week
- Include full business cycle
- Enough time for significance

Metrics:
- Primary: Click-through rate
- Secondary: Conversion rate, time on page

Success Criteria:
- Variant B performs 10%+ better
- Statistically significant (p < 0.05)
- No negative impact on other metrics
```

---

## Usability Testing

### Planning Usability Tests

#### Test Objectives

```
Example: E-commerce Checkout

Research Questions:
1. Can users complete checkout in under 3 minutes?
2. Do users understand the shipping options?
3. Can users successfully apply a coupon code?
4. What causes users to abandon checkout?
5. Are error messages clear and helpful?

Success Metrics:
- Task completion rate: >90%
- Time on task: <3 minutes
- Error rate: <2 errors per session
- User satisfaction: >4/5
```

#### Participant Recruitment

```
Screening Criteria:

Required:
✓ Online shopper (purchases 2+ times/month)
✓ Age 25-45
✓ Comfortable with technology
✓ Has made mobile purchases

Excluded:
✗ UX professionals
✗ Company employees
✗ Participated in recent studies

Sample Size:
- 5-8 participants for qualitative insights
- 15-30 for quantitative metrics
- Test until patterns emerge (diminishing returns after 5)

Diversity:
- Mix of ages
- Different technical proficiency
- Various devices (desktop, mobile, tablet)
```

#### Test Script

```
Usability Test Script:

Introduction (5 min)
────────────────────
"Thank you for participating. Today we're testing a checkout process. There are no right or wrong answers - we're testing the design, not you. Please think aloud as you work. Any questions before we begin?"

Tasks (30 min)
──────────────
Task 1: Add product to cart
"Imagine you need a new pair of running shoes. Find a pair you like and add it to your cart."

Success: Product in cart
Time: 2 minutes
Metrics: Clicks, time, success rate

Task 2: Complete checkout
"Now complete your purchase. You can use this test credit card: [number]"

Success: Order confirmation
Time: 3 minutes
Observe: Friction points, errors, hesitations

Task 3: Apply coupon
"You just received coupon code SAVE10. Apply it to your order."

Success: Discount applied
Observe: Can they find coupon field? Is it clear?

Post-Task Questions (10 min)
─────────────────────────────
- "What was the easiest part?"
- "What was the most difficult?"
- "Was anything confusing?"
- "What would you change?"
- "Rate your overall experience 1-5"

Wrap-up (5 min)
───────────────
- Thank participant
- Provide incentive
- Answer any questions
```

### Test Methods

#### Moderated Testing

```
In-Person or Remote:

Setup:
- Moderator present
- Screen/audio recording
- Think-aloud protocol

Advantages:
✓ Can probe deeper
✓ Observe body language
✓ Clarify tasks
✓ Higher quality insights

Disadvantages:
✗ Time intensive
✗ Moderator bias
✗ Limited scale
✗ Scheduling challenges

Best for:
- Complex tasks
- Early-stage concepts
- Detailed feedback
```

#### Unmoderated Testing

```
Remote Self-Guided:

Setup:
- Online platform
- Written instructions
- Automated recording

Advantages:
✓ Faster results
✓ More participants
✓ Natural environment
✓ Cost-effective

Disadvantages:
✗ Can't probe deeper
✗ Technical issues
✗ Task misinterpretation
✗ Less rich data

Best for:
- Simple tasks
- Large sample sizes
- Quick validation
```

#### Guerrilla Testing

```
Quick Informal Testing:

Location:
- Coffee shops
- Libraries
- Public spaces

Approach:
1. Approach potential users
2. Offer small incentive ($5 coffee card)
3. Show design on laptop/phone
4. Ask 2-3 quick questions
5. Thank and move on

Duration: 5-10 minutes per person

Benefits:
✓ Very fast
✓ Low cost
✓ Real-world users
✓ Fresh perspectives

Limitations:
✗ Convenience sample
✗ Distracting environment
✗ Limited depth
```

### Analyzing Test Results

#### Quantitative Analysis

```
Task Performance Metrics:

Task Completion Rate:
Completed tasks / Total attempts
Example: 8/10 = 80% completion

Time on Task:
Average time to complete
Example: Mean = 2:34, Median = 2:15

Error Rate:
Errors / Total task attempts
Example: 12 errors / 10 users = 1.2 errors per user

System Usability Scale (SUS):
10 questions, 1-5 scale
Score: 0-100
- <60: Poor
- 60-70: OK
- 70-80: Good
- >80: Excellent
```

#### Qualitative Analysis

```
Thematic Analysis:

1. Collect Data:
   - Transcribe interviews
   - Compile observations
   - Gather quotes

2. Code Data:
   "The checkout button was hard to find" → Navigation
   "I didn't know if my order was processing" → Feedback
   "Too many form fields" → Form Design

3. Identify Patterns:
   Navigation issues: 7/8 participants
   Feedback concerns: 6/8 participants
   Form complaints: 5/8 participants

4. Prioritize Issues:
   Severity × Frequency = Priority
   
   Critical (P0):
   - 6 users couldn't find checkout button
   
   High (P1):
   - 5 users confused by shipping options
   
   Medium (P2):
   - 3 users wanted saved addresses
   
   Low (P3):
   - 2 users requested product recommendations
```

#### Rainbow Spreadsheet

```
Participant Findings Matrix:

Issue               | P1 | P2 | P3 | P4 | P5 | Total | Severity
─────────────────────────────────────────────────────────────────
Can't find checkout | ✓  | ✓  | ✓  |    | ✓  | 4/5   | Critical
Unclear shipping    |    | ✓  | ✓  | ✓  |    | 3/5   | High
Want saved cards    | ✓  |    | ✓  |    | ✓  | 3/5   | Medium
Confusing coupon    |    | ✓  |    | ✓  |    | 2/5   | Medium
Slow loading        | ✓  |    |    |    |    | 1/5   | Low

Green: Easy to fix, high impact
Yellow: Moderate effort/impact
Red: Difficult to fix or low impact
```

---

## Information Architecture

Information Architecture (IA) is the structural design of shared information environments. It organizes and labels content to support usability and findability.

### IA Components

#### Site Maps

```
Website Sitemap:

Home
│
├── Products
│   ├── Category 1
│   │   ├── Subcategory A
│   │   └── Subcategory B
│   ├── Category 2
│   └── Category 3
│
├── Solutions
│   ├── By Industry
│   ├── By Use Case
│   └── By Team Size
│
├── Resources
│   ├── Blog
│   ├── Documentation
│   ├── Tutorials
│   └── Case Studies
│
├── Pricing
│
├── Company
│   ├── About Us
│   ├── Team
│   ├── Careers
│   └── Contact
│
└── Support
    ├── Help Center
    ├── FAQ
    └── Contact Support
```

#### Navigation Systems

```
Primary Navigation:
- Products
- Solutions
- Resources
- Pricing
- Company

Secondary Navigation (Products):
- Browse by Category
- New Arrivals
- Best Sellers
- Sale Items

Utility Navigation:
- Search
- Account
- Cart
- Help

Breadcrumbs:
Home > Products > Electronics > Laptops > Gaming Laptops

Footer Navigation:
- Site map links
- Legal links
- Social media
- Newsletter signup
```

#### Taxonomy

```
Product Categorization:

Hierarchical:
Electronics
  └── Computers
      └── Laptops
          └── Gaming Laptops
              └── 15-inch Gaming Laptops

Faceted (Multiple ways to browse):
- By Category: Laptops
- By Brand: Dell, HP, Lenovo
- By Price: <$500, $500-$1000, >$1000
- By Features: Gaming, Business, Student
- By Screen Size: 13", 15", 17"
- By Rating: 4+ stars
```

### IA Methods

#### Card Sorting

```
Open Card Sorting:
- Participants group cards
- Create own category names
- Reveals mental models

Process:
1. Create 30-50 cards with content items
2. Ask users to group related items
3. Ask users to name each group
4. Analyze patterns across participants

Results:
Group 1 (75% agreement): "Account Settings"
  - Profile
  - Password
  - Notifications
  - Privacy

Group 2 (60% agreement): "Billing"
  - Payment Methods
  - Invoices
  - Subscription

Closed Card Sorting:
- Pre-defined categories
- Users place cards in categories
- Tests existing structure
```

#### Tree Testing

```
Tree Test Example:

Task: "Where would you find your purchase history?"

Tree Structure:
Home
├── Account
│   ├── Profile
│   ├── Orders ← Correct answer
│   ├── Settings
│   └── Payment Methods
├── Shopping
└── Help

Metrics:
- Success rate: Did they find it?
- Directness: Did they go straight there?
- Time: How long did it take?
- Path: What route did they take?

Results:
Success: 8/10 users
Average time: 12 seconds
Direct path: 6/10 users
Common mistake: 2 users looked in Shopping
```

#### Content Inventory

```
Content Audit Spreadsheet:

Page URL | Title | Description | Last Updated | Owner | Status | Action
─────────────────────────────────────────────────────────────────────
/about   | About| Company info| 2022-03-15  | Mktg  | Outdated | Rewrite
/pricing | Pricing | Plans   | 2024-01-10  | Sales | Current  | Keep
/blog/1  | Post1| Old topic   | 2020-05-20  | Mktg  | Outdated | Archive
/faq     | FAQ  | Questions   | 2023-08-14  | Support| Current | Update

Actions:
- Keep: Content is current and relevant
- Update: Needs minor revisions
- Rewrite: Needs major changes
- Archive: Move to archive, redirect
- Delete: Remove entirely
```

---

## Data Analysis and Iteration

### Metrics and KPIs

```
Product Metrics Framework:

Acquisition:
- Traffic sources
- Sign-up conversion rate
- Cost per acquisition (CPA)

Activation:
- Onboarding completion rate
- Time to first value
- Feature discovery rate

Engagement:
- Daily Active Users (DAU)
- Weekly Active Users (WAU)
- Sessions per user
- Time spent in app

Retention:
- Day 1, 7, 30 retention rates
- Churn rate
- Cohort retention curves

Revenue:
- Conversion rate
- Average revenue per user (ARPU)
- Customer lifetime value (LTV)
- LTV:CAC ratio

Referral:
- Net Promoter Score (NPS)
- Referral rate
- Viral coefficient
```

### Iteration Framework

```
Continuous Improvement Cycle:

1. MEASURE
   ↓
2. LEARN → 3. BUILD
   ↑           ↓
   ←───────────┘

Phase 1: MEASURE
- Collect quantitative data (analytics)
- Collect qualitative data (research)
- Define success metrics
- Identify problems

Phase 2: LEARN
- Analyze data
- Identify patterns
- Form hypotheses
- Prioritize issues

Phase 3: BUILD
- Design solutions
- Prototype
- Test
- Implement

Phase 4: MEASURE
- Monitor metrics
- Validate changes
- Document learnings
- Repeat cycle
```

### Prioritization

```
RICE Scoring:

Reach: How many users affected?
Impact: How much will it improve their experience?
  - 3 = Massive
  - 2 = High
  - 1 = Medium
  - 0.5 = Low
  - 0.25 = Minimal
Confidence: How sure are you?
  - 100% = High confidence
  - 80% = Medium
  - 50% = Low
Effort: How much work required? (person-months)

Score = (Reach × Impact × Confidence) / Effort

Example:
Feature: One-click checkout
Reach: 10,000 users/month
Impact: 2 (High)
Confidence: 80%
Effort: 2 person-months

Score = (10,000 × 2 × 0.8) / 2 = 8,000
```

---

## Tools and Resources

### Design Tools

```
Wireframing & Prototyping:
- Figma (collaborative, web-based)
- Sketch (Mac-only, powerful)
- Adobe XD (Adobe ecosystem)
- Balsamiq (low-fidelity, quick)
- Axure (high-fidelity, complex interactions)
- InVision (prototyping, feedback)

User Research:
- UserTesting.com (remote usability testing)
- Lookback (user interviews)
- Optimal Workshop (card sorting, tree testing)
- Hotjar (heatmaps, recordings)
- Maze (prototype testing)
- Dovetail (research repository)

Analytics:
- Google Analytics (web analytics)
- Mixpanel (product analytics)
- Amplitude (user behavior)
- Heap (auto-capture)
- FullStory (session replay)

Collaboration:
- Miro (whiteboarding)
- FigJam (brainstorming)
- Notion (documentation)
- Airtable (databases)
```

---

## Best Practices

### User Flow Best Practices

✅ **Do:**
- Start with user goals, not features
- Map all possible paths, including errors
- Keep flows simple and linear when possible
- Test flows with real users
- Update flows as product evolves
- Include edge cases and error states
- Document decision points clearly

❌ **Don't:**
- Assume users will follow the "happy path"
- Create flows in isolation from research
- Make flows too complex
- Forget mobile vs desktop differences
- Skip error and loading states
- Create flows without user validation

### Journey Mapping Best Practices

✅ **Do:**
- Base maps on real research data
- Include emotions and pain points
- Identify opportunities for improvement
- Share with entire team
- Update as you learn more
- Focus on specific personas and scenarios
- Make it visual and engaging

❌ **Don't:**
- Create based on assumptions
- Make it too detailed to be useful
- Forget to include touchpoints outside your product
- Create and forget
- Try to solve everything at once

### Testing Best Practices

✅ **Do:**
- Test early and often
- Test with representative users
- Record sessions (with permission)
- Focus on tasks, not features
- Ask open-ended questions
- Observe non-verbal cues
- Test competitors too
- Document and share findings

❌ **Don't:**
- Lead participants to answers
- Test only with colleagues
- Ask yes/no questions
- Defend your design during tests
- Test without a plan
- Ignore negative feedback
- Test only once

---

## Conclusion

User flows, journey mapping, wireframing, prototyping, research, and information architecture are all interconnected disciplines that inform great UX design. Success comes from understanding your users deeply, iterating based on data, and continuously improving the experience.

### Key Takeaways

**User Flows:**
- Map complete user journeys
- Include all paths and edge cases
- Test and validate with users
- Update as product evolves

**Research:**
- Combine qualitative and quantitative methods
- Test early and often
- Base decisions on data, not assumptions
- Include diverse user groups

**Prototyping:**
- Start low-fidelity, increase detail as needed
- Test before building
- Iterate quickly based on feedback
- Use appropriate fidelity for the question

**Information Architecture:**
- Organize content around user mental models
- Provide multiple ways to find information
- Keep navigation simple and predictable
- Test with card sorting and tree testing

**Iteration:**
- Measure everything that matters
- Learn from both successes and failures
- Prioritize based on impact and effort
- Build, measure, learn, repeat

Remember: The goal is not perfect designs, but continuously improving experiences that meet real user needs.
