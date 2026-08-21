import uvicorn
from fastapi import FastAPI

from .media_review import MediaIntake, ProcessingJob, gateway_client, process_media

service = FastAPI(title="Private media gateway cutover")


@service.post("/media-jobs", response_model=ProcessingJob)
def create_media_job(intake: MediaIntake) -> ProcessingJob:
    return process_media(intake, gateway_client())


def run() -> None:
    uvicorn.run("private_media_gateway.creator_delivery:service", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
