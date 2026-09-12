class InvalidEmailError(ValueError):
    """
    Email exception when email is not correct
    """
    pass

class UserNotFoundError(LookupError):
    """
    Error when user does not exist
    """
    pass


class UserAlreadyExistsError(ValueError):
    """
    Error when user with given email or username already exists
    """
    pass