# Django i18n Automated Translation Guide

A comprehensive guide to automating the translation of Django `.po` files using Python libraries and machine translation APIs.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Why Automate Translation?](#why-automate)
3. [Required Libraries](#libraries)
4. [Approach 1: Polib with Google Translate](#approach-1)
5. [Approach 2: Batch Translation](#approach-2)
6. [Approach 3: DeepL API (Higher Quality)](#approach-3)
7. [CI/CD Integration](#cicd)
8. [Quality Assurance](#qa)
9. [Post-Translation Workflow](#workflow)
10. [Comparison of Approaches](#comparison)
11. [Best Practices](#best-practices)
12. [Common Issues](#issues)
13. [Quick Reference](#quick-reference)

---

## Introduction {#introduction}

This guide covers automated translation of Django `.po` files using Python. While manual translation ensures the highest quality, automation significantly accelerates the process—especially for large projects with hundreds or thousands of strings.

> **Important:** Automated translation should be considered a **starting point**, not the final product. Always have human translators review and refine the output for production applications.

---

## Why Automate Translation? {#why-automate}

| Benefit | Description |
|---------|-------------|
| **Speed** | Generate base translations in minutes instead of weeks |
| **Cost Reduction** | Professional translators focus on refining, not starting from scratch |
| **Rapid Prototyping** | Quickly see how your app looks in different languages |
| **Multi-Language Support** | Easily add new languages without manual effort |
| **Consistency** | Maintain consistent terminology across languages |

---

## Required Libraries {#libraries}

Install the necessary dependencies:

```bash
# Core library for parsing/editing .po files
pip install polib==1.2.0

# Machine translation (Google Translate)
pip install deep-translator==1.11.4

# Optional: Higher quality translation
pip install deepl
```

---

## Approach 1: Polib with Google Translate {#approach-1}

This is the recommended approach for most projects—free, fast, and reliable.

### Complete Translation Script

```python
# scripts/translate_po.py
#!/usr/bin/env python3
"""
Automated .po file translation script.

Usage:
    python scripts/translate_po.py --language ar --file locale/ar/LC_MESSAGES/django.po
"""

import argparse
import polib
from deep_translator import GoogleTranslator
import time
import sys


class POTranslator:
    """Handles automated translation of .po files."""
    
    def __init__(self, source_lang='en', target_lang='ar'):
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        self.source_lang = source_lang
        self.target_lang = target_lang
    
    def should_translate(self, msgid):
        """
        Determine if a string should be translated.
        
        Returns False for:
        - Empty strings
        - Format strings (containing %s, %(variable)s)
        - Already translated strings
        - Special characters only
        """
        if not msgid or not msgid.strip():
            return False
        
        # Skip format strings
        if '%(' in msgid or '%s' in msgid or '%d' in msgid:
            return False
        
        # Skip strings that are just special characters
        if all(c in msgid for c in ['—', '…', ':', '.', ',', '?']):
            return False
        
        # Skip very short strings that might be format codes
        if len(msgid.strip()) < 2 and not msgid.isalpha():
            return False
        
        return True
    
    def translate(self, text):
        """Translate a single string."""
        if not text:
            return text
        
        try:
            result = self.translator.translate(text)
            if result and result != text:
                return result
            return text
        except Exception as e:
            print(f"Error translating: {text[:30]}... - {e}", file=sys.stderr)
            return text
    
    def translate_po_file(self, input_file, output_file=None, batch_size=50):
        """
        Translate all untranslated entries in a .po file.
        
        Args:
            input_file: Path to input .po file
            output_file: Path for output (defaults to input)
            batch_size: Number of entries to process before saving progress
        
        Returns:
            dict with statistics
        """
        if output_file is None:
            output_file = input_file
        
        # Load the PO file
        po = polib.pofile(input_file)
        print(f"Loaded {len(po)} entries")
        
        # Find entries that need translation
        entries_to_translate = []
        for i, entry in enumerate(po):
            if entry.msgid and not entry.msgstr and self.should_translate(entry.msgid):
                entries_to_translate.append((i, entry.msgid))
        
        print(f"Entries to translate: {len(entries_to_translate)}")
        
        # Translate in batches
        total = len(entries_to_translate)
        
        for batch_num in range(0, total, batch_size):
            batch = entries_to_translate[batch_num:batch_num + batch_size]
            
            for entry_idx, msgid in batch:
                translated = self.translate(msgid)
                po[entry_idx].msgstr = translated
                time.sleep(0.05)  # Rate limiting
            
            # Save progress
            po.save(output_file)
            progress = min(batch_num + batch_size, total)
            percent = 100 * progress // total
            print(f"Progress: {progress}/{total} ({percent}%)")
            sys.stdout.flush()
        
        # Update header
        po.metadata['Last-Translator'] = 'Automated Translation'
        po.metadata['Language'] = self.target_lang
        po.save(output_file)
        
        return {
            'total_entries': len(po),
            'translated': total,
            'skipped': len(po) - total
        }


def main():
    parser = argparse.ArgumentParser(description='Translate Django .po files')
    parser.add_argument('--language', '-l', required=True, help='Target language code (e.g., ar, es, fr)')
    parser.add_argument('--file', '-f', required=True, help='Path to .po file')
    parser.add_argument('--source', '-s', default='en', help='Source language code')
    parser.add_argument('--batch-size', '-b', type=int, default=50, help='Batch size')
    
    args = parser.parse_args()
    
    translator = POTranslator(source_lang=args.source, target_lang=args.language)
    stats = translator.translate_po_file(args.file, batch_size=args.batch_size)
    
    print(f"\nTranslation complete!")
    print(f"Translated: {stats['translated']}")
    print(f"Skipped: {stats['skipped']}")


if __name__ == '__main__':
    main()
```

### Usage

```bash
# Translate to Arabic
python scripts/translate_po.py --language ar --file locale/ar/LC_MESSAGES/django.po

# Translate to Spanish
python scripts/translate_po.py --language es --file locale/es/LC_MESSAGES/django.po

# Custom batch size
python scripts/translate_po.py --language ar --file locale/ar/LC_MESSAGES/django.po --batch-size 100
```

### Features

- **Automatic filtering** of format strings (`%(variable)s`, `%s`)
- **Batch processing** with progress saving
- **Rate limiting** to avoid API blocks
- **Header metadata** updates automatically

---

## Approach 2: Batch Translation {#approach-2}

Translate to multiple languages in a single run.

```python
# scripts/batch_translate.py
#!/usr/bin/env python3
"""
Translate .po file to multiple languages in one run.
"""

import polib
from deep_translator import GoogleTranslator
import time
import os


def translate_to_multiple_languages(pot_file, locale_dir, languages):
    """
    Translate a .pot template to multiple languages.
    
    Args:
        pot_file: Path to the template .pot file
        locale_dir: Path to locale directory (e.g., 'locale')
        languages: List of language codes (e.g., ['ar', 'es', 'fr'])
    """
    # Load template
    pot = polib.pofile(pot_file)
    
    # Extract translatable strings
    translatable = [entry.msgid for entry in pot if entry.msgid and '%' not in entry.msgid]
    print(f"Found {len(translatable)} translatable strings")
    
    for lang_code in languages:
        print(f"\n--- Translating to {lang_code} ---")
        
        translator = GoogleTranslator(source='en', target=lang_code)
        
        # Create or load existing .po file
        po_file = os.path.join(locale_dir, lang_code, 'LC_MESSAGES', 'django.po')
        
        if os.path.exists(po_file):
            po = polib.pofile(po_file)
            # Clear existing translations for fresh start
            for entry in po:
                if entry.msgstr:
                    entry.msgstr = ''
        else:
            # Create from template
            po = pot.copy()
            po.metadata['Language'] = lang_code
        
        # Translate each entry
        translated_count = 0
        for entry in po:
            if entry.msgid and not entry.msgstr and '%(' not in entry.msgid:
                try:
                    entry.msgstr = translator.translate(entry.msgid)
                    translated_count += 1
                    time.sleep(0.05)
                    
                    if translated_count % 50 == 0:
                        print(f"  Progress: {translated_count}")
                except Exception as e:
                    print(f"  Error translating: {entry.msgid[:30]}...")
        
        # Save
        os.makedirs(os.path.dirname(po_file), exist_ok=True)
        po.save(po_file)
        print(f"  Saved {po_file} ({translated_count} translated)")


if __name__ == '__main__':
    translate_to_multiple_languages(
        pot_file='locale/django.pot',
        locale_dir='locale',
        languages=['ar', 'es', 'fr', 'de', 'ja', 'zh-hans']
    )
```

### Usage

```bash
python scripts/batch_translate.py
```

This will create/update translations for Arabic, Spanish, French, German, Japanese, and Chinese all at once.

---

## Approach 3: DeepL API (Higher Quality) {#approach-3}

For better quality translations, use DeepL instead of Google Translate.

```python
# scripts/translate_deepl.py
#!/usr/bin/env python3
"""
Translation using DeepL API (higher quality output).
Requires: pip install deepl
"""

import polib
import deepl
import os


class DeepLTranslator:
    """High-quality translation using DeepL API."""
    
    def __init__(self, api_key, target_lang='AR'):
        self.translator = deepl.Translator(api_key)
        # DeepL language codes are different
        self.lang_map = {
            'ar': 'AR', 'es': 'ES', 'fr': 'FR', 'de': 'DE',
            'ja': 'JA', 'zh-hans': 'ZH', 'pt-br': 'PT-BR',
            'it': 'IT', 'ru': 'RU', 'nl': 'NL'
        }
        self.target_lang = self.lang_map.get(target_lang, target_lang.upper())
    
    def should_translate(self, msgid):
        if not msgid or '%(' in msgid:
            return False
        return True
    
    def translate_po_file(self, input_file, output_file=None):
        """Translate using DeepL."""
        if output_file is None:
            output_file = input_file
        
        po = polib.pofile(input_file)
        print(f"Loaded {len(po)} entries")
        
        translated = 0
        for entry in po:
            if entry.msgid and not entry.msgstr and self.should_translate(entry.msgid):
                try:
                    result = self.translator.translate_text(entry.msgid, target_lang=self.target_lang)
                    entry.msgstr = str(result)
                    translated += 1
                    
                    if translated % 25 == 0:
                        print(f"Translated {translated}...")
                        po.save(output_file)  # Save progress
                        
                except Exception as e:
                    print(f"Error: {e}")
        
        po.save(output_file)
        print(f"Done! Translated {translated} entries")
        return translated


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Translate with DeepL')
    parser.add_argument('--key', required=True, help='DeepL API key')
    parser.add_argument('--language', '-l', required=True, help='Target language')
    parser.add_argument('--file', '-f', required=True, help='.po file path')
    
    args = parser.parse_args()
    
    translator = DeepLTranslator(args.key, target_lang=args.language)
    translator.translate_po_file(args.file)
```

### Usage

```bash
# Get your free API key from https://www.deepl.com/pro-api
python scripts/translate_deepl.py --key YOUR_API_KEY --language ar --file locale/ar/LC_MESSAGES/django.po
```

> **Note:** DeepL offers a free tier with 500,000 characters/month.

---

## CI/CD Integration {#cicd}

Automate translation as part of your deployment pipeline.

```yaml
# .github/workflows/translate.yml
name: Auto Translate

on:
  schedule:
    # Run weekly
    - cron: '0 0 * * 0'
  workflow_dispatch:
    inputs:
      language:
        description: 'Target language'
        required: true
        default: 'ar'

jobs:
  translate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install polib deep-translator
      
      - name: Run translation
        run: |
          python scripts/translate_po.py --language ${{ github.event.inputs.language }} --file locale/${{ github.event.inputs.language }}/LC_MESSAGES/django.po
      
      - name: Compile messages
        run: python manage.py compilemessages
      
      - name: Commit changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "chore: Translate .po files to ${{ github.event.inputs.language }}"
```

---

## Quality Assurance {#qa}

After running automated translation, validate the results.

```python
# scripts/validate_translations.py
#!/usr/bin/env python3
"""Validate translated .po files."""

import polib
import sys


def validate_po_file(file_path):
    """Run various validation checks on translated .po file."""
    po = polib.pofile(file_path)
    
    issues = {
        'empty_translations': [],
        'same_as_original': [],
        'contains_english': [],
        'format_string_issues': []
    }
    
    for entry in po:
        if not entry.msgid:
            continue
            
        # Check for empty translations
        if not entry.msgstr:
            issues['empty_translations'].append(entry.msgid)
            continue
        
        # Check if translation is same as original
        if entry.msgstr.strip() == entry.msgid.strip():
            issues['same_as_original'].append(entry.msgid)
        
        # Check for English in Arabic translation (simple check)
        if any(c.isascii() and c.isalpha() for c in entry.msgstr):
            issues['contains_english'].append((entry.msgid, entry.msgstr))
    
    # Print report
    print(f"\nValidation Report for {file_path}")
    print("=" * 50)
    
    for issue_type, examples in issues.items():
        if examples:
            print(f"\n{issue_type.replace('_', ' ').title()}: {len(examples)}")
            for example in examples[:5]:  # Show first 5
                if isinstance(example, tuple):
                    print(f"  - {example[0][:40]} -> {example[1][:40]}")
                else:
                    print(f"  - {example[:40]}")
    
    return issues


if __name__ == '__main__':
    import os
    locale_dir = 'locale'
    
    for lang in os.listdir(locale_dir):
        po_file = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.po')
        if os.path.exists(po_file):
            validate_po_file(po_file)
```

### Run Validation

```bash
python scripts/validate_translations.py
```

---

## Post-Translation Workflow {#workflow}

After automated translation, always follow this workflow:

```bash
# 1. Review and edit translations
# Use Poedit, Weblate, or any .po editor

# 2. Compile messages (required for Django)
python manage.py compilemessages

# 3. Test in the target language
LANGUAGE_CODE=ar python manage.py runserver

# 4. Run Django's translation check
python manage.py makemessages --check-changes

# 5. Check for missing translations
python manage.py makemessages --check
```

---

## Comparison of Approaches {#comparison}

| Approach | Quality | Speed | Cost | Best For |
|----------|---------|-------|------|----------|
| Google Translate (deep-translator) | Medium | Fast | Free | Initial translation, many languages |
| DeepL API | High | Medium | Free tier available | Production apps, important strings |
| Human translator | Highest | Slow | $$ | Final review, critical content |
| Weblate + Machine | High | Medium | Free/SaaS | Ongoing translation management |

---

## Best Practices {#best-practices}

```python
# 1. ALWAYS use a separate translator instance for each target language
# Bad:
translator = GoogleTranslator(source='en', target='ar')
# Good: Create new instance for each language

# 2. Implement proper error handling
def translate_safe(text, translator):
    try:
        return translator.translate(text)
    except Exception:
        return text  # Return original on failure

# 3. Skip strings that will break the app
SKIP_PATTERNS = [
    '%(field)s',      # Django format strings
    '%s', '%d', '%r', # Python format strings
    '{', '}',         # Might be template syntax
]

def should_skip(msgid):
    return any(pattern in msgid for pattern in SKIP_PATTERNS)

# 4. Save progress frequently (API failures can happen mid-process)
# Use batch processing with saves after each batch

# 5. Update header metadata after translation
po.metadata['Last-Translator'] = 'Automated Translation'
po.metadata['Language'] = 'ar'
po.metadata['PO-Revision-Date'] = '2024-01-15 10:00+0000'

# 6. Always filter format strings
def should_translate(msgid):
    if not msgid:
        return False
    if '%(' in msgid:  # Django format strings
        return False
    if '%s' in msgid or '%d' in msgid:  # Python format
        return False
    return True
```

---

## Common Issues {#issues}

| Issue | Cause | Solution |
|-------|-------|----------|
| Translation halts mid-process | API rate limit | Add delays between requests, save progress frequently |
| Format strings translated | Not properly filtered | Update `should_translate()` to skip strings with `%` |
| Special characters missing | Character encoding | Ensure UTF-8 in file header and save with encoding='utf-8' |
| Same string different translations | Context lost | Use `pgettext` in code, group related strings |
| Arabic text appears right-to-left | Normal in Arabic | This is correct - Arabic is RTL |
| API timeout errors | Network issues | Add retry logic with exponential backoff |
| Empty translations | Skipped entries | Check `should_translate()` logic |

---

## Quick Reference {#quick-reference}

### Commands

```bash
# Extract strings
python manage.py makemessages -a

# Translate (using our script)
python scripts/translate_po.py --language ar --file locale/ar/LC_MESSAGES/django.po

# Compile for Django
python manage.py compilemessages

# Check for issues
python manage.py makemessages --check-changes

# Validate translations
python scripts/validate_translations.py
```

### Key Libraries

| Library | Purpose | Install |
|---------|---------|---------|
| polib | Parse/edit .po files | `pip install polib` |
| deep-translator | Google Translate API | `pip install deep-translator` |
| deepl | DeepL API (higher quality) | `pip install deepl` |

### Key Functions

```python
polib.pofile()     # Load .po file
entry.msgid        # Original string
entry.msgstr       # Translated string
po.save()          # Save changes
po.metadata        # Access header info
```

### Language Codes

| Language | Code |
|----------|------|
| Arabic | ar |
| Spanish | es |
| French | fr |
| German | de |
| Japanese | ja |
| Chinese (Simplified) | zh-hans |
| Portuguese (Brazil) | pt-br |
| Italian | it |
| Russian | ru |
| Dutch | nl |

---

## Checklist Before Automated Translation

- [ ] Run `python manage.py makemessages -a` to extract all strings
- [ ] Review your .pot template for completeness
- [ ] Test translation script on a small subset first
- [ ] Plan for human review of critical strings (error messages, UI labels)
- [ ] Set up a process to update translations when strings change
- [ ] Document which strings were auto-translated vs. human-reviewed

---

## Related Resources

- [Django i18n Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [Polib Documentation](https://polib.readthedocs.io/)
- [DeepL API Documentation](https://www.deepl.com/docs-api)
- [Poedit Editor](https://poedit.net/)
- [Weblate Translation Platform](https://weblate.org/)

---

**Last Updated:** 2026
