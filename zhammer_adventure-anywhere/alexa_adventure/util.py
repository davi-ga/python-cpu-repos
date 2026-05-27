from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

from typing_extensions import Literal

LambdaHandler = Callable[[Dict, Any], Dict]


class InvocationDetails(NamedTuple):
    request_type: str
    intent_name: Optional[str]


class Skill:
    handler_by_invocation_details: Dict[InvocationDetails, LambdaHandler]

    def __init__(self) -> None:
        self.handler_by_invocation_details = {}

    def intent(self, intent_name: str) -> Callable[[LambdaHandler], LambdaHandler]:
        return self._invocation("IntentRequest", intent_name)

    def request(self, request_type: str) -> Callable[[LambdaHandler], LambdaHandler]:
        return self._invocation(request_type)

    def _invocation(
        self, request_type: str, intent_name: Optional[str] = None
    ) -> Callable[[LambdaHandler], LambdaHandler]:
        invocation_details = InvocationDetails(request_type, intent_name)
        invalid_reason = Skill._invocation_details_invalid_reason(invocation_details)
        if invalid_reason:
            raise RuntimeError(invalid_reason)

        def decorator(handler: LambdaHandler) -> LambdaHandler:
            self.handler_by_invocation_details[invocation_details] = handler
            return handler

        return decorator

    def handle(self, event: Dict, context: Any) -> Dict:
        invocation_details = Skill._pluck_invocation_details(event)
        try:
            handler = self.handler_by_invocation_details[invocation_details]
        except KeyError as e:
            raise RuntimeError(f"No handler registered for invocation {e}")

        return handler(event, context)

    @staticmethod
    def _pluck_invocation_details(event: Dict) -> InvocationDetails:
        return InvocationDetails(
            request_type=event["request"]["type"],
            intent_name=event["request"].get("intent", {}).get("name"),
        )

    @staticmethod
    def _invocation_details_invalid_reason(
        invocation_details: InvocationDetails
    ) -> Optional[str]:
        if (
            invocation_details.request_type == "IntentRequest"
            and invocation_details.intent_name is None
        ):
            return "intent_name cannot be none for 'IntentRequest' invocation"
        return None
