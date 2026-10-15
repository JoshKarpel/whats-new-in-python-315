from typing import Literal, TypeForm

def validate[T](value: object, typ: TypeForm[T]) -> T:
    raise NotImplementedError  # think pydantic's TypeAdapter

reveal_type(validate("x", str))
reveal_type(validate(None, int | None))
reveal_type(validate("GET", Literal["GET", "POST"]))
