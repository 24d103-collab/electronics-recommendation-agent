
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.llm_service import extract_requirements_with_llm
from app.agent.requirements import missing_information
from app.api.products import get_db
from app.repositories.conversation_repository import (
    add_message,
    create_conversation,
    get_conversation,
    update_requirements,
)
from app.schemas.conversation import (
    ConversationCreateResponse,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.recommendation_service import recommend_products


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Conversations"],
)


@router.post(
    "",
    response_model=ConversationCreateResponse,
    status_code=201,
)
def start_conversation(session: Session = Depends(get_db)):
    conversation = create_conversation(session)

    return {
        "conversation_id": conversation.id,
        "status": conversation.status,
    }


@router.post("/{conversation_id}/messages")
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    session: Session = Depends(get_db),
):
    conversation = get_conversation(session, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    # Save the customer's message before processing it.
    add_message(session, conversation, "user", payload.message)

    existing_requirements = conversation.current_requirements or {}

    try:
        requirements = extract_requirements_with_llm(
            payload.message,
            existing_requirements,
        )
    except Exception:
        logger.exception(
            "Requirement extraction failed for conversation %s",
            conversation_id,
        )

        # Do not pretend the new message was successfully understood.
        reply = (
            "I couldn't process that message because my local AI model "
            "is temporarily unavailable or returned an invalid response. "
            "Your previous requirements are preserved. Please try again."
        )

        add_message(session, conversation, "assistant", reply)

        return {
            "conversation_id": conversation.id,
            "reply": reply,
            "current_requirements": existing_requirements,
            "status": conversation.status,
        }

    update_requirements(session, conversation, requirements)

    # Ask a follow-up only when required information is missing.
    question = missing_information(requirements)

    if question:
        reply = question
    else:
        # Recommendations are only generated when requirements are ready.
        recommendations = recommend_products(session, requirements)

        if not recommendations:
            reply = (
                "I couldn't find any available products matching your "
                "current requirements. You could increase your budget "
                "or adjust your intended use."
            )
        else:
            lines = ["Here are your best matches:"]

            for index, product in enumerate(recommendations, start=1):
                lines.append(
                    f"{index}. {product['name']} — "
                    f"₹{product['price']:,.0f}"
                )
                lines.append(f"   {product['explanation']}")

                specifications = product.get("specifications") or {}
                if specifications:
                    lines.append(
                        f"   Key specifications: {specifications}"
                    )

            reply = "\n".join(lines)

    add_message(session, conversation, "assistant", reply)

    return {
        "conversation_id": conversation.id,
        "reply": reply,
        "current_requirements": requirements,
        "status": conversation.status,
    }


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def read_conversation(
    conversation_id: int,
    session: Session = Depends(get_db),
):
    conversation = get_conversation(session, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = [
        MessageResponse.model_validate(message)
        for message in conversation.messages
    ]

    return {
        "conversation_id": conversation.id,
        "status": conversation.status,
        "current_requirements": conversation.current_requirements,
        "messages": messages,
    }
