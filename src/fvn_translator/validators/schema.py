from pydantic import BaseModel, ValidationError


def validate_document(model: type[BaseModel], payload: object) -> list[str]:
    try:
        model.model_validate(payload)
    except ValidationError as exc:
        return [error["msg"] for error in exc.errors()]
    return []
