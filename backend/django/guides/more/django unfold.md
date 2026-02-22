# django-unfold — The Complete Guide

> A thorough, example-driven reference for installing, configuring, and mastering django-unfold — the modern Tailwind CSS-based admin theme for Django.

**Current version as of this writing:** 0.80+
**Official docs:** https://unfoldadmin.com/docs/
**Live demo:** https://demo.unfoldadmin.com
**Source (demo project):** https://github.com/unfoldadmin/formula

---

## Table of Contents

1. [What is django-unfold and Why Use It](#1-what-is-django-unfold-and-why-use-it)
2. [How It Works Under the Hood](#2-how-it-works-under-the-hood)
3. [Installation](#3-installation)
4. [The UNFOLD Settings Dictionary](#4-the-unfold-settings-dictionary)
5. [Registering Models — ModelAdmin](#5-registering-models--modeladmin)
6. [The @display Decorator](#6-the-display-decorator)
7. [Actions](#7-actions)
8. [Filters](#8-filters)
9. [Tabs — Organizing Complex Forms](#9-tabs--organizing-complex-forms)
10. [Inlines](#10-inlines)
11. [Widgets](#11-widgets)
12. [Building a Custom Dashboard](#12-building-a-custom-dashboard)
13. [Sidebar Navigation](#13-sidebar-navigation)
14. [Theming and Colors](#14-theming-and-colors)
15. [Custom Pages](#15-custom-pages)
16. [User & Group Admin Setup](#16-user--group-admin-setup)
17. [Third-Party Integrations](#17-third-party-integrations)
18. [Running the Default Admin Alongside Unfold](#18-running-the-default-admin-alongside-unfold)
19. [Common Pitfalls & Troubleshooting](#19-common-pitfalls--troubleshooting)
20. [Checklist](#20-checklist)

---

## 1. What is django-unfold and Why Use It

Django ships with a built-in admin panel. It works, but it is visually dated and difficult to extend in any meaningful way. The default admin uses a Bootstrap-era stylesheet that has not fundamentally changed in years, and customizing it beyond surface-level tweaks requires overriding templates in fragile, undocumented ways.

**django-unfold** solves this by sitting on top of `django.contrib.admin` — not replacing it — and overriding its templates, styles, and some behaviors to deliver a modern, clean, production-grade admin interface built with Tailwind CSS.

The key distinction from similar libraries like Jazzmin or Django Suit is that Unfold is built natively on Tailwind CSS, uses Alpine.js for interactivity, and HTMX for AJAX behaviors. It does not ship a compiled stylesheet that you have to accept — it ships a prebuilt Tailwind stylesheet that you can extend with your own design tokens.

**What Unfold gives you out of the box:**

- A clean, modern UI with light and dark mode
- Sidebar navigation with grouping, collapsible sections, and badge counts
- A command palette (Cmd/Ctrl + K) to search across all registered models
- Custom dashboard support with reusable components (cards, charts, tables, progress bars)
- Richer actions: per-row actions, detail-page actions, submit-line actions, dropdown action groups
- Advanced filter widgets: date ranges, numeric ranges, autocomplete dropdowns, checkboxes, radio buttons
- Tabs on change forms and changelists for organizing complex models
- Sortable inlines (drag and drop), paginated inlines, and non-related inlines
- A WYSIWYG editor widget (Trix) and array field widget
- Conditional (show/hide) fields based on other field values
- An environment label so you always know which environment you are in
- An "unsaved changes" warning before navigating away from an edited form

**What Unfold does NOT do:**

- It does not replace or fight Django's admin architecture. Everything you know about `ModelAdmin`, `list_display`, `search_fields`, `fieldsets`, etc. still applies exactly as before.
- It does not require any database migrations.
- It does not change how your models work.

If you know Django admin, the learning curve is minimal. You change one import and get a modern UI immediately.

---

## 2. How It Works Under the Hood

Understanding this prevents confusion.

Unfold overrides Django admin's templates by placing its own templates earlier in Django's template loading order. When Django renders the admin, it finds Unfold's `admin/base_site.html` before Django's own version. Unfold's templates inject Tailwind CSS, Alpine.js, and HTMX, then reconstruct the UI around the same data Django admin already provides.

Your `ModelAdmin` classes are still standard Django `ModelAdmin` subclasses — Unfold simply provides an enhanced base class (`unfold.admin.ModelAdmin`) that you inherit from instead. If you forget to use Unfold's base class, your admin page will work but will be completely unstyled.

```
Request hits /admin/
    -> Django's admin machinery resolves the view (no change)
    -> Django admin renders using its template system
    -> Template engine finds unfold's templates first
    -> Unfold templates render Tailwind UI + Alpine.js + HTMX
    -> Your ModelAdmin data (list_display, fieldsets, etc.) is unchanged
```

This design means:
- All standard Django admin documentation still applies
- Third-party apps that extend Django admin (like `django-import-export`) can be integrated, though they may need style adjustments
- You can migrate incrementally: one model at a time

---

## 3. Installation

### Step 1: Install the package

```bash
pip install django-unfold

# or with uv
uv add django-unfold

# or with poetry
poetry add django-unfold
```

### Step 2: Add to INSTALLED_APPS

This is the most common mistake. `"unfold"` must appear **before** `"django.contrib.admin"`. If it appears after, Django finds the default admin templates first and Unfold's styles never load.

```python
# settings.py
INSTALLED_APPS = [
    "unfold",                            # MUST be first, before django.contrib.admin
    "unfold.contrib.filters",            # Optional: date, numeric, autocomplete filters
    "unfold.contrib.forms",              # Optional: WYSIWYG, array widgets
    "unfold.contrib.inlines",            # Optional: sortable, paginated inlines
    "unfold.contrib.import_export",      # Optional: django-import-export styling
    "unfold.contrib.guardian",           # Optional: django-guardian integration
    "unfold.contrib.simple_history",     # Optional: django-simple-history integration
    "django.contrib.admin",              # Required: must come after unfold
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # your apps...
]
```

Only include `unfold.contrib.*` sub-apps for features you actually use. Each one adds a dependency but no harm if left out.

### Step 3: urls.py (no change required)

Your existing URL configuration works as-is:

```python
# urls.py
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
```

### Step 4: Run collectstatic

In production, styles will be completely missing if you do not run collectstatic:

```bash
python manage.py collectstatic
```

### Step 5: Update your ModelAdmin classes

Every `ModelAdmin` in your project must now inherit from `unfold.admin.ModelAdmin` instead of `django.contrib.admin.ModelAdmin`. This is what loads Unfold's styling and extra features for that model.

```python
# Before
from django.contrib import admin

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ["name", "status"]

# After — only the import changes
from django.contrib import admin
from unfold.admin import ModelAdmin  # <-- change this import

@admin.register(MyModel)
class MyModelAdmin(ModelAdmin):      # <-- and this base class
    list_display = ["name", "status"]
```

Everything else in your existing `ModelAdmin` — `list_display`, `list_filter`, `search_fields`, `fieldsets`, `inlines`, `readonly_fields`, etc. — stays completely the same.

---

## 4. The UNFOLD Settings Dictionary

All Unfold-specific configuration lives in a single `UNFOLD` dictionary in your `settings.py`. None of these keys are required — the admin works with no `UNFOLD` setting at all, just without customization.

Below is a complete, annotated reference of the most important settings:

```python
# settings.py
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    # -------------------------------------------------------------------------
    # Site branding
    # -------------------------------------------------------------------------
    "SITE_TITLE": "My Company Admin",        # Appears in the browser <title> tag
    "SITE_HEADER": "My Company",             # Large text at the top of the sidebar
    "SITE_SUBHEADER": "Internal Tools",      # Smaller text under SITE_HEADER
    "SITE_URL": "/",                         # Where clicking the site title goes

    # Logo — provide separate images for light and dark mode
    # These are callables (lambdas) so they work with whitenoise/S3 in production
    "SITE_LOGO": {
        "light": lambda request: static("img/logo-light.svg"),
        "dark": lambda request: static("img/logo-dark.svg"),
    },

    # Favicon
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("img/favicon.svg"),
        },
    ],

    # -------------------------------------------------------------------------
    # History and view-on-site buttons
    # -------------------------------------------------------------------------
    "SHOW_HISTORY": True,       # Show "History" button on change form. Default: True
    "SHOW_VIEW_ON_SITE": True,  # Show "View on site" button. Default: True

    # -------------------------------------------------------------------------
    # Environment label
    # Displays a colored badge in the top-right corner of the header.
    # Extremely useful on staging/production to avoid confusing environments.
    # The callback must return [label_text, color_type]
    # color_type choices: "info", "danger", "warning", "success"
    # -------------------------------------------------------------------------
    "ENVIRONMENT": "myapp.admin_config.environment_callback",

    # -------------------------------------------------------------------------
    # Dashboard
    # The callback receives (request, context) and must return the modified context.
    # Use it to inject any data you want available in your dashboard template.
    # -------------------------------------------------------------------------
    "DASHBOARD_CALLBACK": "myapp.admin_config.dashboard_callback",

    # -------------------------------------------------------------------------
    # Tabs — global tab navigation across models
    # Can be a list (static) or a dotted path to a callable (dynamic)
    # -------------------------------------------------------------------------
    "TABS": [
        {
            "models": ["myapp.order", "myapp.orderitem"],
            "items": [
                {
                    "title": _("Orders"),
                    "link": reverse_lazy("admin:myapp_order_changelist"),
                },
                {
                    "title": _("Order Items"),
                    "link": reverse_lazy("admin:myapp_orderitem_changelist"),
                },
            ],
        },
    ],

    # -------------------------------------------------------------------------
    # Sidebar
    # -------------------------------------------------------------------------
    "SIDEBAR": {
        "show_search": True,              # Show a search box in the sidebar
        "show_all_applications": False,   # Auto-list all registered apps
        # navigation is a list of app/section groups (see Section 13)
        "navigation": [
            {
                "title": _("Users"),
                "collapsible": True,
                "items": [
                    {
                        "title": _("All Users"),
                        "link": reverse_lazy("admin:auth_user_changelist"),
                        "badge": "myapp.admin_config.user_count_badge",
                    },
                    {
                        "title": _("Groups"),
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # Login page customization
    # -------------------------------------------------------------------------
    "LOGIN": {
        "image": lambda request: static("img/login-bg.jpg"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },

    # -------------------------------------------------------------------------
    # Border radius — applied globally to cards, buttons, inputs, etc.
    # -------------------------------------------------------------------------
    "BORDER_RADIUS": "6px",

    # -------------------------------------------------------------------------
    # Custom CSS / JS — loaded on every admin page
    # These are callables so they resolve correctly with hashed filenames
    # -------------------------------------------------------------------------
    "STYLES": [
        lambda request: static("css/admin-custom.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/admin-custom.js"),
    ],

    # -------------------------------------------------------------------------
    # Colors — full Tailwind-compatible color scale (oklch format)
    # You only need to define "primary" to match your brand.
    # Leave "base" as default unless you need custom grays.
    # -------------------------------------------------------------------------
    "COLORS": {
        "primary": {
            "50":  "oklch(97.7% .014 308.299)",
            "100": "oklch(94.6% .033 307.174)",
            "200": "oklch(90.2% .063 306.703)",
            "300": "oklch(82.7% .119 306.383)",
            "400": "oklch(71.4% .203 305.504)",
            "500": "oklch(58.5% .275 304.052)",
            "600": "oklch(52.3% .266 303.724)",
            "700": "oklch(44.4% .234 303.349)",
            "800": "oklch(38.8% .197 304.162)",
            "900": "oklch(33.5% .157 303.718)",
            "950": "oklch(27.1% .119 303.079)",
        },
    },
}
```

### Callback Functions

Many settings accept either a static value or a dotted-path string pointing to a callable. This is intentional — it gives you the power of Python functions while keeping configuration in `settings.py` clean.

```python
# myapp/admin_config.py

def environment_callback(request):
    """
    Return [label, color_type] based on the current environment.
    color_type: "info" | "danger" | "warning" | "success"
    """
    from django.conf import settings
    if settings.DEBUG:
        return ["Development", "warning"]
    return ["Production", "danger"]


def dashboard_callback(request, context):
    """
    Inject extra data into the admin index template.
    context already contains all standard Django admin context variables.
    """
    from myapp.models import Order, User
    context.update({
        "total_users": User.objects.count(),
        "pending_orders": Order.objects.filter(status="pending").count(),
        "recent_orders": Order.objects.order_by("-created_at")[:5],
    })
    return context


def user_count_badge(request):
    """Return a number for the badge next to a sidebar item."""
    from django.contrib.auth import get_user_model
    return get_user_model().objects.filter(is_active=True).count()
```

---

## 5. Registering Models — ModelAdmin

This is where you spend most of your time. Unfold's `ModelAdmin` is a drop-in replacement for Django's, with additional options layered on top.

### Minimal Example

```python
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Product

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ["name", "price", "is_active", "created_at"]
    list_filter = ["is_active", "category"]
    search_fields = ["name", "sku"]
    ordering = ["-created_at"]
```

### All Unfold-Specific ModelAdmin Options

These are the extra options Unfold adds on top of the standard Django `ModelAdmin` options. The standard options (`list_display`, `fieldsets`, `inlines`, etc.) all still work exactly as documented by Django.

```python
from django.contrib import admin
from unfold.admin import ModelAdmin

@admin.register(MyModel)
class MyModelAdmin(ModelAdmin):

    # --- Layout options ---

    # Render form fields in a compact, single-column layout
    # Good for models with many fields — saves vertical space
    compressed_fields = True                  # Default: False

    # Show a warning dialog when the user tries to navigate away
    # from a change form that has unsaved edits
    warn_unsaved_form = True                  # Default: False

    # Make the changelist table span the full width of the page
    # (no sidebar gutter). Good for tables with many columns.
    list_fullwidth = True                     # Default: False

    # By default filters appear in a slide-out sheet from the right.
    # Set to False to render filters in the traditional sidebar column.
    list_filter_sheet = True                  # Default: True

    # Show a submit button inside the filter panel.
    # Required for any filter that has a text/number input, because
    # without a submit button the user has no way to apply the filter.
    list_filter_submit = True                 # Default: False

    # Place the horizontal scrollbar at the top of the changelist table
    # instead of the bottom. Useful for very wide tables.
    list_horizontal_scrollbar_top = True      # Default: False

    # Disable the "select all" checkbox in the changelist header
    list_disable_select_all = False           # Default: False

    # --- Readonly field preprocessing ---
    # Pre-process the content of readonly fields before they are rendered.
    # The value is either a dotted Python import path (string) or a callable.
    # Useful for rendering raw HTML stored in a field, or stripping whitespace.
    readonly_preprocess_fields = {
        "description": "html.unescape",                  # Built-in module function
        "notes": lambda content: content.strip(),         # Lambda
        "raw_html": "django.utils.html.mark_safe",        # Django utility
    }

    # --- Custom action placement (see Section 7 for full detail) ---
    actions_list = []        # Actions shown above the changelist results table
    actions_row = []         # Actions shown inline in each table row
    actions_detail = []      # Actions shown at the top of the change form
    actions_submit_line = [] # Actions shown next to the Save button on the change form

    # Hide any default actions (from Django or third-party packages)
    # that you do not want visible alongside your custom actions
    actions_list_hide_default = False
    actions_detail_hide_default = False
```

### Using Fieldsets

Fieldsets work exactly as in standard Django admin but render with nicer styling in Unfold:

```python
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    fieldsets = (
        ("Basic Information", {
            "fields": ("user", "status", "total_amount"),
        }),
        ("Shipping", {
            "fields": ("shipping_address", "tracking_number"),
            "classes": ("collapse",),  # Standard Django collapse still works
        }),
        ("Internal Notes", {
            "fields": ("notes", "internal_flag"),
            "description": "These fields are not visible to customers.",
        }),
    )
```

---

## 6. The @display Decorator

Unfold provides its own `@display` decorator that extends Django's built-in `@admin.display`. It adds visual enhancements for list columns — most notably colored status labels.

### Basic Usage

```python
from unfold.decorators import display

class OrderAdmin(ModelAdmin):
    list_display = ["order_number", "show_status", "customer_name"]

    @display(description="Status", ordering="status")
    def show_status(self, obj):
        return obj.status   # Simple text, no special styling
```

### Status Labels with Color Mapping

The most useful feature. Use `label=True` or `label={value: color}` to render the column value as a colored badge rather than plain text.

```python
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _
from unfold.decorators import display

class Order(models.Model):
    class Status(TextChoices):
        PENDING    = "pending",   _("Pending")
        CONFIRMED  = "confirmed", _("Confirmed")
        SHIPPED    = "shipped",   _("Shipped")
        DELIVERED  = "delivered", _("Delivered")
        CANCELLED  = "cancelled", _("Cancelled")

class OrderAdmin(ModelAdmin):
    list_display = ["order_number", "show_status"]

    @display(
        description=_("Status"),
        ordering="status",
        label={
            # Map each value to a color
            # Available colors: "success", "info", "warning", "danger"
            Order.Status.PENDING:   "warning",
            Order.Status.CONFIRMED: "info",
            Order.Status.SHIPPED:   "info",
            Order.Status.DELIVERED: "success",
            Order.Status.CANCELLED: "danger",
        },
    )
    def show_status(self, obj):
        return obj.status   # Return the raw value; Unfold looks it up in the label map

    # If you want a custom display label alongside the color,
    # return a tuple: (value_for_color_lookup, display_text)
    @display(
        description=_("Payment"),
        label={"paid": "success", "failed": "danger", "pending": "warning"},
    )
    def show_payment_status(self, obj):
        return obj.payment_status, obj.get_payment_status_display()
```

### Two-Line Heading in List

For a richer list cell that shows a primary and secondary value stacked:

```python
@display(description=_("Customer"), header=True)
def show_customer(self, obj):
    # Return a list: [primary_text, secondary_text]
    # Optional third element: initials string (shown in a circle avatar)
    return [obj.user.get_full_name(), obj.user.email, obj.user.first_name[0]]
```

### Boolean Columns

Standard Django boolean display works as always, but use `boolean=True` on `@display` for computed boolean properties:

```python
@display(description=_("Has Items"), boolean=True)
def has_items(self, obj):
    return obj.items.exists()
```

---

## 7. Actions

Django admin has one type of action: bulk actions on selected rows in the changelist. Unfold expands this to four distinct action placement options, each serving a different UX purpose.

### The Four Action Types

```
Changelist page:
  [actions_list]          <- Button bar above the results table (global actions)
  
  [ ] Name   Status  ...  [actions_row button]   <- Per-row action in each table row
  [ ] Name   Status  ...  [actions_row button]

Change form page:
  [actions_detail]        <- Button bar at the top of the change form

  [field] [field] [field]
  ...
  [Save] [Save and continue] [actions_submit_line]  <- Next to the save buttons
```

### Defining Actions

```python
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest
from django.db.models import QuerySet
from unfold.admin import ModelAdmin
from unfold.decorators import action

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # Register which methods serve as which action type
    actions_list    = ["export_all_orders"]
    actions_row     = ["mark_shipped"]
    actions_detail  = ["duplicate_order"]
    actions_submit_line = ["save_and_notify"]

    # --- Changelist global action ---
    # Shown above the table, always visible (not tied to row selection)
    # Must accept (self, request) — no queryset, it's not a row action
    @action(description=_("Export all"), url_path="export-all")
    def export_all_orders(self, request: HttpRequest):
        # Do work, then return a response or redirect
        from django.shortcuts import redirect
        # ... generate export ...
        return redirect("admin:myapp_order_changelist")

    # --- Per-row action ---
    # Rendered as a button in each table row
    # Must accept (self, request, object_id)
    @action(description=_("Ship"), url_path="ship")
    def mark_shipped(self, request: HttpRequest, object_id: int):
        order = Order.objects.get(pk=object_id)
        order.status = "shipped"
        order.save()
        self.message_user(request, f"Order {object_id} marked as shipped.")
        from django.shortcuts import redirect
        return redirect("admin:myapp_order_changelist")

    # --- Change form top action ---
    # Shown at the top of the edit page for a specific object
    @action(description=_("Duplicate"), url_path="duplicate")
    def duplicate_order(self, request: HttpRequest, object_id: int):
        order = Order.objects.get(pk=object_id)
        order.pk = None
        order.save()
        self.message_user(request, "Order duplicated.")
        from django.shortcuts import redirect
        return redirect("admin:myapp_order_change", args=[order.pk])

    # --- Submit line action ---
    # Shown next to the Save button. Receives the object being saved.
    @action(description=_("Save & Notify"))
    def save_and_notify(self, request: HttpRequest, obj: Order):
        obj.save()
        send_notification.delay(obj.id)
        self.message_user(request, "Order saved and notification sent.")
```

### Standard Bulk Actions Still Work

The standard Django bulk action pattern (selecting rows and using the action dropdown) still works exactly as before:

```python
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    actions = ["deactivate_selected"]

    @admin.action(description="Deactivate selected products")
    def deactivate_selected(self, request: HttpRequest, queryset: QuerySet):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} products deactivated.")
```

### Action Permissions

```python
@action(
    description=_("Export"),
    permissions=["export"],                  # Custom permission name
    # OR use existing Django permissions:
    # permissions=["auth.view_user"]         # Dot-notation = Django permission
)
def export_action(self, request, queryset):
    pass

# For custom permissions, define the corresponding has_<name>_permission method:
def has_export_permission(self, request, obj=None):
    return request.user.has_perm("myapp.can_export_orders")
```

---

## 8. Filters

Unfold extends Django's built-in filter system with richer widgets. To use them, make sure `"unfold.contrib.filters"` is in `INSTALLED_APPS`.

### Standard Filters (No Change)

Standard Django filters still work and are automatically styled:

```python
class OrderAdmin(ModelAdmin):
    list_filter = ["status", "is_active", "created_at"]
```

### Unfold's Enhanced Filter Types

```python
from unfold.contrib.filters.admin import (
    RangeDateFilter,          # Date range with a date picker
    RangeDateTimeFilter,      # Datetime range with a datetime picker
    RangeNumericFilter,       # Numeric range (min/max inputs)
    SingleNumericFilter,      # Single number input filter
    SliderNumericFilter,      # Range slider widget
    DropdownFilter,           # Single-select dropdown
    MultipleDropdownFilter,   # Multi-select checkbox dropdown
    ChoiceDropdownFilter,     # Dropdown based on field.choices
    RelatedDropdownFilter,    # FK/M2M with autocomplete dropdown
    AutocompleteFilter,       # Searchable autocomplete filter
    CheckboxFilter,           # Checkbox for boolean fields
)
```

### Example: Combining Filter Types

```python
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # IMPORTANT: When using filters that have text/numeric inputs,
    # set list_filter_submit = True so users can submit the filter form.
    list_filter_submit = True

    list_filter = [
        # Date range picker — for filtering by a date range
        ("created_at", RangeDateFilter),

        # Numeric range — filter orders by total amount
        ("total_amount", RangeNumericFilter),

        # Single dropdown — styled status filter
        ("status", ChoiceDropdownFilter),

        # Multi-select — filter by multiple categories at once
        ("category", MultipleDropdownFilter),

        # Standard boolean filter — styled automatically by Unfold
        "is_active",

        # Autocomplete filter for a ForeignKey
        # Note: the related model's admin must define search_fields
        ("user", RelatedDropdownFilter),
    ]
```

### Filter Layout

By default, Unfold renders filters in a slide-out sheet that appears from the right when the user clicks "Filters". To use the traditional sidebar layout instead:

```python
class OrderAdmin(ModelAdmin):
    list_filter_sheet = False   # Filters appear in a sidebar column on the left
```

---

## 9. Tabs — Organizing Complex Forms

Tabs let you split a complex change form or changelist into organized sections without making users scroll through a massive page.

### Fieldset Tabs (Within a Single Change Form)

Group fieldsets into tab panels on the change form:

```python
@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    fieldsets = (
        # Tab 1 — the tab name comes from the fieldset name
        ("Personal Info", {
            "fields": ("first_name", "last_name", "email", "phone"),
            "classes": ("tab",),     # <-- this fieldset becomes a tab
        }),
        # Tab 2
        ("Address", {
            "fields": ("street", "city", "country", "postal_code"),
            "classes": ("tab",),
        }),
        # Tab 3
        ("Settings", {
            "fields": ("notifications_enabled", "theme_preference"),
            "classes": ("tab",),
        }),
    )
```

### Inline Tabs (Grouping Inlines Into Tabs)

Rather than stacking all inlines below the form, group them into tabs:

```python
from unfold.contrib.inlines.admin import TabularInline

class OrderItemInline(TabularInline):
    model = OrderItem
    tab = True   # This inline becomes a tab panel

class OrderNoteInline(TabularInline):
    model = OrderNote
    tab = True

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    inlines = [OrderItemInline, OrderNoteInline]
    # Each inline with tab=True appears as a tab at the top of the change form
```

### Global Navigation Tabs (Linking Related Models)

Cross-model tab navigation, configured in the `UNFOLD` settings:

```python
# settings.py
UNFOLD = {
    "TABS": [
        {
            # These models show the tab bar when viewed
            "models": ["myapp.order", "myapp.orderitem", "myapp.orderreturn"],
            "items": [
                {
                    "title": _("Orders"),
                    "link": reverse_lazy("admin:myapp_order_changelist"),
                },
                {
                    "title": _("Order Items"),
                    "link": reverse_lazy("admin:myapp_orderitem_changelist"),
                },
                {
                    "title": _("Returns"),
                    "link": reverse_lazy("admin:myapp_orderreturn_changelist"),
                },
            ],
        },
    ],
}
```

When a user visits any of the listed model admin pages, the tab bar appears at the top — making it easy to navigate between related models without going back to the sidebar.

---

## 10. Inlines

Unfold provides enhanced inline classes from `unfold.contrib.inlines`. Add `"unfold.contrib.inlines"` to `INSTALLED_APPS` to use them.

### Available Inline Classes

```python
from unfold.contrib.inlines.admin import (
    TabularInline,      # Standard tabular inline with Unfold styling
    StackedInline,      # Standard stacked inline with Unfold styling
    NonrelatedTabularInline,   # Inline that shows non-related model rows
    NonrelatedStackedInline,
    SortableTabularInline,     # Tabular inline with drag-and-drop row sorting
    SortableStackedInline,
)
```

### Sortable Inlines

Allows users to reorder inline items by dragging:

```python
from unfold.contrib.inlines.admin import SortableTabularInline

class MenuItemInline(SortableTabularInline):
    model = MenuItem
    fields = ["name", "url", "order"]
    # The field used to store sort order must be defined on the model
    # and named to match the sortable_field_name attribute:
    sortable_field_name = "order"  # Default: "order"

@admin.register(Menu)
class MenuAdmin(ModelAdmin):
    inlines = [MenuItemInline]
```

### Paginated Inlines

For parent models with many related objects, paginated inlines avoid loading hundreds of rows:

```python
from unfold.contrib.inlines.admin import TabularInline

class OrderItemInline(TabularInline):
    model = OrderItem
    per_page = 10          # Show 10 items per page in the inline

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    inlines = [OrderItemInline]
```

### Non-Related Inlines

Display rows from a completely unrelated model on a change form. Useful for dashboards or admin pages where you want to show contextual data.

```python
from unfold.contrib.inlines.admin import NonrelatedTabularInline
from myapp.models import AuditLog

class UserAuditLogInline(NonrelatedTabularInline):
    model = AuditLog
    fields = ["action", "timestamp", "ip_address"]
    readonly_fields = ["action", "timestamp", "ip_address"]

    def get_form_queryset(self, obj):
        # obj is the parent User being viewed
        # Return the queryset of AuditLog rows you want to display
        return AuditLog.objects.filter(user=obj).order_by("-timestamp")[:20]

    def save_new_instance(self, parent, instance):
        # Called when a new inline row is saved.
        # Link it to the parent object here.
        instance.user = parent
        instance.save()

@admin.register(User)
class UserAdmin(ModelAdmin):
    inlines = [UserAuditLogInline]
```

---

## 11. Widgets

Unfold provides two extra widgets for special field types. Add `"unfold.contrib.forms"` to `INSTALLED_APPS`.

### WYSIWYG Widget (Trix Editor)

Replaces a `TextField` with a rich text editor using the Trix library:

```python
from django.db import models
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.admin import ModelAdmin

@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    formfield_overrides = {
        models.TextField: {"widget": WysiwygWidget},
    }
```

Or target a specific field only:

```python
from django import forms
from unfold.contrib.forms.widgets import WysiwygWidget

class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "body": WysiwygWidget(),
            "summary": WysiwygWidget(),
        }

@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    form = ArticleAdminForm
```

### Array Widget (PostgreSQL ArrayField)

For `django.contrib.postgres.fields.ArrayField` — renders as a dynamic list of inputs:

```python
from django.contrib.postgres.fields import ArrayField
from unfold.contrib.forms.widgets import ArrayWidget

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    formfield_overrides = {
        ArrayField: {"widget": ArrayWidget},
    }
```

### Conditional Fields (Show/Hide Based on Other Fields)

Make fields conditionally visible based on the value of another field. This requires no JavaScript to write — it is configured declaratively:

```python
@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                "type",           # The controlling field
                "email_address",  # Only visible when type == "email"
                "phone_number",   # Only visible when type == "sms"
                "webhook_url",    # Only visible when type == "webhook"
            )
        }),
    )

    # Map each field to the condition that makes it visible
    # Format: {"field_name": "controlling_field_name__exact=value"}
    conditional_fields = {
        "email_address": "type__exact=email",
        "phone_number":  "type__exact=sms",
        "webhook_url":   "type__exact=webhook",
    }
```

---

## 12. Building a Custom Dashboard

By default, the Django admin index page shows a list of registered apps and a history log. Unfold makes it easy to replace this with a genuinely useful dashboard showing real business data.

### Step 1: Configure the Dashboard Callback

```python
# settings.py
UNFOLD = {
    "DASHBOARD_CALLBACK": "myapp.admin_config.dashboard_callback",
}
```

### Step 2: Write the Callback

```python
# myapp/admin_config.py
from django.utils import timezone

def dashboard_callback(request, context):
    from myapp.models import Order, User, Product

    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)

    context.update({
        "kpis": {
            "total_users":       User.objects.count(),
            "active_users":      User.objects.filter(is_active=True).count(),
            "orders_today":      Order.objects.filter(created_at__date=today).count(),
            "revenue_30d":       Order.objects.filter(
                                     created_at__date__gte=thirty_days_ago
                                 ).aggregate(total=Sum("total_amount"))["total"] or 0,
        },
        "recent_orders": Order.objects.select_related("user").order_by("-created_at")[:10],
        "low_stock_products": Product.objects.filter(stock__lt=10).order_by("stock")[:5],
    })
    return context
```

### Step 3: Create the Template

Create the file at `templates/admin/index.html` in your project. Unfold will find this template before Django's default admin index.

```html
{% extends "admin/index.html" %}
{% load i18n unfold %}

{% block content %}

{# Stat cards row #}
{% component "unfold/components/flex.html" with class="gap-4 mb-8" %}
    {% component "unfold/components/card.html" %}
        {% component "unfold/components/title.html" %}
            Total Users
        {% endcomponent %}
        {% component "unfold/components/text.html" %}
            {{ kpis.total_users }}
        {% endcomponent %}
    {% endcomponent %}

    {% component "unfold/components/card.html" %}
        {% component "unfold/components/title.html" %}
            Orders Today
        {% endcomponent %}
        {% component "unfold/components/text.html" %}
            {{ kpis.orders_today }}
        {% endcomponent %}
    {% endcomponent %}

    {% component "unfold/components/card.html" %}
        {% component "unfold/components/title.html" %}
            30-Day Revenue
        {% endcomponent %}
        {% component "unfold/components/text.html" %}
            ${{ kpis.revenue_30d|floatformat:2 }}
        {% endcomponent %}
    {% endcomponent %}
{% endcomponent %}

{# Recent orders table #}
{% component "unfold/components/card.html" %}
    {% component "unfold/components/title.html" %}
        Recent Orders
    {% endcomponent %}

    {% component "unfold/components/table.html" with card_included=1 %}
        {% component "unfold/components/table_header.html" %}
            {% component "unfold/components/table_row.html" %}
                {% for label in "Order,Customer,Status,Amount,Date"|split:"," %}
                    {% component "unfold/components/table_header_cell.html" %}
                        {{ label }}
                    {% endcomponent %}
                {% endfor %}
            {% endcomponent %}
        {% endcomponent %}

        {% component "unfold/components/table_body.html" %}
            {% for order in recent_orders %}
                {% component "unfold/components/table_row.html" %}
                    {% component "unfold/components/table_cell.html" %}
                        {{ order.id }}
                    {% endcomponent %}
                    {% component "unfold/components/table_cell.html" %}
                        {{ order.user.email }}
                    {% endcomponent %}
                    {% component "unfold/components/table_cell.html" %}
                        {{ order.get_status_display }}
                    {% endcomponent %}
                    {% component "unfold/components/table_cell.html" %}
                        ${{ order.total_amount }}
                    {% endcomponent %}
                    {% component "unfold/components/table_cell.html" %}
                        {{ order.created_at|date:"M d, Y" }}
                    {% endcomponent %}
                {% endcomponent %}
            {% endfor %}
        {% endcomponent %}
    {% endcomponent %}
{% endcomponent %}

{% endblock %}
```

### Available Components

Unfold's component library lets you compose dashboards declaratively without writing custom CSS. Components nest inside each other using Django's template tag system.

| Component | Purpose |
|---|---|
| `unfold/components/card.html` | A white rounded card container |
| `unfold/components/flex.html` | A flexbox row container |
| `unfold/components/title.html` | Section title text |
| `unfold/components/text.html` | Body text |
| `unfold/components/table.html` | A data table |
| `unfold/components/table_header.html` | Table `<thead>` |
| `unfold/components/table_body.html` | Table `<tbody>` |
| `unfold/components/table_row.html` | A `<tr>` |
| `unfold/components/table_header_cell.html` | A `<th>` |
| `unfold/components/table_cell.html` | A `<td>` |
| `unfold/components/chart.html` | Chart.js chart wrapper |
| `unfold/components/button.html` | A styled button |
| `unfold/components/progress.html` | A progress bar |
| `unfold/components/layer.html` | A section layer with padding |

---

## 13. Sidebar Navigation

The sidebar is one of the most visible parts of Unfold. You configure it in the `UNFOLD["SIDEBAR"]` dictionary.

### Full Navigation Configuration

```python
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SIDEBAR": {
        "show_search": True,           # Show a search input in the sidebar
        "show_all_applications": False, # If True, auto-list all registered apps (ignore navigation)
        "navigation": [
            # Each entry is a group/section in the sidebar
            {
                "title": _("Dashboard"),
                "separator": False,    # Draw a horizontal line above this group
                "collapsible": False,  # Whether this group can be collapsed
                "items": [
                    {
                        "title": _("Overview"),
                        "link": reverse_lazy("admin:index"),
                        # "icon": "dashboard",  # Material Symbols icon name
                        # Badge shows a number next to the item
                        # Provide a dotted path to a callable that returns an integer
                        "badge": "myapp.admin_config.pending_orders_count",
                        # "permission": "myapp.admin_config.can_view_dashboard",
                    },
                ],
            },
            {
                "title": _("Orders"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("All Orders"),
                        "link": reverse_lazy("admin:myapp_order_changelist"),
                        "badge": "myapp.admin_config.pending_orders_count",
                    },
                    {
                        "title": _("Returns"),
                        "link": reverse_lazy("admin:myapp_orderreturn_changelist"),
                    },
                    {
                        "title": _("Invoices"),
                        "link": reverse_lazy("admin:myapp_invoice_changelist"),
                    },
                ],
            },
            {
                "title": _("Catalog"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Products"),
                        "link": reverse_lazy("admin:myapp_product_changelist"),
                    },
                    {
                        "title": _("Categories"),
                        "link": reverse_lazy("admin:myapp_category_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Permissions"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("External Links"),
                "separator": True,
                "items": [
                    {
                        "title": _("API Docs"),
                        "link": "https://api.mysite.com/docs/",
                        # External links open in a new tab automatically
                    },
                    {
                        "title": _("Sentry"),
                        "link": "https://sentry.io/organizations/myorg/",
                    },
                ],
            },
        ],
    },
}
```

### Permission-Gating Sidebar Items

Each sidebar item can have a `"permission"` key pointing to a callable. If the callable returns `False` for the current user, the item is hidden:

```python
def can_view_financials(request):
    return request.user.has_perm("myapp.view_financial_data")

# In UNFOLD settings
{
    "title": _("Financial Reports"),
    "link": reverse_lazy("admin:myapp_financialreport_changelist"),
    "permission": "myapp.admin_config.can_view_financials",
}
```

### Site Dropdown

The site dropdown appears when clicking the site header in the sidebar. It is useful for multi-site projects or for providing quick links to related tools:

```python
UNFOLD = {
    "SITE_DROPDOWN": [
        {
            "title": _("Main Site"),
            "link": "https://mysite.com",
        },
        {
            "title": _("Staging Admin"),
            "link": "https://staging.mysite.com/admin/",
        },
        {
            "title": _("Documentation"),
            "link": "https://docs.mysite.com",
        },
    ],
}
```

---

## 14. Theming and Colors

### Changing the Primary Color

The primary color drives buttons, links, active states, and highlighted elements. Define it using OKLCH color notation (the same format Tailwind CSS v4 uses):

```python
UNFOLD = {
    "COLORS": {
        "primary": {
            "50":  "oklch(97.7% .014 250)",    # Very light tint
            "100": "oklch(94.6% .033 250)",
            "200": "oklch(90.2% .063 250)",
            "300": "oklch(82.7% .119 250)",
            "400": "oklch(71.4% .203 250)",
            "500": "oklch(58.5% .275 250)",    # Main brand color
            "600": "oklch(52.3% .266 250)",
            "700": "oklch(44.4% .234 250)",
            "800": "oklch(38.8% .197 250)",
            "900": "oklch(33.5% .157 250)",
            "950": "oklch(27.1% .119 250)",    # Very dark shade
        },
    },
    "BORDER_RADIUS": "4px",    # Controls roundness globally. "0px" = sharp corners.
}
```

The OKLCH format is `oklch(lightness% chroma hue)`. To convert a hex color:
- Use the online tool at https://oklch.com/ to get the scale values for your brand color.
- Generate all 11 shades (50 through 950) following the lightness progression shown above, keeping chroma and hue the same.

### Custom Styles

For fine-grained style overrides, inject your own CSS file:

```python
UNFOLD = {
    "STYLES": [
        lambda request: static("css/admin-overrides.css"),
    ],
}
```

```css
/* static/css/admin-overrides.css */

/* Override the sidebar background */
#nav-sidebar {
    background-color: #1a1a2e;
}

/* Make the header logo larger */
.sidebar-header img {
    height: 40px;
}
```

---

## 15. Custom Pages

Beyond the dashboard, you can register entirely custom admin pages with their own URLs and templates:

```python
# myapp/admin_views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View

@method_decorator(staff_member_required, name="dispatch")
class RevenueReportView(View):
    def get(self, request):
        # Compute whatever you need
        from myapp.models import Order
        from django.db.models import Sum
        import json

        monthly_revenue = (
            Order.objects
            .values("created_at__year", "created_at__month")
            .annotate(total=Sum("total_amount"))
            .order_by("created_at__year", "created_at__month")
        )

        return render(request, "admin/revenue_report.html", {
            "monthly_revenue": monthly_revenue,
            # Pass admin site context for proper Unfold styling
            "title": "Revenue Report",
            "has_permission": True,
        })


# config/urls.py
from myapp.admin_views import RevenueReportView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin/reports/revenue/", RevenueReportView.as_view(), name="revenue-report"),
]
```

```html
<!-- templates/admin/revenue_report.html -->
{% extends "admin/base_site.html" %}
{% load i18n unfold %}

{% block content %}
{% component "unfold/components/card.html" %}
    {% component "unfold/components/title.html" %}
        Monthly Revenue
    {% endcomponent %}
    {# Your custom content here #}
    {% for row in monthly_revenue %}
        <p>{{ row.created_at__year }}/{{ row.created_at__month }}: ${{ row.total }}</p>
    {% endfor %}
{% endcomponent %}
{% endblock %}
```

Link to your custom page from the sidebar:

```python
UNFOLD = {
    "SIDEBAR": {
        "navigation": [
            {
                "title": _("Reports"),
                "items": [
                    {
                        "title": _("Revenue Report"),
                        "link": "/admin/reports/revenue/",
                    },
                ],
            },
        ],
    },
}
```

---

## 16. User & Group Admin Setup

The default Django User and Group admin pages need special handling in Unfold. If you simply inherit from Unfold's `ModelAdmin`, the password change forms and permission widgets will be unstyled.

The correct approach is to unregister the default User admin and re-register it with Unfold's provided base class:

```python
# myapp/admin.py (or wherever you register your admin)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

# Unregister the defaults
admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Use Unfold's form classes so password fields are styled correctly
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
```

If you use a custom User model (which you should — see the main best practices guide), the pattern is the same but you inherit from your model's admin instead:

```python
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from myapp.models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    
    # You can add all the normal ModelAdmin options on top
    list_display = ["email", "first_name", "last_name", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    compressed_fields = True
    warn_unsaved_form = True
```

---

## 17. Third-Party Integrations

Unfold provides styled integrations for several popular packages. Each requires its companion sub-app in `INSTALLED_APPS`.

### django-import-export

```python
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.import_export",  # <-- add this
    "import_export",
    "django.contrib.admin",
    ...
]

# admin.py
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin, ModelAdmin):
    # Import/Export buttons appear in the changelist, styled with Unfold
    pass
```

### django-simple-history

```python
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.simple_history",  # <-- add this
    "simple_history",
    ...
]

# admin.py
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin

@admin.register(Order)
class OrderAdmin(SimpleHistoryAdmin, ModelAdmin):
    # History view will be styled with Unfold
    pass
```

### django-guardian (Object-Level Permissions)

```python
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.guardian",  # <-- add this
    "guardian",
    ...
]
```

### django-celery-beat

The Celery Beat periodic task admin pages are automatically styled when `django-celery-beat` is installed alongside Unfold. No extra configuration is needed — the models just need to be registered via their standard admin classes, and Unfold styles them automatically.

---

## 18. Running the Default Admin Alongside Unfold

If you have a large existing project and want to migrate gradually, you can run the default Django admin at a separate URL while building out Unfold:

```python
# config/urls.py
from django.contrib import admin
from django.urls import path
from unfold.sites import UnfoldAdminSite

# Create a separate admin site running Unfold
unfold_site = UnfoldAdminSite()

urlpatterns = [
    path("admin/", admin.site.urls),          # Legacy default admin
    path("modern-admin/", unfold_site.urls),  # New Unfold admin
]
```

Then register models with `unfold_site` instead of `admin.site`:

```python
@admin.register(MyModel, site=unfold_site)
class MyModelAdmin(ModelAdmin):
    pass
```

This lets you build out the Unfold admin incrementally while keeping the existing admin running.

---

## 19. Common Pitfalls & Troubleshooting

**Problem: The admin page loads but has no styles — everything looks unstyled.**

Cause: `"unfold"` is not at the top of `INSTALLED_APPS`, or you have not run `collectstatic` in production.

Fix: Put `"unfold"` as the very first item in `INSTALLED_APPS`, before `"django.contrib.admin"`. Run `python manage.py collectstatic`.

---

**Problem: My model's change form fields are unstyled, but the rest of the admin looks correct.**

Cause: Your `ModelAdmin` class still inherits from `django.contrib.admin.ModelAdmin` instead of `unfold.admin.ModelAdmin`.

Fix: Change the import and base class:

```python
# Wrong
from django.contrib import admin
class MyAdmin(admin.ModelAdmin): ...

# Right
from unfold.admin import ModelAdmin
class MyAdmin(ModelAdmin): ...
```

---

**Problem: The User change form looks broken — password fields are missing or unstyled.**

Cause: Django's User admin uses special form classes for password handling. You must use Unfold's versions.

Fix: See Section 16 above. Use `UserChangeForm`, `UserCreationForm`, and `AdminPasswordChangeForm` from `unfold.forms`.

---

**Problem: Filters with number or date inputs do not work — there is no way to submit them.**

Cause: Filters with input fields require a submit button. Without it, the user has no way to apply the filter value.

Fix: Set `list_filter_submit = True` on any `ModelAdmin` that uses `RangeDateFilter`, `RangeNumericFilter`, or any other input-based filter.

---

**Problem: I added a custom Tailwind CSS file and now Unfold's styles are broken.**

Cause: Starting with Unfold 0.56.0, Unfold ships a precompiled Tailwind stylesheet. If you compile your own Tailwind and include it on the admin pages, the two stylesheets conflict.

Fix: Do not include your custom Tailwind stylesheet in admin pages. Use Unfold's `STYLES` setting to inject only additional custom CSS that does not conflict with Tailwind's base styles.

---

**Problem: My `actions_row` or `actions_detail` methods receive no arguments or the wrong arguments.**

Cause: Each action type has a different signature. Mismatching it causes errors.

Fix: Use the correct signature for each action type:

```python
# actions_list (global, above changelist table)
def my_action(self, request: HttpRequest): ...

# actions_row (per-row in the changelist)
def my_action(self, request: HttpRequest, object_id: int): ...

# actions_detail (at the top of the change form)
def my_action(self, request: HttpRequest, object_id: int): ...

# actions_submit_line (next to the save buttons)
def my_action(self, request: HttpRequest, obj: MyModel): ...

# Standard bulk actions (selected rows + action dropdown)
def my_action(self, request: HttpRequest, queryset: QuerySet): ...
```

---

**Problem: Sidebar items do not appear even though they are configured.**

Cause: The `"permission"` callback is returning `False`, or the URL in `"link"` is not a valid URL.

Fix: Test your permission callback in a Django shell. Ensure the `reverse_lazy()` calls in your navigation config point to URLs that actually exist.

---

## 20. Checklist

Use this every time you add or configure Unfold in a project.

### Initial Setup

- [ ] `"unfold"` is the very first item in `INSTALLED_APPS`, before `"django.contrib.admin"`
- [ ] Only the `unfold.contrib.*` sub-apps you actually use are included
- [ ] `python manage.py collectstatic` has been run (production)
- [ ] The `UNFOLD` settings dictionary is defined in `settings.py`
- [ ] `SITE_TITLE`, `SITE_HEADER` are set with the project name

### Model Admin

- [ ] Every `ModelAdmin` class inherits from `unfold.admin.ModelAdmin`, not Django's
- [ ] User admin is unregistered and re-registered with Unfold's form classes (`UserChangeForm`, `UserCreationForm`, `AdminPasswordChangeForm`)
- [ ] Group admin is also re-registered with `unfold.admin.ModelAdmin`
- [ ] `compressed_fields = True` is set on models with many fields
- [ ] `warn_unsaved_form = True` is set on models where accidental navigation is risky
- [ ] `list_filter_submit = True` is set whenever date/number input filters are used

### Actions

- [ ] Each action method has the correct signature for its placement type
- [ ] Action methods that navigate away return a redirect, not None
- [ ] Custom permissions are defined with a matching `has_<name>_permission` method

### Filters

- [ ] `"unfold.contrib.filters"` is in `INSTALLED_APPS` if using enhanced filters
- [ ] `list_filter_submit = True` is set whenever filters have input fields

### Display Decorator

- [ ] `@display` is imported from `unfold.decorators`, not `django.contrib.admin`
- [ ] Status fields use `label={value: color}` for colored badges
- [ ] Color values are one of: `"success"`, `"info"`, `"warning"`, `"danger"`

### Dashboard

- [ ] `DASHBOARD_CALLBACK` points to a real, importable function
- [ ] The callback returns the modified `context` dict
- [ ] `templates/admin/index.html` exists in a templates directory that Django searches
- [ ] The template extends `"admin/index.html"` and loads the `unfold` template tag library

### Sidebar

- [ ] All sidebar `"link"` values use `reverse_lazy()` (not hardcoded strings)
- [ ] Permission callbacks return a boolean
- [ ] Badge callbacks return an integer or `None`
- [ ] External links have a full URL with scheme (`https://...`)

### Environment Label

- [ ] `ENVIRONMENT` callback correctly identifies all environments
- [ ] Production is labeled "danger" so it is visually distinct

### Theming

- [ ] Primary colors are defined in OKLCH format
- [ ] All 11 shades (50 to 950) are provided for the primary color
- [ ] `BORDER_RADIUS` is set to match the project's design system

### Third-Party Integrations

- [ ] Each integration's `unfold.contrib.*` sub-app is in `INSTALLED_APPS` before `django.contrib.admin`
- [ ] Admin classes use the correct multiple-inheritance order (Unfold-specific class before `ModelAdmin`)

---

*Official documentation: https://unfoldadmin.com/docs/ — always check for the latest options as Unfold releases frequently.*
