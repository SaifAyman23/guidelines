# The Ultimate Django Managers & Concurrency Guide
### Custom Managers, QuerySet Methods, Transactions, Locking & Safe Concurrent Writes

---

## The Data Model Used Throughout This Guide

The same accounting schema from the querying guide is used here, so every example maps directly to a real system.

```python
# models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimestampedModel):
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, default="USD")


class AccountingPeriod(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)


class ChartOfAccount(TimestampedModel):
    ACCOUNT_TYPES = [
        ("asset", "Asset"), ("liability", "Liability"),
        ("equity", "Equity"), ("revenue", "Revenue"), ("expense", "Expense"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="accounts")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    is_active = models.BooleanField(default=True)


class CostCenter(TimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="cost_centers")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)


class JournalEntry(TimestampedModel):
    STATUS_CHOICES = [
        ("draft", "Draft"), ("posted", "Posted"), ("voided", "Voided"),
    ]
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="journal_entries")
    accounting_period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT)
    date = models.DateField()
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    total_debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_entries")
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_entries")
    approved_at = models.DateTimeField(null=True, blank=True)
    reversal_of = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reversed")
    reverse_entry = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reverse")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "date"], name="je_company_date_idx"),
            models.Index(fields=["company", "status"], name="je_company_status_idx"),
        ]


class JournalEntryLine(TimestampedModel):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    coa_account = models.ForeignKey(ChartOfAccount, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField(blank=True)
```

---

## Table of Contents

1. [Understanding Managers vs QuerySets](#1-understanding-managers-vs-querysets)
2. [Custom QuerySets — Encapsulating Query Logic](#2-custom-querysets--encapsulating-query-logic)
3. [Custom Managers — Controlling the Entry Point](#3-custom-managers--controlling-the-entry-point)
4. [Multiple Managers on One Model](#4-multiple-managers-on-one-model)
5. [Manager Inheritance Across Abstract Models](#5-manager-inheritance-across-abstract-models)
6. [transaction.atomic() — All or Nothing](#6-transactionatomic--all-or-nothing)
7. [select_for_update() — Row-Level Locking](#7-select_for_update--row-level-locking)
8. [Combining Locking and Transactions — The Full Pattern](#8-combining-locking-and-transactions--the-full-pattern)
9. [nowait and skip_locked — Non-Blocking Patterns](#9-nowait-and-skip_locked--non-blocking-patterns)
10. [transaction.on_commit() — Safe Side Effects](#10-transactionon_commit--safe-side-effects)
11. [Savepoints — Partial Rollbacks](#11-savepoints--partial-rollbacks)
12. [Common Concurrency Pitfalls and How to Fix Them](#12-common-concurrency-pitfalls-and-how-to-fix-them)
13. [Manager Patterns for Finite State Machines](#13-manager-patterns-for-finite-state-machines)
14. [Testing Managers and Transactions](#14-testing-managers-and-transactions)
15. [Quick Reference Cheat Sheet](#15-quick-reference-cheat-sheet)

---

## 1. Understanding Managers vs QuerySets

Before writing a single line of custom code, you need to understand the relationship between these two objects because they serve different purposes and live at different layers.

A **Manager** is the interface attached to the model class. It's what you access via `Model.objects`. It is responsible for creating new QuerySets and acts as the entry point from the model to the database. By default Django gives every model a manager named `objects` that returns a plain `QuerySet`.

A **QuerySet** is the object returned by the manager. It represents a lazy database query that you can chain filters, annotations, and other clauses onto. It is evaluated only when you force it (by iterating, slicing, calling `list()`, etc.).

The critical insight: **custom logic should almost always live on a custom QuerySet, not directly on the Manager**. The reason is that QuerySet methods are chainable — if you put your logic on the Manager, it's only available as the first call. If you put it on a QuerySet, it works anywhere in the chain.

```python
# If logic lives ONLY on the Manager:
JournalEntry.objects.posted()               # works
JournalEntry.objects.posted().for_company() # AttributeError — QuerySet has no for_company()

# If logic lives on the QuerySet (and the Manager proxies it):
JournalEntry.objects.posted()                          # works
JournalEntry.objects.for_company(c).posted()           # works
JournalEntry.objects.posted().for_company(c).in_year() # works — fully chainable
```

The standard pattern is: write everything on a custom QuerySet, then have the Manager return that QuerySet class so all methods are available from both the Manager and mid-chain.

---

## 2. Custom QuerySets — Encapsulating Query Logic

A custom QuerySet is a class that extends `models.QuerySet`. Every method you define must return `self.filter(...)`, `self.exclude(...)`, or another QuerySet operation so it stays chainable.

```python
from django.db.models import QuerySet, Sum, Count, Q, F, Prefetch
from django.utils import timezone


class JournalEntryQuerySet(QuerySet):
    """
    All query logic for JournalEntry lives here.
    Every method returns a QuerySet so they can be chained arbitrarily.
    """

    # ── Status filters ────────────────────────────────────────────────────────

    def posted(self):
        return self.filter(status="posted")

    def draft(self):
        return self.filter(status="draft")

    def voided(self):
        return self.filter(status="voided")

    def pending(self):
        """Draft entries that are older than 24 hours — stale and should be reviewed."""
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        return self.filter(status="draft", created_at__lte=cutoff)

    # ── Relationship filters ───────────────────────────────────────────────────

    def for_company(self, company):
        return self.filter(company=company)

    def for_period(self, period):
        return self.filter(accounting_period=period)

    def in_open_periods(self):
        return self.filter(accounting_period__is_closed=False)

    def created_by(self, user):
        return self.filter(created_by=user)

    def approved_by(self, user):
        return self.filter(approved_by=user)

    def unapproved(self):
        return self.filter(status="posted", approved_by__isnull=True)

    # ── Date filters ──────────────────────────────────────────────────────────

    def in_year(self, year):
        return self.filter(date__year=year)

    def in_month(self, year, month):
        return self.filter(date__year=year, date__month=month)

    def in_date_range(self, date_from, date_to):
        return self.filter(date__range=(date_from, date_to))

    def recent(self, days=30):
        cutoff = timezone.now().date() - timezone.timedelta(days=days)
        return self.filter(date__gte=cutoff)

    # ── Data integrity filters ────────────────────────────────────────────────

    def unbalanced(self):
        """
        Entries where total debit != total credit.
        Annotates first so we can filter on the computed values.
        In a healthy system, this should always return empty.
        """
        return self.annotate(
            computed_debit=Sum("lines__debit"),
            computed_credit=Sum("lines__credit"),
        ).exclude(computed_debit=F("computed_credit"))

    def with_no_lines(self):
        """Draft entries that somehow have zero lines — invalid state."""
        return self.annotate(line_count=Count("lines")).filter(line_count=0)

    def reversals(self):
        """Only entries that are reversals of another entry."""
        return self.filter(reversal_of__isnull=False)

    def not_reversed(self):
        """Posted entries that have not yet been reversed."""
        return self.filter(status="posted", reverse_entry__isnull=True)

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, term):
        return self.filter(
            Q(description__icontains=term) |
            Q(reference__icontains=term) |
            Q(lines__description__icontains=term)
        ).distinct()

    # ── Eager loading ─────────────────────────────────────────────────────────

    def with_lines(self):
        """
        Use this whenever you'll access entry.lines in a loop or serializer.
        Prevents N+1 on lines and their FK relationships.
        """
        return self.prefetch_related(
            Prefetch(
                "lines",
                queryset=JournalEntryLine.objects.select_related(
                    "coa_account",
                    "cost_center",
                ).order_by("id")
            )
        )

    def with_related(self):
        """Full eager load for API serialization."""
        return self.select_related(
            "company",
            "accounting_period",
            "created_by",
            "approved_by",
            "reversal_of",
            "reverse_entry",
        ).prefetch_related(
            Prefetch(
                "lines",
                queryset=JournalEntryLine.objects.select_related(
                    "coa_account",
                    "cost_center",
                ).order_by("id")
            )
        )

    # ── Annotation shortcuts ──────────────────────────────────────────────────

    def with_totals(self):
        """Annotate computed debit/credit totals and line count."""
        return self.annotate(
            computed_debit=Sum("lines__debit"),
            computed_credit=Sum("lines__credit"),
            line_count=Count("lines", distinct=True),
        )

    def with_balance_flag(self):
        """Annotate a boolean is_balanced field (requires with_totals() first or combined)."""
        from django.db.models import BooleanField, Case, When, Value
        return self.with_totals().annotate(
            is_balanced=Case(
                When(computed_debit=F("computed_credit"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
```

A key rule: **every method that filters or annotates must return `self.something()`**. Never return a new queryset from scratch (`JournalEntry.objects.filter(...)`) inside a QuerySet method — that breaks the chain and ignores any prior filters the caller may have applied.

---

## 3. Custom Managers — Controlling the Entry Point

The Manager's primary job is to return your custom QuerySet. It also serves as a good place to put factory methods — class-level operations that create objects with enforced business rules.

```python
from django.db import models, transaction
from django.utils import timezone


class JournalEntryManager(models.Manager):
    """
    The Manager controls what .objects returns and provides factory methods
    for creating entries with enforced business rules.
    """

    def get_queryset(self):
        """
        Always return our custom QuerySet.
        This is the single override that makes all QuerySet methods
        available on JournalEntry.objects.
        """
        return JournalEntryQuerySet(self.model, using=self._db)

    # ── Proxy methods — convenience shortcuts from the manager directly ────────
    # These are optional. They let you call JournalEntry.objects.posted()
    # directly, which reads nicer than JournalEntry.objects.all().posted()
    # even though both work.

    def posted(self):
        return self.get_queryset().posted()

    def draft(self):
        return self.get_queryset().draft()

    def for_company(self, company):
        return self.get_queryset().for_company(company)

    def unapproved(self):
        return self.get_queryset().unapproved()

    # ── Factory methods — enforce business rules at creation time ─────────────

    def create_draft(self, company, accounting_period, date, created_by, **kwargs):
        """
        Safe entry point for creating a new draft journal entry.
        Enforces that the accounting period belongs to the company
        and that the period is still open.
        """
        if accounting_period.company_id != company.pk:
            raise ValueError("Accounting period does not belong to this company.")
        if accounting_period.is_closed:
            raise ValueError(f"Accounting period '{accounting_period.name}' is closed.")

        return self.create(
            company=company,
            accounting_period=accounting_period,
            date=date,
            created_by=created_by,
            status="draft",
            **kwargs,
        )

    def get_or_create_draft(self, company, reference, accounting_period, created_by, defaults=None):
        """
        Idempotent creation — finds an existing draft by reference or creates one.
        Useful for import jobs that may re-run.
        """
        return self.get_or_create(
            company=company,
            reference=reference,
            status="draft",
            defaults={
                "accounting_period": accounting_period,
                "created_by": created_by,
                **(defaults or {}),
            }
        )


# Attach the manager to the model
class JournalEntry(TimestampedModel):
    # ... fields ...

    objects = JournalEntryManager()

    class Meta:
        indexes = [...]
```

With this setup, every one of the following works and is fully chainable:

```python
# Via manager shortcut
JournalEntry.objects.posted()

# Via QuerySet chain — both identical in behavior
JournalEntry.objects.all().posted()
JournalEntry.objects.posted().for_company(c).in_year(2024).with_lines()

# Factory method with enforced rules
entry = JournalEntry.objects.create_draft(
    company=company,
    accounting_period=period,
    date=date.today(),
    created_by=request.user,
    description="Payroll June 2024",
)
```

---

## 4. Multiple Managers on One Model

A model can have multiple managers. The most common use case is having a default manager that shows all objects and a second manager that automatically filters to a subset. This is useful for soft-delete patterns or multi-tenant models.

```python
class ActiveCompanyQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_entries(self):
        return self.prefetch_related("journal_entries")


class AllCompanyManager(models.Manager):
    """Returns all companies including inactive — use for admin, reports."""
    def get_queryset(self):
        return ActiveCompanyQuerySet(self.model, using=self._db)


class ActiveCompanyManager(models.Manager):
    """Returns only active companies — safe default for most views."""
    def get_queryset(self):
        return ActiveCompanyQuerySet(self.model, using=self._db).filter(is_active=True)


class Company(TimestampedModel):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    # The FIRST manager defined becomes the default (.objects by default)
    # Django also uses the first manager for related object lookups
    objects = ActiveCompanyManager()     # default — always filters to active
    all_objects = AllCompanyManager()    # explicit — bypasses the active filter


# Usage
Company.objects.all()            # only active companies
Company.all_objects.all()        # all companies including inactive
Company.objects.active()         # redundant but works — is_active=True twice is fine
```

**Critical rule about the default manager:** Django uses the first manager defined on the model for internal operations like `select_related` traversal, the admin, and related object lookups. If your default manager filters rows out, those rows can become invisible in related queries. Be careful — filtering in the default manager is a footgun if you have FKs pointing to the filtered-out rows.

---

## 5. Manager Inheritance Across Abstract Models

When you have an abstract base model (`TimestampedModel`), its manager is inherited by all child models. This is a great way to give every model in your system a consistent set of base QuerySet methods without repeating yourself.

```python
class TimestampedQuerySet(models.QuerySet):
    """Methods available on EVERY model that inherits from TimestampedModel."""

    def recent(self, days=30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)

    def created_before(self, dt):
        return self.filter(created_at__lt=dt)

    def created_after(self, dt):
        return self.filter(created_at__gte=dt)

    def oldest_first(self):
        return self.order_by("created_at")

    def newest_first(self):
        return self.order_by("-created_at")


class TimestampedManager(models.Manager):
    def get_queryset(self):
        return TimestampedQuerySet(self.model, using=self._db)


class TimestampedModel(models.Model):
    objects = TimestampedManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Every model that extends TimestampedModel automatically gets these methods:
class JournalEntry(TimestampedModel):
    # Override objects with a more specific manager that also inherits base methods
    objects = JournalEntryManager()  # JournalEntryManager.get_queryset() should return
                                     # a QuerySet that also includes TimestampedQuerySet methods
    # ...


# If you want JournalEntryQuerySet to also have TimestampedQuerySet's methods,
# inherit from it:
class JournalEntryQuerySet(TimestampedQuerySet):
    """Inherits all TimestampedQuerySet methods and adds entry-specific ones."""

    def posted(self):
        return self.filter(status="posted")

    # .recent(), .newest_first(), etc. are all available here too


# Now this works:
JournalEntry.objects.posted().recent(days=7).newest_first()
```

---

## 6. transaction.atomic() — All or Nothing

`transaction.atomic()` wraps a block of database operations in a single transaction. If anything inside the block raises an exception, every database operation inside is rolled back — nothing is persisted. If the block exits cleanly, everything commits together.

This is essential any time you touch multiple rows or multiple models that must stay consistent with each other.

```python
from django.db import transaction


# ── As a context manager ──────────────────────────────────────────────────────

def post_journal_entry(entry_id: int, approved_by) -> JournalEntry:
    with transaction.atomic():
        entry = JournalEntry.objects.get(id=entry_id)

        if entry.status != "draft":
            raise ValueError(f"Cannot post entry with status '{entry.status}'.")

        # Validate balance
        from django.db.models import Sum
        totals = entry.lines.aggregate(
            total_debit=Sum("debit"),
            total_credit=Sum("credit"),
        )
        if totals["total_debit"] != totals["total_credit"]:
            raise ValueError(
                f"Entry is unbalanced: debit={totals['total_debit']}, "
                f"credit={totals['total_credit']}"
            )
        if not entry.lines.exists():
            raise ValueError("Cannot post an entry with no lines.")

        entry.status = "posted"
        entry.approved_by = approved_by
        entry.approved_at = timezone.now()
        # save() only the fields that changed — more efficient, avoids overwriting
        # concurrent updates to other fields
        entry.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    return entry  # returned outside the block, but the transaction has committed


# ── As a decorator ────────────────────────────────────────────────────────────

@transaction.atomic
def void_journal_entry(entry_id: int, voided_by) -> JournalEntry:
    entry = JournalEntry.objects.get(id=entry_id)

    if entry.status != "posted":
        raise ValueError("Only posted entries can be voided.")
    if entry.accounting_period.is_closed:
        raise ValueError("Cannot void an entry in a closed accounting period.")

    entry.status = "voided"
    entry.save(update_fields=["status", "updated_at"])

    # Also log the void in metadata — this update is inside the same transaction
    entry.metadata["voided_by"] = voided_by.id
    entry.metadata["voided_at"] = timezone.now().isoformat()
    entry.save(update_fields=["metadata", "updated_at"])

    return entry


# ── Creating multiple related objects atomically ──────────────────────────────

def create_journal_entry_with_lines(header_data: dict, lines_data: list) -> JournalEntry:
    """
    Creates the entry and all its lines in one transaction.
    If any line fails validation, the entry is also rolled back.
    """
    with transaction.atomic():
        entry = JournalEntry.objects.create(**header_data)

        lines = [
            JournalEntryLine(journal_entry=entry, **line)
            for line in lines_data
        ]

        if not lines:
            raise ValueError("A journal entry must have at least one line.")

        JournalEntryLine.objects.bulk_create(lines)

        # Validate balance after creating lines
        from django.db.models import Sum
        totals = entry.lines.aggregate(total_debit=Sum("debit"), total_credit=Sum("credit"))
        if totals["total_debit"] != totals["total_credit"]:
            raise ValueError("Lines are unbalanced — entry not created.")

        return entry
```

**What `atomic()` does NOT do:** it does not protect against race conditions between concurrent transactions. Two transactions can both read the same row cleanly and then both write to it, overwriting each other. That requires locking — covered in the next section.

---

## 7. select_for_update() — Row-Level Locking

`select_for_update()` adds `SELECT ... FOR UPDATE` to the SQL query. This is a **pessimistic lock** — it tells the database "I'm about to modify this row, lock it so nobody else can until my transaction finishes."

It must always be used inside `transaction.atomic()`. Without an open transaction, the lock is released immediately, making it useless.

```python
from django.db import transaction


# ── Basic usage — lock a single row ──────────────────────────────────────────

with transaction.atomic():
    # Row is locked from this point until the transaction commits or rolls back
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)

    # Safe to read, check, and modify — no other transaction can touch this row
    if entry.status != "draft":
        raise ValueError("Entry is not in draft status.")

    entry.status = "posted"
    entry.save(update_fields=["status", "updated_at"])
# Lock released here — transaction committed


# ── Lock multiple rows at once ────────────────────────────────────────────────

with transaction.atomic():
    # All matching rows are locked simultaneously
    entries = list(
        JournalEntry.objects
        .select_for_update()
        .filter(company=company, status="draft", date__lt=cutoff_date)
    )
    for entry in entries:
        entry.status = "voided"

    JournalEntry.objects.bulk_update(entries, fields=["status"])


# ── Lock with related objects via select_related ──────────────────────────────
# select_for_update() + select_related() locks all tables in the JOIN by default
# Use of= to lock only specific tables

with transaction.atomic():
    entry = (
        JournalEntry.objects
        .select_related("accounting_period")
        .select_for_update(of=("self",))   # lock ONLY journal_entry, not accounting_period
        .get(id=entry_id)
    )
    # Now entry.accounting_period is loaded (via JOIN) but NOT locked
    # entry itself IS locked
    if entry.accounting_period.is_closed:
        raise ValueError("Period is closed.")
    entry.status = "posted"
    entry.save()
```

**Why `select_for_update()` matters — the race condition it prevents:**

```python
# ── WITHOUT select_for_update() — race condition ─────────────────────────────
# Two requests arrive simultaneously for the same entry

# Request A                          # Request B
entry = JE.objects.get(id=1)         entry = JE.objects.get(id=1)
# entry.status = "draft" for both

# Both pass the check:
if entry.status == "draft": ...      if entry.status == "draft": ...

# Both post — entry is posted TWICE
entry.status = "posted"              entry.status = "posted"
entry.save()                         entry.save()


# ── WITH select_for_update() — safe ──────────────────────────────────────────
# Request A locks the row first
with transaction.atomic():
    entry = JE.objects.select_for_update().get(id=1)  # A acquires lock
    # B tries to run the same line — it BLOCKS here, waiting for A's lock
    entry.status = "posted"
    entry.save()
# A commits — lock released

# B resumes — now reads status="posted"
# B's check fails — raises ValueError — correct behavior
```

---

## 8. Combining Locking and Transactions — The Full Pattern

This is the complete, production-safe pattern for any state-changing operation on a single record. It combines `transaction.atomic()`, `select_for_update()`, state validation, the actual mutation, and side effects.

```python
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum


class JournalEntryService:
    """
    Service layer that owns all state-changing operations on JournalEntry.
    Each method is self-contained: it opens its own transaction, locks what
    it needs, validates, mutates, and then commits or raises.
    """

    @staticmethod
    def post(entry_id: int, approved_by) -> "JournalEntry":
        with transaction.atomic():
            # 1. Lock the row — prevents concurrent posts
            entry = (
                JournalEntry.objects
                .select_for_update()
                .select_related("accounting_period")
                .get(id=entry_id)
            )

            # 2. Validate preconditions
            if entry.status != "draft":
                raise ValueError(
                    f"Cannot post entry #{entry.id}: status is '{entry.status}', expected 'draft'."
                )
            if entry.accounting_period.is_closed:
                raise ValueError(
                    f"Cannot post entry #{entry.id}: accounting period is closed."
                )

            # 3. Validate business rules
            totals = entry.lines.aggregate(
                total_debit=Sum("debit"),
                total_credit=Sum("credit"),
            )
            if not entry.lines.exists():
                raise ValueError(f"Entry #{entry.id} has no lines.")
            if totals["total_debit"] != totals["total_credit"]:
                raise ValueError(
                    f"Entry #{entry.id} is unbalanced: "
                    f"debit={totals['total_debit']}, credit={totals['total_credit']}."
                )

            # 4. Mutate
            entry.status = "posted"
            entry.approved_by = approved_by
            entry.approved_at = timezone.now()
            entry.total_debit = totals["total_debit"]
            entry.total_credit = totals["total_credit"]
            entry.save(update_fields=[
                "status", "approved_by", "approved_at",
                "total_debit", "total_credit", "updated_at"
            ])

            # 5. Trigger post-commit side effects (covered in section 10)
            transaction.on_commit(lambda: notify_entry_posted.delay(entry.id))

        return entry

    @staticmethod
    def void(entry_id: int, voided_by, reason: str = "") -> "JournalEntry":
        with transaction.atomic():
            entry = JournalEntry.objects.select_for_update().get(id=entry_id)

            if entry.status != "posted":
                raise ValueError(f"Only posted entries can be voided. Status: '{entry.status}'.")
            if entry.accounting_period.is_closed:
                raise ValueError("Cannot void an entry in a closed period.")

            entry.status = "voided"
            entry.metadata["void_reason"] = reason
            entry.metadata["voided_by"] = voided_by.id
            entry.metadata["voided_at"] = timezone.now().isoformat()
            entry.save(update_fields=["status", "metadata", "updated_at"])

            transaction.on_commit(lambda: notify_entry_voided.delay(entry.id))

        return entry

    @staticmethod
    def reverse(entry_id: int, reversal_date, created_by) -> "JournalEntry":
        """
        Creates a mirror-image entry that cancels out the original.
        Both the original (marking it reversed) and the new reversal entry
        must succeed or neither should.
        """
        with transaction.atomic():
            # Lock original — prevents double reversals
            original = (
                JournalEntry.objects
                .select_for_update()
                .prefetch_related("lines")
                .get(id=entry_id)
            )

            if original.status != "posted":
                raise ValueError("Only posted entries can be reversed.")
            if original.reverse_entry_id is not None:
                raise ValueError("This entry has already been reversed.")

            # Create the reversal entry
            reversal = JournalEntry.objects.create(
                company=original.company,
                accounting_period=original.accounting_period,
                date=reversal_date,
                reference=f"REV-{original.reference}",
                description=f"Reversal of {original.reference}",
                status="posted",
                created_by=created_by,
                reversal_of=original,
                total_debit=original.total_credit,   # flip debit ↔ credit
                total_credit=original.total_debit,
            )

            # Flip all lines
            reversal_lines = [
                JournalEntryLine(
                    journal_entry=reversal,
                    coa_account=line.coa_account,
                    debit=line.credit,    # flip
                    credit=line.debit,    # flip
                    cost_center=line.cost_center,
                    description=f"Reversal: {line.description}",
                )
                for line in original.lines.all()
            ]
            JournalEntryLine.objects.bulk_create(reversal_lines)

            # Mark original as having been reversed
            original.reverse_entry = reversal
            original.save(update_fields=["reverse_entry", "updated_at"])

        return reversal
```

---

## 9. nowait and skip_locked — Non-Blocking Patterns

By default, `select_for_update()` **blocks** — if another transaction holds the lock on a row, your query waits until that lock is released. This is fine for most operations, but sometimes blocking is unacceptable (async contexts, user-facing requests) or counterproductive (workers competing for a queue).

### nowait=True — Fail Immediately if Locked

```python
from django.db import transaction, DatabaseError


def try_post_entry(entry_id: int, approved_by):
    """
    Attempt to post an entry. If another request is already processing it,
    fail immediately with a clear error rather than making the user wait.
    Useful in API endpoints where a user clicks "Post" twice rapidly.
    """
    try:
        with transaction.atomic():
            entry = (
                JournalEntry.objects
                .select_for_update(nowait=True)   # raises immediately if locked
                .get(id=entry_id)
            )
            # ... validation and mutation ...
            entry.status = "posted"
            entry.save()

    except DatabaseError:
        raise ValueError(
            "This entry is currently being processed by another request. "
            "Please wait a moment and try again."
        )
```

### skip_locked=True — The Worker Queue Pattern

`skip_locked=True` tells the database: "give me rows that are not currently locked; skip any that are." This is perfect for job queues where multiple workers should each process a different item concurrently without stepping on each other.

```python
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


def process_pending_entries_worker():
    """
    Designed to run concurrently across multiple worker processes.
    Each worker picks a batch of unlocked draft entries and processes them.
    Workers never compete for the same row — skip_locked ensures this.
    """
    while True:
        with transaction.atomic():
            # Grab up to 10 entries that nobody else is currently processing
            batch = list(
                JournalEntry.objects
                .select_for_update(skip_locked=True)
                .filter(status="draft")
                .order_by("created_at")[:10]
            )

            if not batch:
                break   # No more unprocessed entries — worker is done

            for entry in batch:
                try:
                    # Heavy processing logic here
                    _validate_and_post_entry(entry)
                except Exception as e:
                    logger.error(f"Failed to process entry #{entry.id}: {e}")
                    # Mark it as failed so it doesn't keep getting picked up
                    entry.metadata["error"] = str(e)
                    entry.save(update_fields=["metadata", "updated_at"])


def _validate_and_post_entry(entry):
    """Inner logic — runs inside the same atomic block as the lock."""
    from django.db.models import Sum
    totals = entry.lines.aggregate(total_debit=Sum("debit"), total_credit=Sum("credit"))
    if totals["total_debit"] == totals["total_credit"]:
        entry.status = "posted"
        entry.save(update_fields=["status", "updated_at"])


# Multiple workers running simultaneously — no conflicts:
# Worker A grabs entries [1, 2, 3]  (locks them)
# Worker B grabs entries [4, 5, 6]  (skips 1,2,3 — locked; takes next available)
# Worker C grabs entries [7, 8, 9]  (same)
```

### Combining nowait and of= — Fine-Grained Lock Control

```python
with transaction.atomic():
    # Lock only the journal_entry row, not the company row from the JOIN
    # Fail immediately if the entry is locked (another request is processing it)
    entry = (
        JournalEntry.objects
        .select_related("company", "accounting_period")
        .select_for_update(nowait=True, of=("self",))
        .get(id=entry_id)
    )
```

---

## 10. transaction.on_commit() — Safe Side Effects

Side effects like sending emails, firing Celery tasks, or hitting webhooks should **never** run inside a `transaction.atomic()` block. If the transaction later rolls back, the side effect has already happened and cannot be undone.

`transaction.on_commit()` registers a callback that runs **only if and after** the transaction successfully commits to the database.

```python
from django.db import transaction


def post_entry_with_notifications(entry_id: int, approved_by):
    with transaction.atomic():
        entry = JournalEntry.objects.select_for_update().get(id=entry_id)
        entry.status = "posted"
        entry.save()

        # ❌ WRONG — runs even if the transaction rolls back after this line
        # send_posting_email(entry)

        # ❌ WRONG — Celery task fires even if transaction rolls back
        # notify_accounting_team.delay(entry.id)

        # ✅ CORRECT — only runs after the transaction commits successfully
        transaction.on_commit(lambda: notify_accounting_team.delay(entry.id))
        transaction.on_commit(lambda: sync_to_erp.delay(entry.id))
        transaction.on_commit(lambda: send_posting_email(entry.id))

    # At this point the transaction has committed and all on_commit hooks have fired


# ── on_commit in tests ────────────────────────────────────────────────────────
# In tests, Django wraps each test in a transaction that is rolled back
# at the end. on_commit hooks NEVER fire in this case.
# Use TestCase (not TransactionTestCase) to be aware of this.

# To test on_commit behavior, use:
from django.test import TransactionTestCase

class PostEntryTest(TransactionTestCase):
    def test_notification_fired_on_post(self):
        # on_commit hooks DO fire in TransactionTestCase
        ...

# Or capture them with:
from django.test.utils import CaptureQueriesContext
# Or mock transaction.on_commit to call the function immediately:
with mock.patch("django.db.transaction.on_commit", side_effect=lambda fn: fn()):
    post_entry_with_notifications(entry.id, user)
```

---

## 11. Savepoints — Partial Rollbacks

When you nest `transaction.atomic()` blocks, the inner block creates a **savepoint** rather than a new transaction. If the inner block raises, only the operations inside it are rolled back — the outer transaction can continue and commit.

This is useful when you have optional or non-critical steps that should not abort the main operation if they fail.

```python
from django.db import transaction


def create_entry_and_notify(header_data: dict, lines_data: list) -> JournalEntry:
    """
    The entry and lines MUST succeed together.
    The notification is optional — if it fails, the entry should still be created.
    """
    with transaction.atomic():   # outer transaction
        # Critical path — if this fails, everything rolls back
        entry = JournalEntry.objects.create(**header_data)
        lines = [JournalEntryLine(journal_entry=entry, **ld) for ld in lines_data]
        JournalEntryLine.objects.bulk_create(lines)

        # Optional path — wrapped in its own savepoint
        try:
            with transaction.atomic():   # savepoint
                # If this raises, only the savepoint is rolled back
                # The outer transaction (entry + lines) is preserved
                AuditLog.objects.create(
                    action="entry_created",
                    entry=entry,
                    user=header_data["created_by"],
                )
        except Exception as e:
            # Savepoint rolled back — audit log not created
            # But entry and lines ARE still committed with the outer transaction
            logger.warning(f"Audit log failed for entry {entry.id}: {e}")

        return entry


# ── Savepoints and database integrity ────────────────────────────────────────
# Even within a savepoint, database errors (like unique constraint violations)
# put PostgreSQL into an aborted state — you MUST handle them in a try/except
# around the inner atomic() block, not outside it.

# WRONG:
with transaction.atomic():
    try:
        inner_thing()            # raises IntegrityError
    except IntegrityError:
        pass                     # transaction is now aborted — any further DB op fails

# CORRECT:
with transaction.atomic():
    try:
        with transaction.atomic():   # savepoint isolates the error
            inner_thing()
    except IntegrityError:
        pass                     # savepoint rolled back, outer transaction still healthy
    # Further DB operations here work fine
    outer_thing()
```

---

## 12. Common Concurrency Pitfalls and How to Fix Them

### Pitfall 1: Read-Modify-Write Without a Lock

```python
# ❌ WRONG — classic race condition
entry = JournalEntry.objects.get(id=entry_id)
entry.total_debit += new_line.debit    # read-modify-write
entry.save()

# ✅ CORRECT option A — use F() for atomic DB-level increment
from django.db.models import F
JournalEntry.objects.filter(id=entry_id).update(
    total_debit=F("total_debit") + new_line.debit
)

# ✅ CORRECT option B — lock then modify (needed when you also need to validate)
with transaction.atomic():
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)
    if entry.status != "draft":
        raise ValueError("Cannot add lines to a non-draft entry.")
    entry.total_debit += new_line.debit
    entry.save(update_fields=["total_debit", "updated_at"])
```

### Pitfall 2: Locking Outside a Transaction

```python
# ❌ WRONG — lock is released immediately, provides zero protection
entry = JournalEntry.objects.select_for_update().get(id=entry_id)
# transaction ended at end of that line — lock gone
entry.status = "posted"
entry.save()   # completely unprotected

# ✅ CORRECT — lock lives for the duration of the transaction
with transaction.atomic():
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)
    entry.status = "posted"
    entry.save()
```

### Pitfall 3: Side Effects Inside a Transaction

```python
# ❌ WRONG — email fires even if the transaction rolls back after this line
with transaction.atomic():
    entry.status = "posted"
    entry.save()
    send_email(entry)   # can't be undone if something below raises

# ✅ CORRECT — email only fires after successful commit
with transaction.atomic():
    entry.status = "posted"
    entry.save()
    transaction.on_commit(lambda: send_email.delay(entry.id))
```

### Pitfall 4: Using .update() When You Need Validation

```python
# ❌ WRONG — .update() bypasses model logic, signals, and your validation
JournalEntry.objects.filter(id=entry_id).update(status="posted")

# ✅ CORRECT — fetch, validate, then save
with transaction.atomic():
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)
    if entry.status != "draft":
        raise ValueError("...")
    entry.status = "posted"
    entry.save(update_fields=["status", "updated_at"])

# NOTE: .update() IS appropriate for bulk operations where you've already
# done validation and don't need per-row logic:
JournalEntry.objects.filter(
    status="draft",
    accounting_period__is_closed=True
).update(metadata=F("metadata"))   # legitimate bulk update
```

### Pitfall 5: Deadlocks from Inconsistent Lock Ordering

```python
# ❌ DANGEROUS — if two requests run simultaneously, they can deadlock:
# Request A: locks entry 1, then tries to lock entry 2
# Request B: locks entry 2, then tries to lock entry 1
# Both block forever

def transfer(from_id, to_id):
    with transaction.atomic():
        from_entry = JournalEntry.objects.select_for_update().get(id=from_id)
        to_entry = JournalEntry.objects.select_for_update().get(id=to_id)
        ...

# ✅ CORRECT — always lock in a consistent order (e.g., by ascending ID)
def transfer(from_id, to_id):
    ids = sorted([from_id, to_id])   # always same order regardless of input
    with transaction.atomic():
        entries = dict(
            JournalEntry.objects
            .select_for_update()
            .filter(id__in=ids)
            .in_bulk()
        )
        from_entry = entries[from_id]
        to_entry = entries[to_id]
        ...
```

### Pitfall 6: Holding Locks Too Long

```python
# ❌ WRONG — lock is held for the entire duration of the HTTP request or slow operation
with transaction.atomic():
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)
    time.sleep(5)          # simulating a slow API call — lock held for 5+ seconds
    result = call_external_api(entry)
    entry.metadata = result
    entry.save()

# ✅ CORRECT — do slow work OUTSIDE the lock, then lock briefly to commit
result = call_external_api(entry_id)   # slow work without holding any lock

with transaction.atomic():            # lock only for the brief write
    entry = JournalEntry.objects.select_for_update().get(id=entry_id)
    entry.metadata = result
    entry.save(update_fields=["metadata", "updated_at"])
```

---

## 13. Manager Patterns for Finite State Machines

Journal entries follow a state machine: `draft → posted → voided`. Encoding valid transitions into the manager makes invalid state changes impossible to accidentally trigger.

```python
from django.db import transaction
from django.utils import timezone


class JournalEntryStateMachine:
    """
    All valid state transitions for JournalEntry.
    Each method enforces its preconditions and performs the transition atomically.
    """

    VALID_TRANSITIONS = {
        "draft": ["posted"],
        "posted": ["voided"],
        "voided": [],   # terminal state
    }

    @staticmethod
    def can_transition(current_status: str, target_status: str) -> bool:
        return target_status in JournalEntryStateMachine.VALID_TRANSITIONS.get(current_status, [])

    @staticmethod
    def transition(entry_id: int, target_status: str, by_user, **extra_fields) -> "JournalEntry":
        with transaction.atomic():
            entry = JournalEntry.objects.select_for_update().get(id=entry_id)

            if not JournalEntryStateMachine.can_transition(entry.status, target_status):
                raise ValueError(
                    f"Invalid transition: '{entry.status}' → '{target_status}'. "
                    f"Allowed: {JournalEntryStateMachine.VALID_TRANSITIONS.get(entry.status, [])}"
                )

            entry.status = target_status
            for field, value in extra_fields.items():
                setattr(entry, field, value)

            update_fields = ["status", "updated_at"] + list(extra_fields.keys())
            entry.save(update_fields=update_fields)

            entry.metadata.setdefault("transitions", []).append({
                "from": entry.status,
                "to": target_status,
                "by": by_user.id,
                "at": timezone.now().isoformat(),
            })
            entry.save(update_fields=["metadata", "updated_at"])

        return entry


# Usage — clean, explicit, impossible to make invalid transitions by accident
JournalEntryStateMachine.transition(
    entry_id=1,
    target_status="posted",
    by_user=request.user,
    approved_by=request.user,
    approved_at=timezone.now(),
)
```

You can also encode this directly on the QuerySet for bulk state transitions:

```python
class JournalEntryQuerySet(models.QuerySet):

    def bulk_post(self, approved_by):
        """
        Post all draft entries in the queryset atomically.
        Only entries that are balanced and have lines are posted.
        Returns the count of successfully posted entries.
        """
        from django.db.models import Sum, Count
        with transaction.atomic():
            # Find which entries in this queryset are actually postable
            postable_ids = (
                self.filter(status="draft")
                .annotate(
                    total_debit=Sum("lines__debit"),
                    total_credit=Sum("lines__credit"),
                    line_count=Count("lines"),
                )
                .filter(
                    line_count__gt=0,
                    total_debit=models.F("total_credit"),
                )
                .values_list("id", flat=True)
            )

            count = JournalEntry.objects.filter(id__in=postable_ids).update(
                status="posted",
                approved_by=approved_by,
                approved_at=timezone.now(),
            )
        return count
```

---

## 14. Testing Managers and Transactions

Testing custom managers and transactional behavior requires understanding how Django's test infrastructure handles transactions.

```python
from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError
from unittest import mock


class JournalEntryQuerySetTest(TestCase):
    """
    TestCase wraps each test in a transaction that is rolled back.
    Fast, but on_commit hooks NEVER fire here.
    Use for testing QuerySet methods, filtering, annotations.
    """

    def setUp(self):
        self.company = Company.objects.create(name="Test Co", tax_id="123")
        self.user = User.objects.create_user(username="test")
        self.period = AccountingPeriod.objects.create(
            company=self.company,
            name="Jan 2024",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

    def test_posted_filter(self):
        draft = JournalEntry.objects.create(
            company=self.company, accounting_period=self.period,
            date="2024-01-15", created_by=self.user, status="draft"
        )
        posted = JournalEntry.objects.create(
            company=self.company, accounting_period=self.period,
            date="2024-01-15", created_by=self.user, status="posted"
        )

        result = JournalEntry.objects.posted()
        self.assertIn(posted, result)
        self.assertNotIn(draft, result)

    def test_chainability(self):
        """QuerySet methods must remain chainable."""
        qs = (
            JournalEntry.objects
            .for_company(self.company)
            .posted()
            .in_year(2024)
        )
        # Should not raise — just builds a lazy queryset
        self.assertIsInstance(qs, models.QuerySet)

    def test_create_draft_validates_period_company(self):
        other_company = Company.objects.create(name="Other", tax_id="456")
        other_period = AccountingPeriod.objects.create(
            company=other_company,
            name="Jan 2024",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        with self.assertRaises(ValueError):
            JournalEntry.objects.create_draft(
                company=self.company,
                accounting_period=other_period,   # wrong company's period
                date="2024-01-15",
                created_by=self.user,
            )

    def test_query_count_with_lines(self):
        """Ensure with_lines() eliminates N+1."""
        for _ in range(5):
            JournalEntry.objects.create(
                company=self.company, accounting_period=self.period,
                date="2024-01-15", created_by=self.user, status="posted"
            )

        with self.assertNumQueries(2):   # 1 for entries, 1 for lines prefetch
            entries = list(JournalEntry.objects.posted().with_lines())
            for entry in entries:
                _ = list(entry.lines.all())   # no extra queries — already prefetched


class JournalEntryTransactionTest(TransactionTestCase):
    """
    TransactionTestCase does NOT wrap tests in a transaction.
    Use when testing on_commit hooks, select_for_update, or atomic behavior.
    Slower — database is truncated between tests.
    """

    def test_on_commit_fires_after_post(self):
        company = Company.objects.create(name="Test Co", tax_id="123")
        # ... setup ...

        fired = []
        with mock.patch("myapp.tasks.notify_accounting_team.delay", side_effect=lambda id: fired.append(id)):
            JournalEntryService.post(entry_id=entry.id, approved_by=user)

        self.assertIn(entry.id, fired)

    def test_on_commit_does_not_fire_on_rollback(self):
        fired = []
        with mock.patch("myapp.tasks.notify_accounting_team.delay", side_effect=lambda id: fired.append(id)):
            try:
                with transaction.atomic():
                    JournalEntryService.post(entry_id=entry.id, approved_by=user)
                    raise Exception("Force rollback")
            except Exception:
                pass

        self.assertEqual(fired, [])   # on_commit should NOT have fired

    def test_select_for_update_prevents_double_post(self):
        """
        Simulate concurrent requests by using threads.
        Only one should succeed — the other should get a ValueError.
        """
        import threading

        results = []

        def try_post():
            try:
                JournalEntryService.post(entry_id=self.entry.id, approved_by=self.user)
                results.append("success")
            except ValueError as e:
                results.append(f"error: {e}")

        threads = [threading.Thread(target=try_post) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if r == "success"]
        self.assertEqual(len(successes), 1)   # exactly one should succeed
```

---

## 15. Quick Reference Cheat Sheet

| Situation | Tool | Notes |
|---|---|---|
| All query logic for a model | Custom `QuerySet` | Every method returns `self.something()` |
| Entry point / factory methods | Custom `Manager` | `get_queryset()` returns your QuerySet |
| Available on Manager and mid-chain | Proxy QuerySet methods on Manager | Chainable from anywhere |
| Filter a subset by default | Second manager on the model | Be careful with related lookups |
| Shared methods across all models | QuerySet on abstract base model | Children inherit it |
| Multi-row/multi-model consistency | `transaction.atomic()` | Decorator or context manager |
| State-change without race conditions | `select_for_update()` inside `atomic()` | Locks the row for the transaction |
| Fail immediately if row is locked | `select_for_update(nowait=True)` | Raises `DatabaseError` |
| Worker queue — skip busy rows | `select_for_update(skip_locked=True)` | Multiple workers, no conflict |
| Lock only specific tables in a JOIN | `select_for_update(of=("self",))` | Prevents locking joined rows |
| Atomic increment without Python | `F("field") + value` in `.update()` | No read-modify-write race |
| Emails / Celery tasks after commit | `transaction.on_commit(fn)` | Only fires if transaction commits |
| Optional step that can fail | Nested `transaction.atomic()` (savepoint) | Inner rollback, outer proceeds |
| Consistent lock ordering | Sort IDs before locking | Prevents deadlocks |
| Keep locks brief | Do slow work outside the transaction | Lock only for the actual write |
| State machine transitions | Enforce in manager or service layer | Invalid transitions raise immediately |
| Test QuerySet methods | `TestCase` + `assertNumQueries` | Fast — wrapped in rollback |
| Test on_commit hooks | `TransactionTestCase` | Slower — real commits |
| Test concurrent behavior | `TransactionTestCase` + threads | Verifies lock behavior end-to-end |
| Factory creation with rules | Manager factory method (`create_draft`) | Centralizes precondition checks |

---

*The core principle running through all of this: **put query logic on the QuerySet, put the database transaction boundary as close to the mutation as possible, lock what you read before you write it, and never run side effects inside a transaction.** Follow these four rules and 95% of Django concurrency bugs become impossible by construction.*
