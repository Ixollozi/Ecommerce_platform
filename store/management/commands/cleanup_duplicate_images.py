import hashlib
import os
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from store.models import Product, ProductImage
from store.media_urls import _file_fingerprint


class Command(BaseCommand):
    help = "Find and remove duplicate ProductImage records and files for products across sites."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )
        parser.add_argument(
            "--site",
            type=str,
            default="",
            help="Specific site slug to clean up (default: all sites in platform mode).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        site_filter = options["site"]

        if getattr(settings, "PLATFORM_MODE", False):
            from store.platform.registry import iter_sites, get_site
            from store.platform.context import site_context

            if site_filter:
                site = get_site(site_filter)
                if not site:
                    self.stderr.write(f"Site '{site_filter}' not found.")
                    return
                sites = [site]
            else:
                sites = list(iter_sites())

            total_deleted = 0
            for site in sites:
                self.stdout.write(f"\nScanning site: {site.slug} ({site.theme})")
                with site_context(site):
                    del_count = self._cleanup_site(dry_run)
                    total_deleted += del_count

            prefix = "[DRY-RUN] Would delete" if dry_run else "Successfully deleted"
            self.stdout.write(self.style.SUCCESS(f"\n{prefix} {total_deleted} duplicate ProductImage records across {len(sites)} sites."))
        else:
            del_count = self._cleanup_site(dry_run)
            prefix = "[DRY-RUN] Would delete" if dry_run else "Successfully deleted"
            self.stdout.write(self.style.SUCCESS(f"\n{prefix} {del_count} duplicate ProductImage records."))

    def _cleanup_site(self, dry_run: bool) -> int:
        deleted = 0
        products = Product.objects.all()

        for product in products:
            seen_fingerprints: set[str] = set()

            # Primary image fingerprint
            primary_fp = _file_fingerprint(product.image)
            if primary_fp:
                seen_fingerprints.add(primary_fp)

            # Check extra images
            extra_images = list(product.images.all().order_by("id"))
            for extra in extra_images:
                fp = _file_fingerprint(extra.image)
                is_duplicate = False

                if fp and fp in seen_fingerprints:
                    is_duplicate = True
                elif not fp:
                    # If file doesn't exist, check by filename
                    name = getattr(extra.image, "name", "")
                    prim_name = getattr(product.image, "name", "")
                    if name and prim_name and name == prim_name:
                        is_duplicate = True

                if is_duplicate:
                    deleted += 1
                    file_name = getattr(extra.image, "name", "")
                    self.stdout.write(
                        f"  -> Duplicate in Prod #{product.id} '{product.name}': "
                        f"Image #{extra.id} '{file_name}' (matches primary: {fp == primary_fp})"
                    )
                    if not dry_run:
                        # Optionally remove file from storage if different from primary
                        if hasattr(extra.image, "storage") and file_name and file_name != getattr(product.image, "name", ""):
                            try:
                                if extra.image.storage.exists(file_name):
                                    extra.image.storage.delete(file_name)
                            except Exception:
                                pass
                        extra.delete()
                else:
                    if fp:
                        seen_fingerprints.add(fp)

        return deleted
