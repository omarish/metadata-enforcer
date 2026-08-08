"""Sample vault schema used by the README and smoke tests."""

from pathlib import Path

from metadata_enforcer import models


class Essay(models.Model):
    title = models.TextField()
    latex = models.BooleanField(default=False)
    tags = models.TagsField(default=list, optional=True)

    class Meta:
        extra = models.ExtraFields.FORBID
        field_order = ("title", "tags", "latex")


class Project(models.Model):
    title = models.TextField()
    status = models.TextField(choices=("active", "done", "paused"), default="active")

    class Meta:
        field_order = ("title", "status")


ROUTES = {
    Path("essays"): Essay,
    Path("projects"): Project,
}
