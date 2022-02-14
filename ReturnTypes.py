from enum import Enum


class Returns(Enum):
    SAFE = 1
    NOTSAFE = 2


class NotSafe(Enum):
    MALICIOUS = 1
    DANGEROUS = 2
    HARMFUL = 3


class URLResponse(Enum):
    HOSTNAME = 1
    PORT = 2
    QUERY = 3
    DECISION = 4
    REASON = 5


class Reasons(Enum):
    DEFAULT = "Safe since didnt match our criteria"
    LENGTH = "Length of Query too Long"
    PORT = "Port Numbers between 20000 - 24000 are malicious"
    HOSTNAME = "Hostname has invalid string"
