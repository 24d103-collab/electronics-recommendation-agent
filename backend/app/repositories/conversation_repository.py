
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message


def create_conversation(session: Session) -> Conversation:
    conversation = Conversation(
        status="active",
        current_requirements={},
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def add_message(
    session: Session,
    conversation: Conversation,
    role: str,
    content: str,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_conversation(
    session: Session,
    conversation_id: int,
) -> Conversation | None:
    statement = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
    )
    return session.scalar(statement)


def get_conversation_messages(
    session: Session,
    conversation_id: int,
) -> list[Message]:
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at, Message.id)
    )
    return list(session.scalars(statement).all())


def update_requirements(
    session: Session,
    conversation: Conversation,
    requirements: dict,
) -> Conversation:
    conversation.current_requirements = requirements
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation
