from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class Event(models.Model):
    CATEGORY_CHOICES = [
        ("music", "Music"),
        ("sports", "Sports"),
        ("nightlife", "Nightlife"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    image = CloudinaryField("image", null=True, blank=True)

    payout_done = models.BooleanField(default=False)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="music",
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
    )

    def __str__(self):
        return self.title