import sqlite3
import sys, time, pickle
from random import randint, shuffle
from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet import reactor

chan = '#tested'
white_cards = []
with open('c:\python27\cahbot\whitecards.pickle', 'r') as f:
    white_cards = pickle.load(f)

class Bot(irc.IRCClient):

    def __init__(self):
        self.lineRate = 1
        self.white_cards = white_cards
        
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % (self.nickname,)
        

    def joined(self, channel):
        print "Joined %s." % (channel,)


            
    def privmsg(self, user, channel, msg):
        username = user.split('!')[0]
        if msg.startswith("!haiku"):
            self.haiku(channel)

    def haiku(self, channel):
        line1 = self.get_card()
        line2 = self.get_card()
        line3 = self.get_card()

        while len(line2)<20:
            line2 = self.get_card()

        while len(line1)>=len(line2):
            line1 = self.get_card()

        while len(line3)>=len(line2):
            line3 = self.get_card()

        msg = line1+"\n"+line2+"\n"+line3
        self.msg(channel, msg)
        



    def get_card(self):
        key = randint(1, len(self.white_cards)-1)
        card = self.white_cards[key][1]
        return card.encode('ascii', 'ignore')
        
            
            
    
        
class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self, channel, nickname='haikubot'):
        self.channel = channel
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)




if __name__ == "__main__":
    reactor.connectTCP('irc.freenode.net', 6667, BotFactory(chan))
    reactor.run()
        
    
