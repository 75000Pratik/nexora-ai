from app.services.agent_router import (
    AgentRoute,
    AgentRouter,
)


def test_route_uses_document_qa_when_document_id_is_provided():
    router = AgentRouter()

    result = router.route(
        query="What does the document say?",
        document_id="doc-123",
    )

    assert result == AgentRoute.DOCUMENT_QA


def test_route_uses_document_qa_when_project_id_is_provided():
    router = AgentRouter()

    result = router.route(
        query="What does this project contain?",
        project_id="project-123",
    )

    assert result == AgentRoute.DOCUMENT_QA


def test_route_defaults_to_document_qa():
    router = AgentRouter()

    result = router.route(
        query="What is Python?",
    )

    assert result == AgentRoute.DOCUMENT_QA


def test_route_uses_general_when_explicitly_requested():
    router = AgentRouter()

    result = router.route(
        query="What is Python?",
        requested_route=AgentRoute.GENERAL,
    )

    assert result == AgentRoute.GENERAL

def test_document_id_takes_priority_when_both_ids_are_provided():
    router = AgentRouter()

    result = router.route(
        query="Explain this project document",
         document_id="doc-123",
        project_id="project-123",
        requested_route=AgentRoute.GENERAL,
    )

    assert result == AgentRoute.DOCUMENT_QA    
