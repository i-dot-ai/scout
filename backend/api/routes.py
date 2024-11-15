import base64
import json
import logging
import typing
from functools import lru_cache
from typing import Annotated
from typing import Optional
from uuid import UUID

import requests
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi.responses import Response
from pydantic import BaseModel

from backend.utils.filters import Filters
from backend.utils.rating_request import RatingRequest
from scout.DataIngest.models.schemas import Chunk as PyChunk
from scout.DataIngest.models.schemas import ChunkFilter
from scout.DataIngest.models.schemas import Criterion as PyCriterion
from scout.DataIngest.models.schemas import CriterionFilter
from scout.DataIngest.models.schemas import File as PyFile
from scout.DataIngest.models.schemas import FileFilter
from scout.DataIngest.models.schemas import Project as PyProject
from scout.DataIngest.models.schemas import ProjectFilter
from scout.DataIngest.models.schemas import Rating as PyRating
from scout.DataIngest.models.schemas import RatingCreate
from scout.DataIngest.models.schemas import RatingFilter
from scout.DataIngest.models.schemas import RatingUpdate
from scout.DataIngest.models.schemas import Result as PyResult
from scout.DataIngest.models.schemas import ResultFilter
from scout.DataIngest.models.schemas import User as PyUser
from scout.DataIngest.models.schemas import UserCreate
from scout.DataIngest.models.schemas import UserFilter
from scout.DataIngest.models.schemas import UserUpdate
from scout.utils.config import Settings
from scout.utils.storage import postgres_interface as interface
from scout.utils.storage.postgres_database import SessionLocal


router = APIRouter()


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

SECRET_KEY = settings.API_JWT_KEY
ALGORITHM = "HS256"


models = {
    "result": PyResult,
    "criterion": PyCriterion,
    "chunk": PyChunk,
    "file": PyFile,
    "project": PyProject,
    "user": PyUser,
    "rating": PyRating,
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TokenData(BaseModel):
    username: str


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_current_user(x_amzn_oidc_data: Annotated[str, Header()] = None) -> PyUser | None:
    """
    Called on every endpoint to decode JWT in every request header under the name "Authorization"
    Gets or creates the user based on the email in the JWT
    Args:
        x_amzn_oidc_data: The incoming JWT from cognito, passed via the frontend app
    Returns:
        User: The user matching the username in the token
    """

    if settings.ENVIRONMENT == "local":
        # A JWT for local testing, an example JWT from cognito, for user test@test.com
        # pragma: allowlist nextline secret
        authorization = "eyJ0eXAiOiJKV1QiLCJraWQiOiIxMjM0OTQ3YS01OWQzLTQ2N2MtODgwYy1mMDA1YzY5NDFmZmciLCJhbGciOiJIUzI1NiIsImlzcyI6Imh0dHBzOi8vY29nbml0by1pZHAuZXUtd2VzdC0yLmFtYXpvbmF3cy5jb20vZXUtd2VzdC0yX2V4YW1wbGUiLCJjbGllbnQiOiIzMjNqZDBuaW5kb3ZhM3NxdTVsbjY2NTQzMiIsInNpZ25lciI6ImFybjphd3M6ZWxhc3RpY2xvYWRiYWxhbmNpbmc6ZXUtd2VzdC0yOmFjYzpsb2FkYmFsYW5jZXIvYXBwL2FsYi85OWpkMjUwYTAzZTc1ZGVzIiwiZXhwIjoxNzI3MjYyMzk5fQ.eyJzdWIiOiI5MDQyOTIzNC00MDMxLTcwNzctYjliYS02MGQxYWYxMjEyNDUiLCJlbWFpbF92ZXJpZmllZCI6InRydWUiLCJjdXN0b206cHJvamVjdHMiOiJ0ZXN0IHByb2plY3R8dGVzdCBwcm9qZWN0IDJ8dGVzdC1wcm9qZWN0IiwiZW1haWwiOiJ0ZXN0QHRlc3QuY28udWsiLCJ1c2VybmFtZSI6InRlc3RAdGVzdC5jby51ayIsImV4cCI6MTcyNzI2MjM5OSwiaXNzIjoiaHR0cHM6Ly9jb2duaXRvLWlkcC5ldS13ZXN0LTIuYW1hem9uYXdzLmNvbS9ldS13ZXN0LTJfZXhhbXBsZSJ9.CD5T4hoFiVuC7aABAAeDeI0Di2MSv8Icy5R05jF-Pzc"

    else:
        authorization = x_amzn_oidc_data

    logger.info(f"auth from token: {authorization}")

    if not authorization:
        logger.info("No authorization header provided")
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(".")

    if len(parts) != 3:
        raise HTTPException(
            status_code=401,
            detail="Malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = parts[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)

    try:
        decoded = base64.urlsafe_b64decode(payload).decode("utf-8")
        token_content = json.loads(decoded)
        email = token_content["email"] or None
        if not email:
            logger.info("No email in token")
            raise HTTPException(
                status_code=401,
                detail="Email not found in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            users: list[PyUser] = interface.filter_items(UserFilter(email=email))
            user = users[0] if len(users) > 0 else None

            project_names = token_content.get("custom:projects", None)
            projects = []
            if project_names:
                project_names_split = project_names.split("|")
                for project_name in project_names_split:
                    project = interface.filter_items(ProjectFilter(name=project_name))
                    if project:
                        projects.append(project[0])
            if not user:
                user: PyUser = interface.get_or_create_item(UserCreate(email=email, projects=projects))
            else:
                user = interface.update_item(UserUpdate(id=user.id, email=user.email, projects=projects))
            return user
    except Exception as e:
        logger.info(e)
        raise HTTPException(
            status_code=401,
            detail="Failed to decode token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def is_item_in_user_projects(
    item: PyUser | PyRating | PyFile | PyProject | PyResult | PyCriterion | PyChunk,
    user: PyUser,
) -> bool:
    # Using typing.cast just helps with intellisense
    user_project_names = [project.name for project in user.projects]
    if type(item) is PyProject:
        item = typing.cast(PyProject, item)
        if item.name in user_project_names:
            return True
    if type(item) is PyUser:
        return True
    if type(item) is PyRating:
        item = typing.cast(PyRating, item)
        if item.project.name in user_project_names:
            return True
    if type(item) is PyFile:
        item = typing.cast(PyFile, item)
        if item.project.name in user_project_names:
            return True
    if type(item) is PyResult:
        item = typing.cast(PyResult, item)
        if item.project.name in user_project_names:
            return True
    if type(item) is PyCriterion:
        item = typing.cast(PyCriterion, item)
        criterion_project_names = [project.name for project in item.projects]
        if any(project_name in user_project_names for project_name in criterion_project_names):
            return True
    if type(item) is PyChunk:
        item = typing.cast(PyChunk, item)
        file = interface.get_by_id(PyFile, item.file.id)
        if file.project.name in user_project_names:
            return True
    logger.debug(f"Item {item.id} not available to user {user.id}")
    return False


@router.get("/item/{table}")
def get_items(
    request: Request,
    table: str,
    uuid: Optional[UUID] = Query(None),
    current_user: PyUser = Depends(get_current_user),
):
    logger.log(level=logging.INFO, msg=request)
    model = models.get(table.lower())
    if not model:
        raise HTTPException(status_code=400, detail="Invalid table name")

    if uuid:
        item = interface.get_by_id(model, uuid)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
    else:
        items = interface.get_all(model)
        return items


@router.get("/related/{uuid}/{model1}/{model2}")
def get_related_items(
    uuid: UUID | None,
    model1: str,
    model2: str,
    limit_to_user: Optional[bool] = False,
    current_user: PyUser = Depends(get_current_user),
):
    source_model = models.get(model1.lower())
    target_model = models.get(model2.lower())
    if not source_model or not target_model:
        raise HTTPException(status_code=400, detail="Invalid model names")

    source_item = interface.get_by_id(source_model, uuid)
    target_items = source_item.dict().get(f"{model2.lower()}s", [])
    populated_target_items = [interface.get_by_id(target_model, item["id"]) for item in target_items]
    if limit_to_user:
        populated_target_items = [
            populated_target_item
            for populated_target_item in populated_target_items
            if populated_target_item.user.id == current_user.id
        ]
    return populated_target_items


@router.post("/read_items_by_attribute")
def read_items_by_attribute(
    filters: Filters,
    request: Request,
    current_user: PyUser = Depends(get_current_user),
):
    logger.debug(f"headers: {request.headers}")
    model = models.get(filters.model.lower())
    if not model:
        raise HTTPException(status_code=400, detail="Invalid model name")

    items = []
    if model is PyProject:
        filter = ProjectFilter(
            name=filters.filters.get("name", None),
            results_summary=filters.filters.get("results_summary", None),
        )
        items = interface.filter_items(filter)
    if model is PyFile:
        filter = FileFilter(
            name=filters.filters.get("name", None),
            type=filters.filters.get("type", None),
            clean_name=filters.filters.get("clean_name", None),
            summary=filters.filters.get("summary", None),
            source=filters.filters.get("source", None),
        )
        items = interface.filter_items(filter)
    if model is PyResult:
        filter = ResultFilter(
            answer=filters.filters.get("answer", None),
            full_text=filters.filters.get("full_text", None),
        )
        items = interface.filter_items(filter)
    if model is PyCriterion:
        filter = CriterionFilter(
            gate=filters.filters.get("gate", None),
            category=filters.filters.get("category", None),
            question=filters.filters.get("question", None),
            evidence=filters.filters.get("evidence", None),
        )
        items = interface.filter_items(filter)
    if model is PyChunk:
        filter = ChunkFilter(
            idx=filters.filters.get("idx", None),
            text=filters.filters.get("text", None),
            page_num=filters.filters.get("page_num", None),
        )
        items = interface.filter_items(filter)
    if model is PyUser:
        filter = UserFilter(
            username=filters.filters.get("username", None),
            name=filters.filters.get("name", None),
        )
        items = interface.filter_items(filter)
    return items


@router.get("/get_file/{uuid}")
def get_file(
    uuid: UUID,
    current_user: PyUser = Depends(get_current_user),
):
    try:
        file = interface.get_by_id(PyFile, uuid)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        file_extension = file.s3_key.split(".")[-1].lower()

        if file_extension == "pdf":
            file_type = "application/pdf"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        # Replace this file.url with a pre-signed url from a s3 bucket to test with remote files
        file_response = requests.get(file.url)
        file_response.raise_for_status()
        file_content = file_response.content
        return Response(
            content=file_content,
            media_type=file_type,
            headers={
                "Content-Disposition": f"attachment; filename={file.s3_key.split('/')[-1]}",
                "X-File-Type": file_type,
            },
        )

    except Exception as e:
        logger.exception("An error occurred while retrieving the file")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving the file: {str(e)}",
        )


@router.post("/rate")
def rate_response(
    rating_request: RatingRequest,
    current_user: PyUser = Depends(get_current_user),
):
    result = interface.get_by_id(PyResult, rating_request.result_id)
    if not result:
        return Response("Referenced result not found", 404)
    existing_rating = interface.filter_items(RatingFilter(user=current_user, result=result, project=result.project))
    if existing_rating:
        updated_item = interface.update_item(
            RatingUpdate(
                id=existing_rating[0].id,
                user=current_user,
                result=result,
                project=result.project,
                positive_rating=rating_request.good_response,
            )
        )
        return {"message": f"Rating {updated_item.id} submitted successfully"}
    else:
        new_rating = RatingCreate(
            user=current_user,
            result=result,
            project=result.project,
            positive_rating=rating_request.good_response,
        )
        response = interface.get_or_create_item(new_rating)
        return {"message": f"Rating {response.id} submitted successfully"}
