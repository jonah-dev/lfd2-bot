
import discord
from pprint import pprint


class Player():
    def __init__(self, member: discord.Member):
        print(member)
        self.member = member
        self.ready = False

    def isReady(self):
        return self.ready

    def getName(self):
        if self.member.display_name == None:
            return ''
        return self.member.display_name

    def setType(self, player_type: str):
        self.player_type = player_type

    def setReady(self):
        self.ready = True

    def setUnready(self):
        self.ready = False

    def __eq__(self, other):
        if (isinstance(other, Player)):
            return self.member.id == other.member.id
        return False


    # Maybe define __hash__ at some point