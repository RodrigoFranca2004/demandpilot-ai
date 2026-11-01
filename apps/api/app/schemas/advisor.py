from pydantic import BaseModel, ConfigDict, Field


class AdvisorChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=1000)


class AdvisorChatResponse(BaseModel):
    answer: str
