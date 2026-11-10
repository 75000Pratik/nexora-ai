from enum import Enum


class AgentRoute(str, Enum):
    DOCUMENT_QA = "document_qa"
    GENERAL = "general"


class AgentRouter:
    def route(
            self,
            query: str,
            document_id: str | None = None,
            project_id: str | None = None,
            requested_route: AgentRoute = AgentRoute.DOCUMENT_QA
    ) -> AgentRoute:
        if document_id or project_id:
            return AgentRoute.DOCUMENT_QA

        return requested_route
