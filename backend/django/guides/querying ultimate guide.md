# The Ultimate Django Querying Guide
### From Beginner to Legend — Dense, Comprehensive, Production-Grade

---

## The Data Model We'll Use Throughout This Guide

Everything in this guide is grounded in a realistic accounting system. Understanding the schema first makes every example below immediately applicable to real work.

```python
# models.py — the full schema used throughout this guide

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimestampedModel(models.Model):
    """Abstract base — every model gets created_at / updated_at automatically."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimestampedModel):
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50, unique=True)
    fiscal_year_start = models.IntegerField(default=1)  # month number
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "companies"


class CostCenter(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cost_centers")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )

    class Meta:
        unique_together = [("company", "code")]


class ChartOfAccount(TimestampedModel):
    ACCOUNT_TYPES = [
        ("asset", "Asset"),
        ("liability", "Liability"),
        ("equity", "Equity"),
        ("revenue", "Revenue"),
        ("expense", "Expense"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="accounts")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("company", "code")]
        indexes = [
            models.Index(fields=["company", "account_type"], name="coa_company_type_idx"),
        ]


class JournalEntry(TimestampedModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("voided", "Voided"),
    ]
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="journal_entries")
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="created_entries"
    )
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_entries"
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "date"], name="je_company_date_idx"),
            models.Index(
                fields=["company", "date"],
                condition=models.Q(status="posted"),
                name="je_company_date_posted_idx",
            ),
            models.Index(fields=["company", "status"], name="je_company_status_idx"),
        ]


class JournalEntryLine(TimestampedModel):
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name="lines"
    )
    coa_account = models.ForeignKey(
        ChartOfAccount, on_delete=models.PROTECT, related_name="entry_lines"
    )
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    cost_center = models.ForeignKey(
        CostCenter, on_delete=models.PROTECT, null=True, blank=True, related_name="lines"
    )
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~(models.Q(debit__gt=0) & models.Q(credit__gt=0)),
                name="no_simultaneous_debit_and_credit",
            ),
            models.CheckConstraint(
                check=models.Q(debit__gte=0) & models.Q(credit__gte=0),
                name="non_negative_amounts",
            ),
        ]
        indexes = [
            models.Index(fields=["coa_account", "journal_entry"], name="jel_account_entry_idx"),
        ]


class Budget(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="budgets")
    coa_account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT)
    cost_center = models.ForeignKey(CostCenter, null=True, blank=True, on_delete=models.SET_NULL)
    year = models.IntegerField()
    month = models.IntegerField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        unique_together = [("company", "coa_account", "cost_center", "year", "month")]
```

---

## Table of Contents

1. [Level 1 — Beginner: The Basics](#level-1--beginner-the-basics)
2. [Level 2 — Intermediate: Relationships, Q Objects & Managers](#level-2--intermediate-relationships-q-objects--managers)
3. [Level 3 — Advanced: Annotations, Aggregations & Subqueries](#level-3--advanced-annotations-aggregations--subqueries)
4. [Level 4 — Expert: Window Functions, Custom Expressions & Raw SQL](#level-4--expert-window-functions-custom-expressions--raw-sql)
5. [Level 5 — Legend: Optimization, Locking & The Heavily Nested Example](#level-5--legend-optimization-locking--the-heavily-nested-example)
6. [Quick Reference Cheat Sheet](#quick-reference--the-legend-cheat-sheet)

---

## Level 1 — Beginner: The Basics

### How Django QuerySets Actually Work

A QuerySet is **lazy** — it does not hit the database until you force evaluation. Django builds up a SQL query in Python and only executes it when you iterate, slice, call `list()`, `bool()`, `len()`, or `repr()` on it. This lets you chain filters, annotations, and ordering without paying any DB cost until the last moment.

```python
# This does NOT hit the database — just builds a query object
qs = JournalEntry.objects.filter(status="posted")

# Still no DB hit — another filter is appended to the SQL
qs = qs.filter(company=company)

# THIS hits the database — evaluation is forced
entries = list(qs)

# This also forces evaluation
for entry in qs:
    print(entry.description)

# So does this
if qs.exists():
    pass

# And this
count = qs.count()
```

### Basic CRUD

```python
# CREATE — one INSERT
entry = JournalEntry.objects.create(
    company=company,
    date="2024-01-15",
    description="Opening balance",
    status="draft",
    created_by=request.user,
)

# Alternative: instantiate then save (useful when you want to do logic before saving)
entry = JournalEntry(company=company, date="2024-01-15", created_by=request.user)
entry.full_clean()  # run model validation before saving
entry.save()

# READ ALL — lazy
JournalEntry.objects.all()

# READ ONE — raises JournalEntry.DoesNotExist if not found, raises MultipleObjectsReturned if >1
JournalEntry.objects.get(id=1)

# READ ONE SAFELY — returns None instead of raising
JournalEntry.objects.filter(id=1).first()
JournalEntry.objects.filter(id=1).last()

# get_or_create — returns (instance, created_bool)
entry, created = JournalEntry.objects.get_or_create(
    company=company,
    reference="INV-2024-001",
    defaults={"date": "2024-01-15", "created_by": request.user},
)

# update_or_create — returns (instance, created_bool)
entry, created = JournalEntry.objects.update_or_create(
    company=company,
    reference="INV-2024-001",
    defaults={"date": "2024-01-15", "description": "Updated description"},
)

# UPDATE — one UPDATE statement, does NOT call .save() or trigger signals
JournalEntry.objects.filter(id=1).update(description="Updated", status="posted")

# DELETE — one DELETE statement, triggers on_delete cascade at DB level
JournalEntry.objects.filter(status="voided").delete()
```

### Filtering — Every Lookup Type You'll Actually Use

Django lookup types are appended to field names with double underscores. They translate directly to SQL operators.

```python
# Exact (default — __exact is implicit)
JournalEntry.objects.filter(status="posted")
JournalEntry.objects.filter(status__exact="posted")   # same thing

# String lookups
JournalEntry.objects.filter(description__contains="rent")       # LIKE '%rent%'
JournalEntry.objects.filter(description__icontains="rent")      # ILIKE '%rent%' (case-insensitive)
JournalEntry.objects.filter(reference__startswith="INV")        # LIKE 'INV%'
JournalEntry.objects.filter(reference__istartswith="inv")       # case-insensitive
JournalEntry.objects.filter(reference__endswith="2024")         # LIKE '%2024'
JournalEntry.objects.filter(description__regex=r"^[A-Z]{3}")   # regex
JournalEntry.objects.filter(description__iregex=r"^[a-z]{3}")  # case-insensitive regex

# Numeric comparisons
JournalEntryLine.objects.filter(debit__gt=0)         # >
JournalEntryLine.objects.filter(debit__gte=1000)     # >=
JournalEntryLine.objects.filter(credit__lt=5000)     # <
JournalEntryLine.objects.filter(credit__lte=4999.99) # <=

# Range (inclusive on both ends → BETWEEN)
JournalEntry.objects.filter(date__range=("2024-01-01", "2024-12-31"))
JournalEntryLine.objects.filter(debit__range=(1000, 5000))

# In a list
JournalEntry.objects.filter(status__in=["posted", "draft"])

# Null checks
JournalEntry.objects.filter(approved_by__isnull=True)
JournalEntry.objects.filter(approved_by__isnull=False)

# Date/time component extraction
JournalEntry.objects.filter(date__year=2024)
JournalEntry.objects.filter(date__month=3)
JournalEntry.objects.filter(date__day=15)
JournalEntry.objects.filter(date__quarter=1)              # Q1
JournalEntry.objects.filter(date__week=12)                # ISO week number
JournalEntry.objects.filter(date__week_day=2)             # 1=Sunday, 2=Monday, etc.
JournalEntry.objects.filter(created_at__hour=9)           # hour of day
JournalEntry.objects.filter(created_at__date="2024-01-15") # extract date from datetime

# Exclude — NOT (inverts the filter)
JournalEntry.objects.exclude(status="voided")
JournalEntry.objects.exclude(approved_by__isnull=True)

# Chaining (each .filter() is an AND)
JournalEntry.objects.filter(status="posted").filter(company=company).filter(date__year=2024)
# Equivalent to:
JournalEntry.objects.filter(status="posted", company=company, date__year=2024)
```

### Ordering & Slicing

```python
# Ascending (default)
JournalEntry.objects.order_by("date")

# Descending — prefix with -
JournalEntry.objects.order_by("-date")

# Multiple fields — secondary sort when primary has ties
JournalEntry.objects.order_by("-date", "reference")

# Order by related field
JournalEntry.objects.order_by("company__name", "-date")

# Random order (useful for sampling — expensive on large tables)
JournalEntry.objects.order_by("?")

# Clear any inherited ordering (e.g. from Meta.ordering)
JournalEntry.objects.all().order_by()

# Slicing — translates to LIMIT/OFFSET. Note: negative indexing NOT supported
JournalEntry.objects.all()[:10]        # LIMIT 10
JournalEntry.objects.all()[10:20]      # LIMIT 10 OFFSET 10
JournalEntry.objects.all()[0]          # same as .first() but raises IndexError if empty

# You cannot filter after slicing — it raises TypeError
# This is wrong:
# JournalEntry.objects.all()[:10].filter(status="posted")  # TypeError!
```

### Existence & Counting

```python
# exists() — translates to SELECT 1 FROM ... LIMIT 1, very efficient
JournalEntry.objects.filter(status="posted").exists()   # → True/False

# count() — translates to SELECT COUNT(*) FROM ...
JournalEntry.objects.filter(status="posted").count()    # → int

# Never do this:
# len(JournalEntry.objects.filter(status="posted"))  # loads ALL records into memory first!
# Use .count() instead when you just need a number.
```

---

## Level 2 — Intermediate: Relationships, Q Objects & Managers

### select_related — Eliminating N+1 on Forward Relations

`select_related` works by performing a SQL JOIN and selecting the related object's columns in the same query. Use it for `ForeignKey` and `OneToOneField`. Without it, accessing `entry.company` or `entry.created_by` on each object in a loop causes one extra query per row — the N+1 problem.

```python
# BAD — 1 query to get entries, then 1 per entry to get company = N+1
entries = JournalEntry.objects.filter(status="posted")
for entry in entries:
    print(entry.company.name)   # hits DB every iteration

# GOOD — 1 query with JOIN, company data comes along for free
entries = JournalEntry.objects.select_related("company").filter(status="posted")
for entry in entries:
    print(entry.company.name)   # no extra query

# Multiple FK relationships — chain them or pass multiple args
JournalEntry.objects.select_related("company", "created_by", "approved_by")

# Traverse deeper — follow FKs on FKs
JournalEntry.objects.select_related("company", "created_by__profile")

# Select ALL FK relations (use carefully — can JOIN too many tables)
JournalEntry.objects.select_related()

# select_related on lines (JournalEntryLine has FKs to coa_account and cost_center)
JournalEntryLine.objects.select_related("journal_entry", "coa_account", "cost_center")

# Going even deeper — follow journal_entry's company FK in the same JOIN chain
JournalEntryLine.objects.select_related(
    "journal_entry__company",
    "coa_account",
    "cost_center__parent",   # CostCenter has a self-referential parent FK
)
```

### prefetch_related — Eliminating N+1 on Reverse Relations

`prefetch_related` executes a **separate** query for the related objects and stitches the results together in Python. Use it for reverse FK (one-to-many), M2M, and GenericRelatedObjectManager. It avoids the N+1 but does so with 2 queries total instead of a JOIN — better for large result sets where a JOIN would create cartesian multiplication.

```python
from django.db.models import Prefetch

# Basic — fetches all lines in a single separate query
JournalEntry.objects.prefetch_related("lines")

# With Prefetch() — customize the queryset that fetches the related objects
JournalEntry.objects.prefetch_related(
    Prefetch(
        "lines",
        queryset=JournalEntryLine.objects.select_related("coa_account", "cost_center")
    )
)
# This results in exactly 2 DB queries regardless of how many JournalEntries are returned:
# Query 1: SELECT * FROM journal_entry WHERE ...
# Query 2: SELECT jel.*, coa.*, cc.* FROM journal_entry_line jel
#           JOIN chart_of_account coa ON ...
#           JOIN cost_center cc ON ...
#           WHERE jel.journal_entry_id IN (1, 2, 3, ...)

# Prefetch with filtering — only prefetch lines that have debit > 0
JournalEntry.objects.prefetch_related(
    Prefetch(
        "lines",
        queryset=JournalEntryLine.objects.filter(debit__gt=0).select_related("coa_account"),
        to_attr="debit_lines",  # stores result as entry.debit_lines (a list, not a queryset)
    )
)
# Access: entry.debit_lines — this is a plain Python list
# Without to_attr: entry.lines.all() — this is a queryset (already cached)

# Multiple prefetches at once
JournalEntry.objects.prefetch_related(
    Prefetch("lines", queryset=JournalEntryLine.objects.select_related("coa_account")),
    "lines__cost_center",  # prefetch cost_center for each line (alternative style)
)

# Prefetch on a prefetch — ChartOfAccount has children (self-referential FK)
ChartOfAccount.objects.prefetch_related(
    Prefetch("children", queryset=ChartOfAccount.objects.filter(is_active=True))
)
```

### Filtering Across Relationships

When you filter across a JOIN, Django creates an implicit JOIN. With reverse FK filters, this can cause **duplicate rows** if multiple related objects match — use `.distinct()` to deduplicate.

```python
# Forward FK — filter JournalEntries by company name (implicit JOIN on company)
JournalEntry.objects.filter(company__name__icontains="Acme")

# Multi-level traversal
JournalEntry.objects.filter(lines__coa_account__account_type="expense")

# Filter entries that HAVE at least one line with debit > 0
# Without distinct(), an entry with 3 qualifying lines appears 3 times
JournalEntry.objects.filter(lines__debit__gt=0).distinct()

# Subtle distinction: chaining .filter() calls vs passing both to same .filter()
# For multi-valued relations (reverse FK, M2M), these produce DIFFERENT SQL:

# Version A: finds entries where a SINGLE line has debit > 0 AND credit == 0
JournalEntry.objects.filter(lines__debit__gt=0, lines__credit=0)

# Version B: finds entries where (some line has debit > 0) AND (some line has credit == 0)
# — those two conditions can be on DIFFERENT lines!
JournalEntry.objects.filter(lines__debit__gt=0).filter(lines__credit=0)

# This distinction is one of the most common sources of subtle query bugs in Django.
```

### Q Objects — Arbitrary Boolean Logic

`Q` objects wrap filter conditions and can be composed with `|` (OR), `&` (AND), and `~` (NOT). Without Q objects you're limited to AND-only filters.

```python
from django.db.models import Q

# OR — entries that are posted OR have a reference starting with INV
JournalEntry.objects.filter(Q(status="posted") | Q(reference__startswith="INV"))

# AND (explicit — same as passing kwargs but useful when mixing with OR)
JournalEntry.objects.filter(Q(status="posted") & Q(company=company))

# NOT
JournalEntry.objects.filter(~Q(status="voided"))

# Combine NOT with OR
JournalEntry.objects.filter(~Q(status="voided") & (Q(company=company) | Q(reference__startswith="INV")))

# Dynamic filter construction — build up Q objects programmatically
def search_entries(company, status=None, date_from=None, date_to=None, search_term=None):
    filters = Q(company=company)  # start with base filter

    if status:
        filters &= Q(status=status)
    if date_from:
        filters &= Q(date__gte=date_from)
    if date_to:
        filters &= Q(date__lte=date_to)
    if search_term:
        # Search across multiple fields with OR
        filters &= (
            Q(description__icontains=search_term) |
            Q(reference__icontains=search_term) |
            Q(lines__description__icontains=search_term)
        )

    return JournalEntry.objects.filter(filters).distinct()

# Q with related field traversal
JournalEntry.objects.filter(
    Q(lines__coa_account__account_type="expense") |
    Q(lines__coa_account__account_type="revenue")
).distinct()
```

### Custom QuerySets and Managers — The Right Way to Encapsulate Logic

Scattering `.filter(status="posted")` across 20 views is a maintenance nightmare. Custom QuerySets centralize this logic, make it reusable, and make your code read like English.

```python
from django.db.models import Prefetch, Sum, Count, Q


class JournalEntryQuerySet(models.QuerySet):
    """All query logic for JournalEntry lives here — one place to maintain."""

    def posted(self):
        return self.filter(status="posted")

    def draft(self):
        return self.filter(status="draft")

    def voided(self):
        return self.filter(status="voided")

    def for_company(self, company):
        return self.filter(company=company)

    def in_period(self, date_from, date_to):
        return self.filter(date__range=(date_from, date_to))

    def in_year(self, year):
        return self.filter(date__year=year)

    def unbalanced(self):
        """Entries where total debits != total credits — data integrity check."""
        return self.annotate(
            total_debit=Sum("lines__debit"),
            total_credit=Sum("lines__credit"),
        ).exclude(total_debit=models.F("total_credit"))

    def unapproved(self):
        return self.filter(status="posted", approved_by__isnull=True)

    def with_lines(self):
        """Eagerly load lines and their FKs — use this whenever serializing."""
        return self.prefetch_related(
            Prefetch(
                "lines",
                queryset=JournalEntryLine.objects.select_related(
                    "coa_account", "cost_center"
                ).order_by("id")
            )
        )

    def with_totals(self):
        """Annotate each entry with its debit/credit totals and line count."""
        return self.annotate(
            total_debit=Sum("lines__debit"),
            total_credit=Sum("lines__credit"),
            line_count=Count("lines"),
        )

    def search(self, term):
        return self.filter(
            Q(description__icontains=term) |
            Q(reference__icontains=term)
        )


class JournalEntryManager(models.Manager):
    def get_queryset(self):
        return JournalEntryQuerySet(self.model, using=self._db)

    # Proxy the most commonly used methods so you can call Manager.posted() directly
    def posted(self):
        return self.get_queryset().posted()

    def for_company(self, company):
        return self.get_queryset().for_company(company)


class JournalEntry(TimestampedModel):
    objects = JournalEntryManager()
    # ...


# The payoff — reads like English, no raw filter args scattered everywhere:
entries = (
    JournalEntry.objects
    .for_company(company)
    .posted()
    .in_year(2024)
    .with_lines()
    .with_totals()
    .search("payroll")
    .order_by("-date")
)

# Each method returns a queryset, so they're all lazy and chainable.
# The final SQL is built from all the chained calls and sent in ONE query.
```

---

## Level 3 — Advanced: Annotations, Aggregations & Subqueries

### aggregate() — Collapse the Entire QuerySet to a Single Dict

`aggregate()` terminates the queryset and returns a Python dict. It maps to `SELECT SUM(...), COUNT(...) FROM ...` — one row returned, no GROUP BY.

```python
from django.db.models import Sum, Avg, Max, Min, Count, StdDev, Variance

result = JournalEntryLine.objects.filter(
    journal_entry__company=company,
    journal_entry__status="posted",
    journal_entry__date__year=2024,
).aggregate(
    total_debit=Sum("debit"),
    total_credit=Sum("credit"),
    avg_debit=Avg("debit"),
    max_debit=Max("debit"),
    min_debit=Min("debit"),
    line_count=Count("id"),
    distinct_accounts=Count("coa_account", distinct=True),
    debit_stddev=StdDev("debit"),
)
# → {
#     "total_debit": Decimal("1500000.00"),
#     "total_credit": Decimal("1500000.00"),
#     "avg_debit": Decimal("2543.21"),
#     "max_debit": Decimal("250000.00"),
#     "min_debit": Decimal("0.01"),
#     "line_count": 590,
#     "distinct_accounts": 42,
#     "debit_stddev": Decimal("18432.11"),
# }

# Aggregate with null handling — Sum returns None if no rows, coalesce with 0
from django.db.models.functions import Coalesce
from django.db.models import DecimalField, Value

result = JournalEntryLine.objects.filter(...).aggregate(
    total=Coalesce(Sum("debit"), Value(0), output_field=DecimalField())
)
```

### annotate() — Add Computed Columns Per Row

`annotate()` is `aggregate()` applied per row. It maps to `SELECT ..., SUM(...) FROM ... GROUP BY (primary key)`. Each object in the resulting queryset gets the computed attribute attached.

```python
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField, Q

# Basic annotation — each JournalEntry gets total_debit, total_credit, line_count
entries = JournalEntry.objects.annotate(
    total_debit=Sum("lines__debit"),
    total_credit=Sum("lines__credit"),
    line_count=Count("lines"),
)
entry = entries.first()
print(entry.total_debit)   # Decimal("5000.00") — no extra query
print(entry.line_count)    # 4

# Filter on annotations — uses HAVING under the hood
large_entries = JournalEntry.objects.annotate(
    total_debit=Sum("lines__debit")
).filter(total_debit__gte=100000)

# Order by annotation
JournalEntry.objects.annotate(
    line_count=Count("lines")
).order_by("-line_count")

# F() expressions — reference field values without Python roundtripping
# This computes the difference at the DB level, no Python involved
JournalEntryLine.objects.annotate(
    net=ExpressionWrapper(
        F("debit") - F("credit"),
        output_field=DecimalField(max_digits=18, decimal_places=2)
    )
)

# F() for field-to-field comparisons
# Find lines where debit equals credit (unusual but possible)
JournalEntryLine.objects.filter(debit=F("credit"))

# Conditional aggregation — count only lines that meet a condition
# This is incredibly powerful: one query gives you multiple conditional counts
JournalEntry.objects.annotate(
    debit_line_count=Count("lines", filter=Q(lines__debit__gt=0)),
    credit_line_count=Count("lines", filter=Q(lines__credit__gt=0)),
    expense_line_total=Sum("lines__debit", filter=Q(lines__coa_account__account_type="expense")),
    revenue_line_total=Sum("lines__credit", filter=Q(lines__coa_account__account_type="revenue")),
)
```

### values() + annotate() — GROUP BY

When you put `values()` BEFORE `annotate()`, Django generates a `GROUP BY` on the values fields. This is your SQL `GROUP BY` equivalent.

```python
# Total debit and credit per account type
ChartOfAccount.objects.values("account_type").annotate(
    total_debit=Sum("entry_lines__debit"),
    total_credit=Sum("entry_lines__credit"),
    account_count=Count("id"),
).order_by("account_type")
# → [
#     {"account_type": "asset", "total_debit": ..., "total_credit": ..., "account_count": 12},
#     {"account_type": "expense", ...},
#     ...
# ]

# GROUP BY multiple fields — monthly totals per cost center
JournalEntryLine.objects.filter(
    journal_entry__status="posted",
    journal_entry__company=company,
).values(
    "journal_entry__date__year",
    "journal_entry__date__month",
    "cost_center__name",
).annotate(
    total_debit=Sum("debit"),
    total_credit=Sum("credit"),
).order_by(
    "journal_entry__date__year",
    "journal_entry__date__month",
    "cost_center__name",
)

# values_list — returns tuples instead of dicts
JournalEntryLine.objects.values_list("coa_account__name", "debit").filter(debit__gt=0)

# values_list with flat=True — returns a flat list of a single field (great for .filter(id__in=...))
posted_ids = JournalEntry.objects.filter(status="posted").values_list("id", flat=True)
JournalEntryLine.objects.filter(journal_entry_id__in=posted_ids)
```

### Conditional Expressions — Case/When

`Case/When` is a SQL `CASE WHEN ... THEN ... END` — lets you branch logic inside the DB, producing a different output per row based on conditions.

```python
from django.db.models import Case, When, Value, IntegerField, CharField, DecimalField

# Annotate each entry with a numeric sort priority
JournalEntry.objects.annotate(
    priority=Case(
        When(status="posted", then=Value(3)),
        When(status="draft", then=Value(2)),
        When(status="voided", then=Value(1)),
        default=Value(0),
        output_field=IntegerField(),
    )
).order_by("-priority", "-date")

# Conditional bucketing — classify entries by total size
JournalEntry.objects.annotate(
    total_debit=Sum("lines__debit")
).annotate(
    size_bucket=Case(
        When(total_debit__gte=100000, then=Value("large")),
        When(total_debit__gte=10000, then=Value("medium")),
        When(total_debit__gte=1000, then=Value("small")),
        default=Value("micro"),
        output_field=CharField(),
    )
)

# Conditional Sum — pivot data into columns (no GROUP BY needed for simple pivots)
# This computes expense vs revenue totals in ONE query instead of two
JournalEntryLine.objects.filter(
    journal_entry__company=company,
    journal_entry__status="posted",
).aggregate(
    expense_total=Sum(
        Case(
            When(coa_account__account_type="expense", then=F("debit")),
            default=Value(0),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
    ),
    revenue_total=Sum(
        Case(
            When(coa_account__account_type="revenue", then=F("credit")),
            default=Value(0),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
    ),
)
```

### Subqueries and OuterRef

`Subquery` embeds a queryset as a SQL subquery inside another query. `OuterRef` references a field from the outer query — it's the Django equivalent of a correlated subquery. This is powerful because it lets you attach per-row computations from related tables without a JOIN (which avoids row multiplication).

```python
from django.db.models import OuterRef, Subquery, Exists

# Annotate each JournalEntry with its most recently posted line's description
latest_line = JournalEntryLine.objects.filter(
    journal_entry=OuterRef("pk")          # correlate to the outer JournalEntry
).order_by("-id").values("description")[:1]  # take one value (must be a single column)

JournalEntry.objects.annotate(
    latest_line_desc=Subquery(latest_line, output_field=models.TextField())
)

# Annotate each ChartOfAccount with its most recent debit amount
last_debit = JournalEntryLine.objects.filter(
    coa_account=OuterRef("pk"),
    journal_entry__status="posted",
).order_by("-journal_entry__date", "-id").values("debit")[:1]

ChartOfAccount.objects.annotate(
    last_debit_amount=Subquery(last_debit, output_field=models.DecimalField())
)

# Exists subquery — very efficient "does a related row exist?" check
# Translates to SELECT 1 WHERE EXISTS (SELECT 1 FROM ...)
has_expense_lines = JournalEntryLine.objects.filter(
    journal_entry=OuterRef("pk"),
    coa_account__account_type="expense",
)
JournalEntry.objects.annotate(
    has_expenses=Exists(has_expense_lines)
).filter(has_expenses=True)

# Multi-level OuterRef — reference the outer outer query
# Example: for each company, for each account, get the latest entry date
latest_entry_for_account = JournalEntry.objects.filter(
    company=OuterRef(OuterRef("company")),      # go two levels up
    lines__coa_account=OuterRef("pk"),
    status="posted",
).order_by("-date").values("date")[:1]

ChartOfAccount.objects.annotate(
    last_used=Subquery(latest_entry_for_account, output_field=models.DateField())
)
```

### Bulk Operations — Replacing Python Loops with Single SQL Statements

```python
# BULK CREATE — inserts all rows in a single INSERT statement (or batched)
lines = [
    JournalEntryLine(
        journal_entry=entry,
        coa_account=acc,
        debit=amount,
        description=desc,
    )
    for acc, amount, desc in line_data
]
created = JournalEntryLine.objects.bulk_create(lines, batch_size=500)
# Returns the created instances. On PostgreSQL, IDs are populated.
# bulk_create does NOT call .save() and does NOT trigger signals.

# ignore_conflicts — skip rows that would violate unique constraints
JournalEntryLine.objects.bulk_create(lines, ignore_conflicts=True)

# update_conflicts — upsert on PostgreSQL (Django 4.2+)
JournalEntryLine.objects.bulk_create(
    lines,
    update_conflicts=True,
    unique_fields=["journal_entry", "coa_account"],
    update_fields=["debit", "credit", "description"],
)

# BULK UPDATE — updates all rows in a single UPDATE statement (or batched)
for line in lines:
    line.debit = line.debit * Decimal("1.1")  # 10% increase

JournalEntryLine.objects.bulk_update(lines, fields=["debit"], batch_size=500)
# Only updates the listed fields. Does NOT call .save() and does NOT trigger signals.

# UPDATE with F() expressions — the most efficient update, no Python loop at all
# This sends a single UPDATE ... SET debit = debit * 1.1 WHERE ...
from django.db.models import F
JournalEntryLine.objects.filter(
    journal_entry__company=company,
    journal_entry__status="draft",
).update(debit=F("debit") * Decimal("1.1"))

# UPDATE with Case/When — conditional update per row in one statement
from django.db.models import Case, When, Value
JournalEntry.objects.filter(company=company).update(
    status=Case(
        When(approved_by__isnull=False, then=Value("posted")),
        default=F("status"),  # keep existing status if not approved
        output_field=models.CharField(),
    )
)
```

---

## Level 4 — Expert: Window Functions, Custom Expressions & Raw SQL

### Window Functions — Analytics Without Losing Row Granularity

Window functions compute a value "over a window" of related rows without collapsing them the way `GROUP BY` does. They're invaluable for rankings, running totals, moving averages, and lead/lag comparisons. Django has supported them since version 2.0.

```python
from django.db.models import Window, Sum, Avg, Count, Rank, DenseRank, RowNumber, F
from django.db.models.functions import Lag, Lead, FirstValue, LastValue, NthValue, CumeDist, PercentRank

# RUNNING TOTAL — cumulative debit per account, ordered by entry date
# PARTITION BY coa_account means the running total resets for each account
JournalEntryLine.objects.annotate(
    running_debit=Window(
        expression=Sum("debit"),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
    )
)

# RANK — rank lines by debit amount within each account
# Rank skips numbers on ties (1, 2, 2, 4); DenseRank doesn't (1, 2, 2, 3)
JournalEntryLine.objects.annotate(
    rank_by_debit=Window(
        expression=Rank(),
        partition_by=[F("coa_account")],
        order_by=F("debit").desc(),
    ),
    dense_rank_by_debit=Window(
        expression=DenseRank(),
        partition_by=[F("coa_account")],
        order_by=F("debit").desc(),
    ),
    row_number=Window(
        expression=RowNumber(),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
    ),
)

# LAG / LEAD — access the previous or next row's value within the partition
JournalEntryLine.objects.annotate(
    prev_debit=Window(
        expression=Lag("debit", offset=1, default=0),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
    ),
    next_debit=Window(
        expression=Lead("debit", offset=1, default=0),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
    ),
    # Change from previous period
    debit_change=Window(
        expression=F("debit") - Lag("debit", offset=1, default=F("debit")),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
    ),
)

# FIRST/LAST VALUE — anchor to the first or last value in the window
JournalEntryLine.objects.annotate(
    first_debit_for_account=Window(
        expression=FirstValue("debit"),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
    ),
    last_debit_for_account=Window(
        expression=LastValue("debit"),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
        # For LastValue, use ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        # otherwise it only looks at rows up to the current one
        frame=models.expressions.WindowFrame(start=None, end=None),
    ),
)

# PERCENTILE (PostgreSQL) — ordered-set aggregate, requires custom Func
from django.db.models import Func, FloatField

class PercentileCont(Func):
    """PostgreSQL PERCENTILE_CONT ordered-set aggregate."""
    function = "PERCENTILE_CONT"
    template = "%(function)s(%(percentile)s) WITHIN GROUP (ORDER BY %(expressions)s)"

    def __init__(self, expression, percentile=0.5, **extra):
        super().__init__(expression, percentile=percentile, **extra)

# Usage: median debit per account type
ChartOfAccount.objects.values("account_type").annotate(
    median_debit=PercentileCont("entry_lines__debit", percentile=0.5, output_field=FloatField())
)

# MOVING AVERAGE — average over a sliding window of rows
# Uses frame specification: 6 preceding rows + current row = 7-row moving average
from django.db.models.expressions import RowRange
JournalEntryLine.objects.annotate(
    moving_avg_debit=Window(
        expression=Avg("debit"),
        partition_by=[F("coa_account")],
        order_by=F("journal_entry__date").asc(),
        frame=RowRange(start=-6, end=0),  # current row + 6 preceding
    )
)
```

### Custom Database Functions

When Django's built-in functions don't cover a DB-specific function, extend `Func` directly.

```python
from django.db.models import Func, FloatField, CharField, IntegerField

# PostgreSQL EXTRACT — extract part of a date
class Extract(Func):
    function = "EXTRACT"
    template = "%(function)s(%(part)s FROM %(expressions)s)"

    def __init__(self, expression, part, **extra):
        super().__init__(expression, part=part, **extra)

# PostgreSQL DATE_TRUNC — truncate a timestamp to a precision
class DateTrunc(Func):
    function = "DATE_TRUNC"
    template = "%(function)s('%(precision)s', %(expressions)s)"

    def __init__(self, expression, precision="month", **extra):
        super().__init__(expression, precision=precision, **extra)

# PostgreSQL STRING_AGG — aggregate strings with a delimiter
class StringAgg(Func):
    function = "STRING_AGG"
    template = "%(function)s(%(expressions)s, '%(delimiter)s')"
    output_field = CharField()

    def __init__(self, expression, delimiter=", ", **extra):
        super().__init__(expression, delimiter=delimiter, **extra)

# Usage
JournalEntry.objects.annotate(
    month=DateTrunc("date", precision="month")
).values("month").annotate(
    total_debit=Sum("lines__debit"),
    entry_refs=StringAgg("reference", delimiter=" | "),
)
```

### Raw SQL — For When the ORM Genuinely Can't Express It

The ORM covers ~95% of real-world queries. For the remaining 5%, use raw SQL — but always prefer `connection.cursor()` with parameterized queries over f-string interpolation, which is vulnerable to SQL injection.

```python
from django.db import connection

# Raw queryset — returns model instances, supports parameter substitution
# Use %s for positional params (NOT Python f-strings!)
entries = JournalEntry.objects.raw(
    """
    SELECT
        je.id,
        je.date,
        je.reference,
        je.status,
        SUM(jel.debit)  AS total_debit,
        SUM(jel.credit) AS total_credit
    FROM journal_entry je
    JOIN journal_entry_line jel ON jel.journal_entry_id = je.id
    WHERE je.company_id = %s
      AND je.status = %s
    GROUP BY je.id, je.date, je.reference, je.status
    HAVING SUM(jel.debit) <> SUM(jel.credit)
    ORDER BY je.date DESC
    """,
    [company.id, "posted"]
)
# Accessing entry.total_debit works because it's an extra column — Django attaches it

# cursor() — for queries that don't map to a model (reporting, analytics, DDL)
def get_monthly_trial_balance(company_id, year):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH monthly_totals AS (
                SELECT
                    DATE_TRUNC('month', je.date)::DATE AS month,
                    jel.coa_account_id,
                    coa.code                           AS account_code,
                    coa.name                           AS account_name,
                    coa.account_type,
                    SUM(jel.debit)                     AS total_debit,
                    SUM(jel.credit)                    AS total_credit
                FROM journal_entry_line jel
                INNER JOIN journal_entry je
                    ON je.id = jel.journal_entry_id
                INNER JOIN chart_of_account coa
                    ON coa.id = jel.coa_account_id
                WHERE je.company_id = %s
                  AND je.status    = 'posted'
                  AND EXTRACT(year FROM je.date) = %s
                GROUP BY 1, 2, 3, 4, 5
            ),
            running_balance AS (
                SELECT
                    *,
                    SUM(total_debit - total_credit) OVER (
                        PARTITION BY coa_account_id
                        ORDER BY month
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) AS running_balance
                FROM monthly_totals
            )
            SELECT *
            FROM running_balance
            ORDER BY account_code, month
            """,
            [company_id, year]
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
```

### Inspecting Queries — What Is Django Actually Sending?

```python
from django.db import connection, reset_queries

# Force DEBUG=True in settings to populate connection.queries

reset_queries()
qs = JournalEntry.objects.select_related("company").prefetch_related("lines")
list(qs)  # force evaluation

print(f"Queries fired: {len(connection.queries)}")
for q in connection.queries:
    print(f"[{q['time']}s] {q['sql']}\n")

# Get the SQL for any queryset without executing it
print(JournalEntry.objects.filter(status="posted").query)

# EXPLAIN — see the query plan
# PostgreSQL supports verbose=True, analyze=True, buffers=True, format="json"
print(
    JournalEntry.objects
    .filter(company=company, status="posted")
    .select_related("company")
    .explain(verbose=True, analyze=True)
)
# Look for: Seq Scan on large tables (missing index), Hash Join vs Index Scan,
# nested loops with high row estimates, high startup cost operations

# Use django-debug-toolbar in development — it shows all queries per request
# pip install django-debug-toolbar
```

---

## Level 5 — Legend: Optimization, Locking & The Heavily Nested Example

### only() and defer() — Surgical Field Loading

`only()` tells Django to SELECT only the specified fields; all others are deferred (fetched lazily on access). `defer()` is the inverse — select everything EXCEPT the listed fields. Both reduce the amount of data transferred from the database, which matters when rows have large text or JSON columns.

```python
# only() — SELECT id, date, status FROM journal_entry WHERE ...
# Accessing any other field on the instance triggers a separate SELECT
entries = JournalEntry.objects.only("id", "date", "status")

# defer() — SELECT everything EXCEPT description and notes
entries = JournalEntry.objects.defer("description")

# Danger: accessing a deferred field causes 1 extra query PER OBJECT
entries = JournalEntry.objects.only("id", "status")
for entry in entries:
    print(entry.description)  # triggers SELECT id, description FROM ... WHERE id = X for EACH entry

# Safe pattern: know exactly which fields your serializer uses, only() those
# Never use only() unless you've profiled and confirmed it helps

# only() with select_related — must include FK id fields explicitly
JournalEntry.objects.only(
    "id", "date", "status",
    "company_id",          # include the FK column itself
    "company__name",       # also select company name via JOIN
).select_related("company")
```

### iterator() — Streaming Large QuerySets Without Memory Explosion

Without `iterator()`, Django fetches the entire queryset result set and holds it in memory. For large datasets (tens of thousands of rows), this can exhaust RAM. `iterator()` fetches rows in chunks and yields them one at a time.

```python
# Without iterator() — ALL rows loaded into Python memory simultaneously
for entry in JournalEntry.objects.filter(status="posted"):
    process(entry)   # 500,000 entries = 500,000 Python objects in RAM

# With iterator() — rows fetched in chunks, one object alive at a time
for entry in JournalEntry.objects.filter(status="posted").iterator(chunk_size=2000):
    process(entry)   # only chunk_size objects in RAM at any time

# Combine with only() for maximum efficiency on large datasets
for line in JournalEntryLine.objects.only("id", "debit", "credit").iterator(chunk_size=5000):
    process(line)

# IMPORTANT: iterator() is incompatible with prefetch_related
# If you need related data with iterator(), use select_related only
for entry in (
    JournalEntry.objects
    .select_related("company", "created_by")   # OK — uses JOIN
    .filter(status="posted")
    .iterator(chunk_size=1000)
):
    process(entry)
```

### select_for_update() — Row-Level Pessimistic Locking

When multiple processes or threads might modify the same rows concurrently, you need database-level locking. `select_for_update()` issues `SELECT ... FOR UPDATE`, which locks the selected rows until the current transaction commits or rolls back. Must be inside `transaction.atomic()`.

```python
from django.db import transaction

# Lock a single row — no other transaction can UPDATE or DELETE it until we commit
with transaction.atomic():
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)
    if entry.status != "draft":
        raise ValueError("Only draft entries can be posted")
    entry.status = "posted"
    entry.save()

# nowait=True — raise DatabaseError immediately instead of blocking if lock is unavailable
# Useful for async contexts or when blocking is unacceptable
with transaction.atomic():
    try:
        entry = JournalEntry.objects.select_for_update(nowait=True).get(id=entry_id)
    except Exception:
        raise ValueError("Entry is currently being modified by another process")

# skip_locked=True — skip rows that are locked, process only available ones
# Perfect for job queues where multiple workers process different entries concurrently
with transaction.atomic():
    entries = JournalEntry.objects.select_for_update(
        skip_locked=True
    ).filter(status="draft")[:10]
    for entry in entries:
        process_and_post(entry)

# of= — lock only specific tables in a multi-table query (PostgreSQL)
with transaction.atomic():
    entry = JournalEntry.objects.select_related("company").select_for_update(
        of=("self",)  # lock only the journal_entry row, not company
    ).get(id=entry_id)
```

### Atomic Transactions — All or Nothing

```python
from django.db import transaction

# Decorator — entire function runs in one transaction
@transaction.atomic
def post_journal_entry(entry_id: int, approved_by_id: int) -> JournalEntry:
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)

    if entry.status != "draft":
        raise ValueError(f"Cannot post entry with status '{entry.status}'")

    totals = entry.lines.aggregate(
        total_debit=Sum("debit"),
        total_credit=Sum("credit"),
    )
    if totals["total_debit"] != totals["total_credit"]:
        raise ValueError(
            f"Entry is unbalanced: debit={totals['total_debit']}, credit={totals['total_credit']}"
        )
    if not entry.lines.exists():
        raise ValueError("Cannot post an entry with no lines")

    from django.utils import timezone
    entry.status = "posted"
    entry.approved_by_id = approved_by_id
    entry.approved_at = timezone.now()
    entry.save(update_fields=["status", "approved_by_id", "approved_at", "updated_at"])
    return entry

# Context manager — finer-grained control with savepoints
def create_entry_with_lines(header_data: dict, lines_data: list) -> JournalEntry:
    with transaction.atomic():
        entry = JournalEntry.objects.create(**header_data)

        lines = [JournalEntryLine(journal_entry=entry, **ld) for ld in lines_data]
        JournalEntryLine.objects.bulk_create(lines)

        # Savepoint — partial rollback if optional step fails
        # The outer transaction is NOT rolled back if this inner block fails
        try:
            with transaction.atomic():
                send_notification(entry)   # optional, non-critical
        except Exception:
            pass  # savepoint rolled back; outer transaction proceeds

        return entry

# on_commit hook — run code ONLY after the transaction successfully commits
# Use for side effects: sending emails, firing Celery tasks, webhooks
def post_entry(entry_id):
    with transaction.atomic():
        entry = JournalEntry.objects.select_for_update().get(id=entry_id)
        entry.status = "posted"
        entry.save()

        # This runs AFTER commit — NOT if the transaction rolls back
        transaction.on_commit(lambda: send_posting_email.delay(entry_id))
        transaction.on_commit(lambda: sync_to_erp.delay(entry_id))
```

### Indexes — The Single Highest-Impact Optimization

No amount of ORM optimization compensates for a missing index on a hot query path. Understanding which indexes to create — and which ones waste space — is what separates senior engineers from the rest.

```python
class JournalEntry(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, db_index=True)
    date = models.DateField()
    status = models.CharField(max_length=20)
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            # Composite index — covers WHERE company_id = X AND date BETWEEN ...
            # Column order matters: put the most selective filter first
            models.Index(fields=["company", "date"], name="je_company_date_idx"),

            # Partial index (PostgreSQL only) — indexes ONLY posted entries
            # Much smaller and faster than indexing all statuses
            models.Index(
                fields=["company", "date"],
                condition=models.Q(status="posted"),
                name="je_company_date_posted_idx",
            ),

            # Index for status filtering per company
            models.Index(fields=["company", "status"], name="je_company_status_idx"),

            # Covering index (PostgreSQL) — includes extra columns so the query
            # can be satisfied entirely from the index without hitting the table
            # Requires third-party: django-covering-indexes or raw migration
        ]

class JournalEntryLine(TimestampedModel):
    class Meta:
        indexes = [
            # Covers: filter by account + order by entry date
            models.Index(
                fields=["coa_account", "journal_entry"],
                name="jel_account_entry_idx"
            ),
        ]

# When to NOT add an index:
# - Columns with very low cardinality (e.g. a boolean, a status with 2 values) — full scan is faster
# - Tables with fewer than ~10,000 rows — indexes add write overhead for minimal read gain
# - Columns that are only written, never read-filtered
# - Already covered by the leftmost columns of another composite index

# How to detect missing indexes:
# .explain(analyze=True) and look for "Seq Scan" on large tables
# Or enable pg_stat_statements and look for high total_time queries
```

---

## The Heavily Nested Example — Everything at Once

This is a single queryset that combines `select_related`, `prefetch_related`, `Prefetch`, nested `select_related` inside `Prefetch`, `annotate`, `Subquery`, `OuterRef`, `Exists`, `Case/When`, `F()`, `Window`, `Q` objects, and `values()` — all in one production-grade query. This is the kind of query you write when you need a complete financial dashboard in as few DB roundtrips as possible.

**Business requirement:** For a given company, return all posted journal entries in a period with:
- All lines eagerly loaded with their account and cost center
- The total debit, credit, and line count per entry
- A flag for whether the entry is balanced
- A flag for whether the entry has any expense lines
- The account name of the largest debit line
- The entry's rank by total debit within the period
- Budget vs actual for each line's account in the same period
- A human-readable status label
- Only entries where total debit is above a threshold OR the entry was approved by a specific user

```python
from django.db.models import (
    Sum, Count, Max, F, Q, Value, Case, When,
    OuterRef, Subquery, Exists, Window, Rank,
    DecimalField, CharField, BooleanField, IntegerField,
    ExpressionWrapper, Prefetch,
)
from django.db.models.functions import Coalesce


def get_dashboard_entries(company, date_from, date_to, min_amount=0, approver=None):
    """
    Single-function, minimal-query financial dashboard queryset.
    Designed to power a full accounting dashboard with one primary DB roundtrip
    (plus 2 for prefetch_related).
    """

    # -------------------------------------------------------------------------
    # Subquery 1: Name of the account with the highest debit in each entry
    # Correlated to the outer JournalEntry via OuterRef("pk")
    # -------------------------------------------------------------------------
    largest_debit_line = (
        JournalEntryLine.objects
        .filter(journal_entry=OuterRef("pk"))          # correlate to outer entry
        .order_by("-debit")                            # descending to get the largest
        .select_related("coa_account")
        .values("coa_account__name")[:1]               # take top 1, single column
    )

    # -------------------------------------------------------------------------
    # Subquery 2: Year-to-date budget for each entry's company
    # This is a scalar subquery — returns a single decimal per entry
    # -------------------------------------------------------------------------
    ytd_budget = (
        Budget.objects
        .filter(
            company=OuterRef("company"),
            year=date_from.year,
            month__lte=date_from.month,
        )
        .values("company")                             # group key for aggregation
        .annotate(total=Sum("amount"))
        .values("total")[:1]                           # scalar — one value
    )

    # -------------------------------------------------------------------------
    # Subquery 3: Does this entry have any expense-type lines?
    # Exists() is the most efficient way — translates to SELECT 1 WHERE EXISTS(...)
    # -------------------------------------------------------------------------
    has_expense = Exists(
        JournalEntryLine.objects.filter(
            journal_entry=OuterRef("pk"),
            coa_account__account_type="expense",
        )
    )

    # -------------------------------------------------------------------------
    # Prefetch: Load lines with their FKs eagerly
    # We filter to only debit lines here to demonstrate filtered prefetch;
    # in practice you might want all lines
    # -------------------------------------------------------------------------
    lines_prefetch = Prefetch(
        "lines",
        queryset=(
            JournalEntryLine.objects
            .select_related(
                "coa_account",               # FK on line
                "coa_account__parent",       # FK on account's parent account
                "cost_center",               # FK on line
                "cost_center__parent",       # self-referential FK on cost center
            )
            .order_by("coa_account__code")
            .annotate(
                net=ExpressionWrapper(
                    F("debit") - F("credit"),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                )
            )
        ),
        to_attr="prefetched_lines",          # accessible as entry.prefetched_lines (list)
    )

    # -------------------------------------------------------------------------
    # Dynamic Q filter: apply threshold OR approver condition
    # -------------------------------------------------------------------------
    dynamic_filter = Q(total_debit__gte=min_amount)
    if approver:
        dynamic_filter |= Q(approved_by=approver)

    # -------------------------------------------------------------------------
    # The main queryset — all pieces assembled
    # -------------------------------------------------------------------------
    qs = (
        JournalEntry.objects

        # ── Eager load direct FKs via JOIN ──────────────────────────────────
        .select_related(
            "company",
            "created_by",
            "approved_by",
        )

        # ── Eager load reverse FK (lines) via separate query ────────────────
        .prefetch_related(lines_prefetch)

        # ── Base filter ─────────────────────────────────────────────────────
        .filter(
            company=company,
            status="posted",
            date__range=(date_from, date_to),
        )

        # ── Annotations — computed columns per entry ─────────────────────────
        .annotate(
            # Aggregate line totals
            total_debit=Coalesce(
                Sum("lines__debit"),
                Value(0),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
            total_credit=Coalesce(
                Sum("lines__credit"),
                Value(0),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
            line_count=Count("lines", distinct=True),

            # Is the entry balanced? Compare two annotated values with F()
            is_balanced=Case(
                When(total_debit=F("total_credit"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),

            # Human-readable status label
            status_label=Case(
                When(status="posted", approved_by__isnull=False, then=Value("Posted & Approved")),
                When(status="posted", approved_by__isnull=True, then=Value("Posted, Pending Approval")),
                When(status="draft", then=Value("Draft")),
                When(status="voided", then=Value("Voided")),
                default=Value("Unknown"),
                output_field=CharField(),
            ),

            # Subquery annotations
            largest_debit_account=Subquery(
                largest_debit_line,
                output_field=CharField(),
            ),
            ytd_budget_total=Subquery(
                ytd_budget,
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),

            # Exists annotation
            has_expense_lines=has_expense,

            # Budget variance — how much actual debit exceeds (or falls under) budget
            budget_variance=ExpressionWrapper(
                Coalesce(Sum("lines__debit"), Value(0), output_field=DecimalField()) -
                Coalesce(
                    Subquery(ytd_budget, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),

            # Window function — rank each entry by total debit within the period
            # All rows are in the same window (no PARTITION BY) so this ranks globally
            debit_rank=Window(
                expression=Rank(),
                order_by=F("total_debit").desc(),
            ),

            # Conditional count — how many expense lines specifically
            expense_line_count=Count(
                "lines",
                filter=Q(lines__coa_account__account_type="expense"),
            ),
            revenue_line_count=Count(
                "lines",
                filter=Q(lines__coa_account__account_type="revenue"),
            ),
        )

        # ── Post-annotation filter (uses HAVING via annotated fields) ─────────
        .filter(dynamic_filter)

        # ── Ordering ──────────────────────────────────────────────────────────
        .order_by("debit_rank", "-date")
    )

    return qs


# ─── Usage ────────────────────────────────────────────────────────────────────
from datetime import date

entries = get_dashboard_entries(
    company=company,
    date_from=date(2024, 1, 1),
    date_to=date(2024, 12, 31),
    min_amount=5000,
    approver=request.user,
)

# Accessing data — zero extra queries because everything was eagerly loaded
for entry in entries:
    print(f"Entry #{entry.id} — {entry.company.name}")          # select_related
    print(f"  Status: {entry.status_label}")                    # annotation
    print(f"  Debit: {entry.total_debit}, Credit: {entry.total_credit}")
    print(f"  Balanced: {entry.is_balanced}")                   # Case/When annotation
    print(f"  Rank by debit: #{entry.debit_rank}")              # Window annotation
    print(f"  Largest account: {entry.largest_debit_account}")  # Subquery annotation
    print(f"  Has expenses: {entry.has_expense_lines}")         # Exists annotation
    print(f"  Budget variance: {entry.budget_variance}")        # compound annotation
    print(f"  Approved by: {entry.approved_by}")                # select_related (nullable)

    for line in entry.prefetched_lines:                         # prefetched list — no query
        print(f"    {line.coa_account.code} — {line.coa_account.name}")  # select_related
        if line.coa_account.parent:
            print(f"      Parent: {line.coa_account.parent.name}")       # select_related
        if line.cost_center:
            print(f"      Cost center: {line.cost_center.name}")         # select_related
            if line.cost_center.parent:
                print(f"        Under: {line.cost_center.parent.name}") # select_related
        print(f"      Net: {line.net}")                                  # annotated on line
# Total DB queries for the entire above loop: 3
# Query 1: the main JournalEntry queryset (with all JOINs from select_related)
# Query 2: the prefetch_related lines query (with JOINs for coa_account, cost_center, parents)
# Query 3: (none — everything is cached)
```

---

## Performance Patterns — The N+1 Killer Checklist

Walk through this checklist before any queryset goes to production:

**1. Relationship coverage** — Map every field your serializer or view code accesses on related objects. Every FK → `select_related`. Every reverse FK or M2M → `prefetch_related`. Every FK on a prefetched object → nested `select_related` inside `Prefetch()`.

**2. Loop hygiene** — If you're calling `.save()`, `.update()`, or `.create()` inside a for loop, you're doing N database roundtrips. Replace with `bulk_update`, `bulk_create`, or a queryset-level `.update()` with `F()` expressions.

**3. Field projection** — If your view only needs `id`, `name`, and `status`, don't SELECT `*`. Use `.only()` or `.values()`. This is especially impactful when rows have large `TextField` or `JSONField` columns.

**4. Aggregations, not Python loops** — If you're summing, counting, or averaging in Python after fetching rows, push it to the database with `aggregate()` or `annotate()`.

**5. Existence checks** — Never `len(qs) > 0` or `bool(list(qs))`. Use `.exists()` — it generates `SELECT 1 ... LIMIT 1`, far cheaper.

**6. Memory management** — For queries returning more than ~10,000 rows in a data pipeline, use `.iterator(chunk_size=N)` to stream instead of loading everything into memory.

**7. Transactions** — Any operation touching multiple rows that must succeed or fail together goes inside `transaction.atomic()`. Side effects (emails, tasks) go in `transaction.on_commit()`.

**8. Locking** — Any read-then-write pattern on a row (check status, then update) must use `select_for_update()` inside `transaction.atomic()` to prevent race conditions.

**9. Index audit** — Every field in a `.filter()` that isn't the primary key should have an index, or be covered by a composite index. Run `.explain(analyze=True)` and check for `Seq Scan`.

**10. Query counting** — Use `django-debug-toolbar` in development and `connection.queries` in tests to count queries per view. Any view returning a list of objects should fire at most 2-3 queries (1 main + 1-2 prefetch).

---

## Quick Reference — The Legend Cheat Sheet

| Situation | Tool | Notes |
|---|---|---|
| FK / OneToOne in code or serializer | `select_related` | SQL JOIN — one query |
| Reverse FK / M2M in code or serializer | `prefetch_related` | 2 queries total |
| Filter or annotate the prefetched set | `Prefetch(queryset=...)` | Full control |
| Store prefetch as a list attribute | `Prefetch(to_attr=...)` | Avoids `.all()` call |
| FK on a prefetched object | Nested `select_related` inside `Prefetch` | Prevents N+1 inside prefetch |
| Load only specific fields | `.only("field1", "field2")` | Deferred access = extra query |
| Skip heavy fields | `.defer("large_text_field")` | Load on demand |
| OR / NOT logic | `Q` objects | Composable with `&`, `\|`, `~` |
| Build filters dynamically | `Q()` accumulator with `&=` / `\|=` | Clean pattern for search APIs |
| Collapse queryset to a single dict | `aggregate()` | Terminates queryset |
| Add computed column per row | `annotate()` | Chainable, filterable |
| GROUP BY | `.values(...).annotate(...)` | Order matters: values before annotate |
| Reference row field in expression | `F("field")` | No Python roundtrip |
| Conditional column | `Case(When(..., then=...), default=...)` | SQL CASE WHEN |
| Correlated subquery | `Subquery(qs)` + `OuterRef("pk")` | Avoids JOIN row multiplication |
| Efficient "does related row exist" | `Exists(qs)` | SELECT 1 WHERE EXISTS |
| Running totals / rankings / lag | `Window(expression=..., partition_by=..., order_by=...)` | DB-level analytics |
| Custom DB function | Extend `Func` | Any SQL function |
| Return dicts (no model instances) | `.values(...)` | Faster for projections |
| Return flat list of one field | `.values_list("field", flat=True)` | Great for `id__in=` |
| Insert many rows efficiently | `bulk_create(list, batch_size=N)` | Single INSERT |
| Update many rows efficiently | `bulk_update(list, fields=[...])` | Single UPDATE |
| Update all rows matching filter | `.update(field=F("field") * 2)` | No Python loop at all |
| Process millions of rows without OOM | `.iterator(chunk_size=N)` | Incompatible with prefetch |
| Race-condition-safe read+write | `select_for_update()` inside `atomic()` | SELECT FOR UPDATE |
| Skip locked rows (worker pattern) | `select_for_update(skip_locked=True)` | Multi-worker queue |
| Fail fast if locked | `select_for_update(nowait=True)` | Raises immediately |
| All-or-nothing writes | `transaction.atomic()` | Decorator or context manager |
| Savepoint (partial rollback) | Nested `transaction.atomic()` | Inner rollback, outer proceeds |
| Side effects after commit | `transaction.on_commit(fn)` | Emails, Celery tasks |
| Inspect query plan | `.explain(analyze=True)` | Look for Seq Scan |
| Count queries in tests | `connection.queries` + `reset_queries()` | Requires DEBUG=True |
| DB-level data integrity | `Meta.constraints` with `CheckConstraint` | Last line of defense |
| Partial index (PostgreSQL) | `Index(fields=..., condition=Q(...))` | Index subset of rows |
| Encapsulate query logic | Custom `QuerySet` + `Manager` | Chainable, reusable methods |

---

*This guide covers every querying pattern you will encounter in production Django. Master the relationships and N+1 patterns first — they account for 80% of real performance problems. Then internalize annotations, subqueries, and window functions. The heavily nested example at the end is the blueprint: three DB queries, a full financial dashboard, zero loops hitting the database.*
