from abc import ABC, abstractmethod


class PaymentProvider(ABC):

    @abstractmethod
    def charge(self, *, amount, reference):
        pass
