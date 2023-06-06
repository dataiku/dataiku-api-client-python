class GovernUsersContainer(object):
    """
    An abstract class to represent a users container definition. Do not instance this class but one of its subclasses.
    """

    def __init__(self, type):
        self.type = type

    def build(self):
        raise NotImplementedError("Cannot build an abstract users container")


class GovernUserUsersContainer(GovernUsersContainer):
    """
    A users container representing a single user

    :param str user_login: the user login
    """

    def __init__(self, user_login):
        super(GovernUserUsersContainer, self).__init__(type="user")
        self.user_login = user_login

    def build(self):
        """
        :return: the users container definition as a dict
        :rtype: dict
        """
        return {"type": self.type, "login": self.user_login}

