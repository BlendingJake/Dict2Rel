class ToRowsRequiredError(Exception):
    def __init__(
        self,
        message: str = "A function to turn tables into rows must be provided when the tables aren't in row form already",
    ) -> None:
        super().__init__(message)
