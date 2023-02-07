# get the ip of a user and produce a file transfer tunnel using socketio

import random
import uuid

import redis


class TicketCache:
    """Ticket cache is a redis cache that stores the tickets for the file transfer tunnels"""

    def __init__(self):
        self.cache = redis.Redis(host="localhost", port=6379, db=0)

    def create_ticket():
        # create a ticket for the file collection
        ticket = str(uuid.uuid4())
        return ticket[random.randint(1, 40) : random.randint(41, 80)]

    def cache_ticket(self, ticket):
        self.cache.set(ticket, True)

    def check_ticket(self, ticket):
        return self.cache.get(ticket)

    def remove_ticket(self, ticket):
        self.cache.delete(ticket)

    def get_tickets(self):
        return self.cache.keys()
