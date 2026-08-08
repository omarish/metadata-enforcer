"""Example vault schema models (adapted from a real personal vault).

Point the CLI at this file or copy the pattern into your vault's schema.py:

    metadata-enforcer check --schema examples/vault_schema.py /path/to/vault
"""

from pathlib import Path

from metadata_enforcer import models


class AbstractPage(models.Model):
    latex = models.BooleanField(
        default=False, description="Does this page contain LaTeX?"
    )
    sync_id = models.UUIDField(description="Used for syncing with website.")
    title = models.TextField()
    description = models.TextField(optional=True)

    class Meta:
        abstract = True


class Essay(AbstractPage):
    tags = models.TagsField(
        default=list, description="Tags associated with this essay."
    )
    revision_id = models.TextField(default="1")
    github_url = models.TextField(optional=True)

    class Meta:
        field_order = ("title", "description", "tags", "latex", "revision_id", "sync_id")


class WontPublishEssay(Essay):
    sync_id = models.UUIDField(
        optional=True,
        description="Used for syncing with website when present.",
    )


class Project(AbstractPage):
    pass


class Page(AbstractPage):
    path = models.URLPathField()


ROUTES = {
    Path("essays/wont-publish"): WontPublishEssay,
    Path("essays"): Essay,
    Path("projects"): Project,
}
