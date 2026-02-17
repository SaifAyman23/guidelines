# Django ModelAdmin — Complete Guide

Using `TaskAdmin` as the running example throughout.

---

## Table of Contents

- [The baseline](#the-baseline)
- [list_display](#list_display)
- [list_filter](#list_filter)
- [search_fields](#search_fields)
- [fieldsets](#fieldsets)
- [Styling columns with format_html](#styling-columns-with-format_html)
- [readonly_fields](#readonly_fields)
- [ordering](#ordering)
- [list_per_page and pagination](#list_per_page-and-pagination)
- [list_select_related](#list_select_related)
- [date_hierarchy](#date_hierarchy)
- [list_editable](#list_editable)
- [list_display_links](#list_display_links)
- [prepopulated_fields](#prepopulated_fields)
- [autocomplete_fields](#autocomplete_fields)
- [raw_id_fields](#raw_id_fields)
- [save_model hook](#save_model-hook)
- [delete_model hook](#delete_model-hook)
- [get_queryset](#get_queryset)
- [Custom actions](#custom_actions)
- [Inlines](#inlines)
- [Permissions](#permissions)
- [Everything together](#everything-together)

---

## The baseline

This is the admin we're starting from. Everything below extends or improves it.

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "assignee",
        "project",
        "deadline",
        "status_colored",
    )
    list_filter = ("status", "project", "deadline")
    search_fields = (
        "name",
        "assignee__user__first_name",
        "assignee__user__last_name",
        "project__name",
        "description",
    )

    fieldsets = (
        ("Task Details", {
            "fields": (
                "name",
                "description",
                "assignee",
                "project",
            ),
        }),
        ("Timeline", {
            "fields": (
                "deadline",
                "status",
            ),
        }),
    )

    def status_colored(self, obj):
        color_map = {
            "new":         "#6B7280",
            "in_progress": "#2563EB",
            "done":        "#16A34A",
        }
        color = color_map.get(obj.status, "black")
        return format_html(
            '<strong style="color:{};">{}</strong>',
            color,
            obj.get_status_display()
        )

    status_colored.short_description = "Status"
```

---

## list_display

Controls which columns appear in the changelist (the list page).

Accepts field names, method names, or callables.

```python
list_display = (
    "id",
    "name",
    "assignee",   # FK — Django calls __str__ on the related object
    "project",
    "deadline",
    "status_colored",  # a method defined on the admin class
)
```

**Computed columns** — any method on the class works as a column:

```python
def days_until_deadline(self, obj):
    if not obj.deadline:
        return "—"
    delta = obj.deadline - date.today()
    if delta.days < 0:
        return format_html('<span style="color:#DC2626;">Overdue by {} days</span>', abs(delta.days))
    return f"{delta.days} days"

days_until_deadline.short_description = "Due In"
```

**Column from a related model** — use a method rather than a double-underscore path (double-underscore doesn't work in `list_display`):

```python
# ✗ This does NOT work in list_display:
list_display = ("assignee__user__email",)

# ✓ This does:
def assignee_email(self, obj):
    return obj.assignee.user.email

assignee_email.short_description = "Assignee Email"
```

**Making a column sortable** — by default computed columns are not sortable. Add `admin_order_field` to tell Django which DB field to sort by:

```python
def days_until_deadline(self, obj):
    ...

days_until_deadline.short_description = "Due In"
days_until_deadline.admin_order_field = "deadline"   # sorts by the actual deadline field
```

**Boolean columns** — return a Python bool and Django renders it as a green tick / red cross automatically:

```python
def is_overdue(self, obj):
    return obj.deadline is not None and obj.deadline < date.today()

is_overdue.short_description = "Overdue?"
is_overdue.boolean = True   # tells Django to render as icon, not True/False text
```

---

## list_filter

Adds a filter sidebar on the right side of the changelist.

```python
list_filter = ("status", "project", "deadline")
```

`"deadline"` on a `DateField` automatically gives you shortcuts: Today, Past 7 days, This month, This year.

**Custom filter** — filter by a computed condition, not just a raw field value:

```python
from django.contrib.admin import SimpleListFilter

class OverdueFilter(SimpleListFilter):
    title = "overdue"           # label shown in the sidebar
    parameter_name = "overdue"  # URL query param

    def lookups(self, request, model_admin):
        return (
            ("yes", "Overdue"),
            ("no",  "On track"),
        )

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == "yes":
            return queryset.filter(deadline__lt=today).exclude(status="done")
        if self.value() == "no":
            return queryset.filter(deadline__gte=today)
        return queryset

# Use it just like a field name:
list_filter = ("status", "project", OverdueFilter)
```

---

## search_fields

Powers the search box at the top of the changelist.

```python
search_fields = (
    "name",
    "assignee__user__first_name",
    "assignee__user__last_name",
    "project__name",
    "description",
)
```

The double-underscore traversal works here (unlike `list_display`). Django does a `ILIKE %term%` across all listed fields and ORs the results.

**Search prefixes** control the match type:

| Prefix | Behaviour | Example |
|---|---|---|
| *(none)* | `ILIKE %term%` — contains | `"name"` |
| `^` | `ILIKE term%` — starts with | `"^name"` |
| `=` | `= term` — exact match | `"=name"` |
| `@` | Full-text search (MySQL only) | `"@description"` |

```python
search_fields = (
    "^name",                         # name starts with the query
    "=assignee__user__email",        # exact email match
    "assignee__user__first_name",    # first name contains query
    "assignee__user__last_name",
    "project__name",
    "description",
)
```

---

## fieldsets

Controls the layout of the add/change form. Without `fieldsets`, Django just stacks all fields in definition order.

```python
fieldsets = (
    ("Task Details", {
        "fields": (
            "name",
            "description",
            "assignee",
            "project",
        ),
    }),
    ("Timeline", {
        "fields": (
            "deadline",
            "status",
        ),
    }),
)
```

**Collapsible sections** — add `"collapse"` to `classes`:

```python
("Advanced", {
    "fields": ("internal_notes", "external_id"),
    "classes": ("collapse",),   # collapsed by default, user can expand
}),
```

**Side-by-side fields** — put fields in a tuple inside the `fields` tuple:

```python
("Timeline", {
    "fields": (
        ("deadline", "status"),   # these two render on the same row
    ),
}),
```

**Section description** — add explanatory text under a section header:

```python
("Timeline", {
    "fields": ("deadline", "status"),
    "description": "Set the task deadline and current status.",
}),
```

---

## Styling columns with format_html

`format_html` is Django's safe way to return HTML from an admin method. Never use string concatenation or f-strings with user data — only `format_html` escapes values correctly.

**Your existing colored text:**

```python
def status_colored(self, obj):
    color_map = {
        "new":         "#6B7280",
        "in_progress": "#2563EB",
        "done":        "#16A34A",
    }
    color = color_map.get(obj.status, "black")
    return format_html(
        '<strong style="color:{};">{}</strong>',
        color,
        obj.get_status_display()
    )
```

**Pill / badge style:**

```python
def status_colored(self, obj):
    styles = {
        "new":         ("color:#6B7280;background:#F3F4F6;border:1px solid #D1D5DB;"),
        "in_progress": ("color:#1D4ED8;background:#EFF6FF;border:1px solid #BFDBFE;"),
        "done":        ("color:#15803D;background:#F0FDF4;border:1px solid #BBF7D0;"),
    }
    style = styles.get(obj.status, "color:black;")
    return format_html(
        '<span style="{}padding:2px 10px;border-radius:999px;'
        'font-size:0.78em;font-weight:600;">{}</span>',
        style,
        obj.get_status_display(),
    )
```

**Dot + text:**

```python
def status_colored(self, obj):
    colors = {
        "new":         "#6B7280",
        "in_progress": "#2563EB",
        "done":        "#16A34A",
    }
    color = colors.get(obj.status, "#000")
    return format_html(
        '<span style="display:inline-flex;align-items:center;gap:6px;">'
        '<span style="width:8px;height:8px;border-radius:50%;'
        'background:{};display:inline-block;"></span>{}</span>',
        color,
        obj.get_status_display(),
    )
```

**Boolean icon (custom, not Django's built-in):**

```python
def on_time_icon(self, obj):
    if obj.on_time is True:
        return format_html('<span style="color:#16A34A;font-size:1.1em;">✔</span>')
    if obj.on_time is False:
        return format_html('<span style="color:#DC2626;font-size:1.1em;">✘</span>')
    return format_html('<span style="color:#9CA3AF;">—</span>')

on_time_icon.short_description = "On Time"
```

**Truncated text with hover tooltip:**

```python
def short_description(self, obj):
    text = obj.description or ""
    if len(text) <= 80:
        return text
    return format_html(
        '<span title="{}">{}&hellip;</span>',
        text,
        text[:80],
    )

short_description.short_description = "Description"
```

**Clickable FK link to the related object's change page:**

```python
from django.urls import reverse
from django.utils.html import format_html

def project_link(self, obj):
    if not obj.project:
        return "—"
    url = reverse("admin:myapp_project_change", args=[obj.project.pk])
    return format_html('<a href="{}">{}</a>', url, obj.project.name)

project_link.short_description = "Project"
```

---

## readonly_fields

Fields that are shown on the form but cannot be edited.

```python
readonly_fields = ("created_at", "updated_at", "created_by")
```

You can also put computed methods in `readonly_fields` to display derived information on the form:

```python
readonly_fields = ("created_at", "updated_at", "task_summary")

def task_summary(self, obj):
    return format_html(
        "<strong>{}</strong> — assigned to {} — due {}",
        obj.name,
        obj.assignee,
        obj.deadline or "no deadline",
    )

task_summary.short_description = "Summary"
```

---

## ordering

Default sort order for the changelist. Prefix with `-` for descending.

```python
ordering = ("-deadline", "name")   # soonest deadline first, then alphabetically
```

---

## list_per_page and pagination

```python
list_per_page = 50          # rows per page (default: 100)
list_max_show_all = 500     # max rows shown when clicking "Show all"
show_full_result_count = False  # hides the total count for expensive queries
```

---

## list_select_related

Avoids N+1 queries when `list_display` includes FK fields.

```python
# Simple: follow all FK relationships
list_select_related = True

# Better: specify exactly which relations to follow
list_select_related = ("assignee", "project", "assignee__user")
```

Without this, displaying `assignee` and `project` for 100 tasks fires 201 queries. With it, it fires 1.

---

## date_hierarchy

Adds a drill-down date navigation bar above the list (Year → Month → Day).

```python
date_hierarchy = "deadline"
```

Only one field per admin, must be a `DateField` or `DateTimeField`.

---

## list_editable

Makes fields editable directly in the list view without opening the change form.

```python
list_display = ("id", "name", "status", "deadline")
list_editable = ("status", "deadline")
```

A field must be in `list_display` to be in `list_editable`, and the first column in `list_display` cannot be editable (it's the link). `list_display_links` controls which column is the link.

---

## list_display_links

Controls which column(s) link to the change form. By default it's the first column.

```python
# Make "name" the link instead of "id"
list_display = ("id", "name", "assignee", "status_colored")
list_display_links = ("name",)

# Make multiple columns link to the change form
list_display_links = ("id", "name")

# No link at all (useful when using list_editable)
list_display_links = None
```

---

## prepopulated_fields

Auto-fills a field (typically a `slug`) based on another field as the user types.

```python
prepopulated_fields = {"slug": ("name",)}
```

Uses JavaScript in the browser — works on the add/change form only, not in the list view.

---

## autocomplete_fields

Replaces the default `<select>` dropdown for FK / M2M fields with a searchable AJAX widget. Essential for models with large numbers of related objects.

```python
autocomplete_fields = ("assignee", "project")
```

**Requirement:** the related model's admin must define `search_fields`, otherwise Django raises an error:

```python
# ProjectAdmin must have search_fields for TaskAdmin.autocomplete_fields to work
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ("name",)
```

---

## raw_id_fields

Alternative to `autocomplete_fields` — shows a raw numeric ID input with a popup lookup. Useful for very large tables where you know the ID.

```python
raw_id_fields = ("assignee", "project")
```

---

## save_model hook

Called when the user saves the form. Use it to attach extra data or fire side effects.

```python
def save_model(self, request, obj, form, change):
    # change=False means this is a new object being created
    if not change:
        obj.created_by = request.user

    # Always call super() — this is what actually saves to the DB
    super().save_model(request, obj, form, change)

    # Side effects after save
    if obj.status == "done":
        # send_completion_notification.delay(obj.pk)
        pass
```

---

## delete_model hook

Called when the user deletes a single object from the change form.

```python
def delete_model(self, request, obj):
    if obj.status == "in_progress":
        # self.message_user won't stop the delete here — raise an exception instead
        raise PermissionError("Cannot delete an in-progress task.")

    super().delete_model(request, obj)
```

For bulk deletes from the list view, override `delete_queryset`:

```python
def delete_queryset(self, request, queryset):
    # Called when user selects rows and uses "Delete selected" action
    queryset = queryset.exclude(status="in_progress")
    super().delete_queryset(request, queryset)
```

---

## get_queryset

Override to limit which objects are visible in the admin — useful for multi-tenant apps or role-based visibility.

```python
def get_queryset(self, request):
    qs = super().get_queryset(request)

    # Superusers see everything
    if request.user.is_superuser:
        return qs

    # Regular staff only see tasks assigned to them
    return qs.filter(assignee__user=request.user)
```

Also use it to add annotations for use in computed columns:

```python
from django.db.models import Count

def get_queryset(self, request):
    return super().get_queryset(request).annotate(
        subtask_count=Count("subtasks")
    )

def subtask_count_col(self, obj):
    return obj.subtask_count

subtask_count_col.short_description = "Subtasks"
subtask_count_col.admin_order_field = "subtask_count"   # sortable
```

---

## Custom actions

Actions appear in the "Action" dropdown above the list and operate on selected rows.

```python
from django.contrib import messages

@admin.action(description="Mark selected tasks as done")
def mark_done(modeladmin, request, queryset):
    updated = queryset.update(status="done")
    modeladmin.message_user(
        request,
        f"{updated} task(s) marked as done.",
        messages.SUCCESS,
    )

@admin.action(description="Reassign selected tasks to me")
def claim_tasks(modeladmin, request, queryset):
    try:
        profile = request.user.profile
    except Exception:
        modeladmin.message_user(request, "You don't have a profile.", messages.ERROR)
        return
    queryset.update(assignee=profile)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    actions = [mark_done, claim_tasks]
    ...
```

Actions can also be methods on the admin class:

```python
class TaskAdmin(admin.ModelAdmin):
    actions = ["mark_done", "claim_tasks"]

    @admin.action(description="Mark selected tasks as done")
    def mark_done(self, request, queryset):
        updated = queryset.update(status="done")
        self.message_user(request, f"{updated} task(s) marked as done.")

    @admin.action(description="Reassign selected tasks to me")
    def claim_tasks(self, request, queryset):
        queryset.update(assignee=request.user.profile)
```

---

## Inlines

Display and edit related objects directly on the parent's change form.

```python
from django.contrib import admin

class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 1              # number of empty forms shown for adding new rows
    fields = ("name", "status", "deadline")
    readonly_fields = ("created_at",)
    show_change_link = True  # adds a link to the subtask's own change form

class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = [SubtaskInline, CommentInline]
    ...
```

`TabularInline` — compact, one row per related object.
`StackedInline` — expanded, full form per related object.

**Limit how many inline rows are shown:**

```python
class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0
    max_num = 10
    can_delete = True
```

---

## Permissions

Control which users can do what, at the model or object level.

**Model-level — disable specific operations entirely:**

```python
class TaskAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return True   # everyone with admin access can edit

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return True
```

**Object-level — decisions based on the specific instance:**

```python
def has_change_permission(self, request, obj=None):
    if obj is None:
        return True   # obj=None means "can you change any Task at all?"
    # Can only edit tasks assigned to you
    return obj.assignee.user == request.user or request.user.is_superuser

def has_delete_permission(self, request, obj=None):
    if obj is None:
        return True
    return obj.status != "in_progress"
```

---

## Everything together

The complete `TaskAdmin` with all of the above applied:

```python
from datetime import date

from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count

from .models import Task, Subtask


# ── Custom filter ────────────────────────────────────────────────────────────

class OverdueFilter(SimpleListFilter):
    title = "overdue"
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        return (("yes", "Overdue"), ("no", "On track"))

    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == "yes":
            return queryset.filter(deadline__lt=today).exclude(status="done")
        if self.value() == "no":
            return queryset.filter(deadline__gte=today)


# ── Inline ───────────────────────────────────────────────────────────────────

class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0
    fields = ("name", "status", "deadline")
    show_change_link = True


# ── Actions ───────────────────────────────────────────────────────────────────

@admin.action(description="Mark selected tasks as done")
def mark_done(modeladmin, request, queryset):
    updated = queryset.update(status="done")
    modeladmin.message_user(request, f"{updated} task(s) marked as done.", messages.SUCCESS)


# ── Admin ─────────────────────────────────────────────────────────────────────

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    # List view
    list_display = (
        "id",
        "name",
        "assignee_link",
        "project_link",
        "deadline",
        "status_colored",
        "is_overdue",
        "subtask_count_col",
    )
    list_display_links = ("id", "name")
    list_filter          = ("status", "project", OverdueFilter)
    search_fields        = (
        "^name",
        "assignee__user__first_name",
        "assignee__user__last_name",
        "=assignee__user__email",
        "project__name",
        "description",
    )
    ordering             = ("-deadline",)
    list_per_page        = 50
    list_select_related  = ("assignee", "project", "assignee__user")
    date_hierarchy       = "deadline"
    actions              = [mark_done]

    # Form
    fieldsets = (
        ("Task Details", {
            "fields": (
                "name",
                ("assignee", "project"),   # side by side
                "description",
            ),
        }),
        ("Timeline", {
            "fields": (
                ("deadline", "status"),    # side by side
            ),
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields     = ("created_at", "updated_at", "created_by")
    autocomplete_fields = ("assignee", "project")
    inlines             = [SubtaskInline]

    # ── Queryset ─────────────────────────────────────────────────────

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(subtask_count=Count("subtasks"))
        )

    # ── Columns ──────────────────────────────────────────────────────

    def status_colored(self, obj):
        styles = {
            "new":         "color:#6B7280;background:#F3F4F6;border:1px solid #D1D5DB;",
            "in_progress": "color:#1D4ED8;background:#EFF6FF;border:1px solid #BFDBFE;",
            "done":        "color:#15803D;background:#F0FDF4;border:1px solid #BBF7D0;",
        }
        style = styles.get(obj.status, "color:black;")
        return format_html(
            '<span style="{}padding:2px 10px;border-radius:999px;'
            'font-size:0.78em;font-weight:600;">{}</span>',
            style,
            obj.get_status_display(),
        )

    status_colored.short_description = "Status"
    status_colored.admin_order_field = "status"

    def assignee_link(self, obj):
        if not obj.assignee:
            return "—"
        url = reverse("admin:myapp_profile_change", args=[obj.assignee.pk])
        return format_html("<a href='{}'>{}</a>", url, obj.assignee)

    assignee_link.short_description = "Assignee"
    assignee_link.admin_order_field = "assignee"

    def project_link(self, obj):
        if not obj.project:
            return "—"
        url = reverse("admin:myapp_project_change", args=[obj.project.pk])
        return format_html("<a href='{}'>{}</a>", url, obj.project.name)

    project_link.short_description = "Project"
    project_link.admin_order_field = "project"

    def is_overdue(self, obj):
        if obj.status == "done" or not obj.deadline:
            return None
        return obj.deadline < date.today()

    is_overdue.short_description = "Overdue?"
    is_overdue.boolean = True

    def subtask_count_col(self, obj):
        return obj.subtask_count

    subtask_count_col.short_description = "Subtasks"
    subtask_count_col.admin_order_field = "subtask_count"

    # ── Hooks ─────────────────────────────────────────────────────────

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.status == "in_progress":
            return False
        return super().has_delete_permission(request, obj)
```
