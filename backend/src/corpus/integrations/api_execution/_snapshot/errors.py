class ApiExecutionError(RuntimeError):
    def __init__(self, code: str, public_message: str) -> None:
        super().__init__(code)
        self.code = code
        self.public_message = public_message


class ContractError(ApiExecutionError):
    pass


class UnsupportedPluginError(ApiExecutionError):
    pass


class NetworkPolicyError(ApiExecutionError):
    pass


class ApprovalError(ApiExecutionError):
    pass


class CredentialError(ApiExecutionError):
    pass


class RequestValidationError(ApiExecutionError):
    pass


class ResponseValidationError(ApiExecutionError):
    pass


class ResponseTooLargeError(ApiExecutionError):
    pass

