"""GitLab stub client for pipeline simulation."""
import uuid


class GitLabStubClient:
    """In-memory stub that simulates GitLab CI pipeline triggers."""

    def __init__(self):
        self._pipelines = {}

    def trigger_pipeline(self, template_name, parameters):
        """Trigger a fake pipeline and return its ID + status."""
        pipeline_id = uuid.uuid4().hex[:12]
        self._pipelines[pipeline_id] = "running"
        return {"pipeline_id": pipeline_id, "status": "running"}

    def get_pipeline_status(self, pipeline_id):
        """Return the status of a pipeline, or None if unknown."""
        return self._pipelines.get(pipeline_id)

    def complete_pipeline(self, pipeline_id, success=True):
        """Mark a pipeline as success or failed."""
        if pipeline_id in self._pipelines:
            self._pipelines[pipeline_id] = "success" if success else "failed"
