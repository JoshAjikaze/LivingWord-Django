from django.core.exceptions import ValidationError
from django.db import models


class SiteSettings(models.Model):
    """
    Singleton model — one row only. Holds the copy/branding that appears
    on the homepage and footer so the client can edit it without a
    code deploy.
    """
    imprint_name = models.CharField(max_length=120, default="The Living Word Library")
    tagline = models.CharField(max_length=200, default="Scripture for Life. Wisdom for Generations.")
    hero_image = models.ImageField(upload_to="site/", blank=True)

    intro_text = models.TextField(
        default=(
            "The Living Word Library is a family of devotional books rooted in personal "
            "encounter with God through Scripture — written to help you know Him more "
            "deeply and walk in the potential He's placed in you."
        ),
        help_text="Shown under the hero headline on the homepage.",
    )
    mission_text = models.TextField(
        default=(
            "Each book in this library stands on its own, yet they share one heart: to "
            "help readers encounter truth, not just study it. Whether you're seeking the "
            "names of God, the wisdom of His voice, or the lives that echo His "
            "faithfulness through Scripture, there's a book here for this season of your walk."
        ),
        help_text="Shown in the 'One heart. Many entry points.' section.",
    )

    footer_blurb = models.CharField(
        max_length=200,
        default="Devotional books rooted in Scripture — written to help you encounter God, not just study Him.",
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def clean(self):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError("Site Settings already exists — edit the existing record instead of creating a new one.")

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.imprint_name

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AuthorProfile(models.Model):
    """
    The 'About the Author' content. Modeled separately from Book.author
    (a simple CharField there) since this is the long-form bio page —
    keeping it here avoids coupling the About page to a specific book's author FK.
    """
    name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to="author/", blank=True)
    bio = models.TextField()

    class Meta:
        verbose_name = "Author Profile"
        verbose_name_plural = "Author Profile"

    def __str__(self):
        return self.name
