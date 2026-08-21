from types import SimpleNamespace

from private_media_gateway.media_review import MediaIntake, process_media


class RecordingCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        message = SimpleNamespace(content='{"delivery_summary":"A calm recovery update."}')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class RecordingClient:
    def __init__(self) -> None:
        self.completions = RecordingCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def test_health_data_stays_out_of_model_processing() -> None:
    client = RecordingClient()
    intake = MediaIntake(
        asset_id="asset-clinic-17",
        transcript="Patient discusses post-operative mobility.",
        creator_consent=True,
        contains_health_data=True,
    )

    job = process_media(intake, client)

    assert job.state == "privacy_review"
    assert job.delivery_summary is None
    assert client.completions.calls == []


def test_consented_non_health_media_becomes_creator_delivery() -> None:
    client = RecordingClient()
    intake = MediaIntake(
        asset_id="asset-studio-42",
        transcript="A studio tour covering lighting and microphone placement.",
        creator_consent=True,
        contains_health_data=False,
    )

    job = process_media(intake, client)

    assert job.state == "ready_for_creator"
    assert job.delivery_summary == "A calm recovery update."
    assert client.completions.calls[0]["model"] == "auto"
