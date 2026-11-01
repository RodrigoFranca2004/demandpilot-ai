from fastapi import APIRouter, Depends, HTTPException, status
from google.genai import errors
from sqlalchemy.orm import Session

from app.agents.advisor import ask_advisor
from app.core.database import get_db
from app.models import Restaurant
from app.schemas.advisor import AdvisorChatRequest, AdvisorChatResponse

router = APIRouter(tags=["Advisor"])


@router.post(
    "/restaurants/{restaurant_id}/advisor/chat",
    response_model=AdvisorChatResponse,
)
def chat_with_advisor(
    restaurant_id: int,
    payload: AdvisorChatRequest,
    session: Session = Depends(get_db),
) -> AdvisorChatResponse:
    restaurant = session.get(Restaurant, restaurant_id)

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    try:
        answer = ask_advisor(
            session=session,
            restaurant_id=restaurant_id,
            question=payload.message,
        )

    except ValueError as exc:
        if str(exc) == "GEMINI_API_KEY is not configured":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini API key is not configured",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    except errors.APIError as exc:
        if exc.code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini API quota or rate limit exceeded",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API request failed",
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI advisor could not generate a valid response",
        ) from exc

    return AdvisorChatResponse(answer=answer)
