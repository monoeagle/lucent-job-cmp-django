from apps.provisioning.clients import GitLabStubClient


class TestGitLabStubClient:
    def setup_method(self):
        self.client = GitLabStubClient()

    def test_trigger_returns_pipeline_id(self):
        result = self.client.trigger_pipeline("VM", {"cpu": 4})
        assert "pipeline_id" in result
        assert len(result["pipeline_id"]) > 0

    def test_trigger_returns_status_running(self):
        result = self.client.trigger_pipeline("VM", {})
        assert result["status"] == "running"

    def test_pipeline_ids_unique(self):
        r1 = self.client.trigger_pipeline("VM", {})
        r2 = self.client.trigger_pipeline("VM", {})
        assert r1["pipeline_id"] != r2["pipeline_id"]

    def test_get_status_unknown_returns_none(self):
        assert self.client.get_pipeline_status("nope") is None

    def test_complete_success(self):
        r = self.client.trigger_pipeline("VM", {})
        self.client.complete_pipeline(r["pipeline_id"], success=True)
        assert self.client.get_pipeline_status(r["pipeline_id"]) == "success"

    def test_complete_failure(self):
        r = self.client.trigger_pipeline("VM", {})
        self.client.complete_pipeline(r["pipeline_id"], success=False)
        assert self.client.get_pipeline_status(r["pipeline_id"]) == "failed"
