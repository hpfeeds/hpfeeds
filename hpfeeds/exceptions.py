class FeedException(Exception):
    pass


class Disconnect(Exception):
    pass


class ProtocolException(Disconnect):
    pass


class BadClient(ProtocolException):
    pass
