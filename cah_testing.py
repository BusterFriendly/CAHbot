import sqlite3
import sys, time
from random import randint, shuffle
from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet import reactor

network = 'asimov.freenode.net'
chan = '#testedCAH'
db = 'cah.db'

class Player(object):

    def __init__(self, name):
        self.name = name
        self.hand = {}
        self.score = 0
        self.dealer = False

class Bot(irc.IRCClient):

    def __init__(self):
        self.lineRate = 1
        self.players = []
        self.white_cards = []
        self.black_cards = []
        #self.play_num = 0
        self.current_black = ''
        #self.all_played = 0
        self.current_dealer = 0
        self.dealer_name = ''
        self.played_white = []
        self.main_chan = chan
        self.winner = ''
        self.played_black = ''
        self.vote_count = 0
        self.running = False
        self.valid_choices = []
        self.rando = False
        self.rando_score = 0
        self.draw = 1
        self.multi_only = False
        self.dealer_plays = False
        
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % (self.nickname,)

    def userLeft(self, user, channel):
        username = user.split('!')[0]
        for x in self.players:
            if x.name == username:
                self.remove_player(username, channel)

    def userQuit(self, user, channel):
        username = user.split('!')[0]
        for x in self.players:
            if x.name == username:
                self.remove_player(username, channel)
        

    def joined(self, channel):
        print "Joined %s." % (channel,)


    def sendmessage(self, username, channel, msg):
        if channel == username:
            self.msg(username, msg)
        else:
            self.msg(channel, msg)
            
    def privmsg(self, user, channel, msg):
        username = user.split('!')[0]
        print user + ":" + msg
        if msg.startswith("!play"):
            self.add_player(username, channel)
            return
        elif msg.startswith("!dealerplays"):
            self.dealer_plays = not self.dealer_plays
            msg = "Dealer plays: " + str(self.dealer_plays)
            self.msg(channel, msg)
            return
        elif msg.startswith("!help"):
            msg = """!play - join player list.
!remove [name] - remove player from list.
!start - start a new game.
!score - see the scoreboard.
!dealmein - join a game in progress (use !play first).
!continue - move to the next round if something gets hung.
!trash ### ### ### - trash any number of cards from your hand for 1 point.
!rando - add Rando Cardrissian to the game.
!reset - reset the whole damn bot and start over (for emergencies)."""
            self.msg(channel, msg)
        elif msg.startswith("!start"):
            self.running = True
            self.main_chan = channel
            msg = "Shuffling cards..."
            self.sendmessage('', self.main_chan, msg)
            self.setup()
            msg = "Dealing cards..."
            self.sendmessage('',self.main_chan, msg)
            self.deal_cards(10, self.players)
            self.next_round()
            
            return
        elif msg.startswith("!gimme"):
            msg = msg.split(" ")
            self.gimme(int(msg[1]))
        elif msg.startswith("!kill"):
            sys.exit(0)
            return
        elif msg.startswith("!haiku"):
            self.haiku(channel)
        elif msg.startswith("!rando"):
            self.rando = not self.rando
            if self.rando:
                self.msg(channel, "Rando Cardrissian added to the game!")
            else:
                self.msg(channel, "Rando Cardrissian removed from the game!")
            
        
        elif msg.startswith("!dealmein"):
            for x in self.players:
                if x.name == username and len(x.hand) == 0:
                    self.deal_cards(10, [x])
        elif msg.startswith("!hand"):

            for x in self.players:
                if x.name == username:
                    player = x.name
                    msg = ''
                    for i in x.hand:
                        player_card = "%d - %s\n" %(i,x.hand[i])
                        msg = msg + player_card                        
            self.msg(player, msg)
            return
        elif msg.startswith("!remove"):
            player = msg.split(" ")
            self.remove_player(player[1], channel)
        elif msg.startswith("!continue"):
            self.main_chan = channel
            self.current_dealer = self.current_dealer - 1
            self.played_white = []
            self.next_round()
        elif msg.startswith("!vote"):
            if username == self.players[self.current_dealer].name:    
                choice = msg.split(" ")
                choice = int(choice[1])
                print choice
                if choice in self.valid_choices:
                    for x in self.played_white:
                        if choice == x[0]:
                            self.winner = x[2]
                            msg = "%s wins the round!" %self.winner
                            self.msg(self.main_chan, msg)
                    if self.winner == 'Rando':
                        self.rando_score = self.rando_score + 1
                        msg = "Rando has %d points, nerds." %self.rando_score
                        self.msg(self.main_chan, msg)
                    else:                            
                        for x in self.players:
                            if x.name == self.winner:
                                x.score = x.score+1
                                if x.score == 10:
                                    msg = "%s wins with 10 points! !start to play again." %self.winner
                                    self.sendmessage('', self.main_chan, msg)
                                    return

                    if self.rando and self.rando_score == 10:
                        msg = "Rando wins the game! Suck it, nerds."
                        self.msg(self.main_chan, msg)
                        msg = "Use !start to start a new game. Use !rando to kick Rando."
                        self.msg(self.main_chan, msg)
                        return
                    self.played_white = []
                    self.next_round()
                else:
                    self.msg(channel, "Invalid choice! Try again.")
                    return
            else:
                msg = "You're not the current Card Czar, %s." %username
                self.sendmessage('', channel, msg)
        elif msg.startswith("!score"):
            for x in self.players:
                msg = "%s - %d" %(x.name, x.score)
                self.sendmessage('', channel, msg)
            if self.rando:
                msg = "Rando Cardrissian - %d" %self.rando_score
                self.msg(self.main_chan, msg)
        elif msg.startswith("!trash"):
            msg = msg.split(" ")
            trash = []
            for x in msg:
                if x.isdigit():
                    trash.append(int(x))
            for x in self.players:
                if x.name == username:
                    for key in trash:
                        if key in x.hand:
                            msg = "%s trashed '%s'" %(username, x.hand[key])
                            self.msg(self.main_chan, msg)
                            del x.hand[key]
                            self.deal_cards(1, [x])
                        else:
                            msg = "You don't have card #%d!" %key
                            self.msg(username, msg)
                    x.score = x.score - 1
                    
            return
        elif msg.startswith("!theblacks"):
            self.msg(self.main_chan, "Logging to console...")
            for x in self.black_cards:
                print x

        elif msg.startswith("!reset"):
            self.current_black = ''
            self.current_dealer = 0
            self.dealer_name = ''
            self.played_white = []
            self.main_chan = ''
            self.winner = ''
            self.played_black = ''
            self.vote_count = 0
            self.running = False
            self.players = []
            self.white_cards = []
            self.black_cards = []
            self.rando = False
            self.rando_score = 0
            self.draw = 1
            self.multi_only = False
            self.msg(channel, "Bot completely reset! Add players with !play, then start game with !start.")
        elif msg.startswith("!multi"):
            self.multi_only = not self.multi_only
            if self.multi_only:
                self.msg(channel, "Multi-only mode enabled.")
            else:
                self.msg(channel, "Multi-only mode disabled.")

        elif msg.startswith("!whothefuckarewewaitingon"):
            dudes = []
            for x in self.played_white:
                dudes.append(x[2])
            for x in self.players:
                if x.name not in dudes and not x.dealer:
                    msg = "%s, play a goddamn card." %x.name
                    self.msg(self.main_chan, msg)
            return
                    
        elif msg.split(" ")[0].isdigit():
            print channel
            print username
            print self.nickname
            if channel == self.nickname:
                self.play(username, msg)
            else:
                pass

    def play(self, username, msg):
        if username == self.players[self.current_dealer].name and not self.dealer_plays:
            msg = "You're the Card Czar, you don't play this round!"
            self.msg(username, msg)
            return
        msg = msg.split(" ")
        played_cards = []
        index = []
        hand_index = []
        for x in msg:
            key = int(x)
            index.append(key)
        if len(index) < self.draw:
            self.msg(username, "Not enough cards to complete the sentence. Try again!")
            return
        print "play index:"
        print index
        for x in self.players:
            if x.name == username:
                for key in index:
                    if key in x.hand:
                        played_cards.append((x, x.hand[key], username))
                        del x.hand[key]
                    else:
                        msg = "You don't have card #%d." %key
                        self.msg(username, msg)
                        return

                msg = self.construct_sentence(self.played_black, played_cards)
                self.msg(username, msg)
                self.played_white.append((len(self.played_white), msg, username))
                self.deal_cards(self.draw, [x])
                print self.played_white
                print len(self.played_white)
                print len(self.players)
        if len(self.played_white) >= len(self.players)-1+self.rando+self.dealer_plays:
            self.start_voting()
            

    def start_voting(self):
        msg = "All cards have been submitted. Vote using '!vote #'"
        self.sendmessage('', self.main_chan, msg)
        shuffle(self.played_white)
        vote_id = 1
        self.valid_choices = []          
        for x in range(len(self.played_white)):
            self.played_white[x] = (vote_id, self.played_white[x][1], self.played_white[x][2])
            self.valid_choices.append(vote_id)
            vote_id = vote_id + 1
        for x in self.played_white:
            msg = "%d - %s" %(x[0], x[1])
            self.msg(self.main_chan, msg)

    def gimme(self, card_id):
        self.played_white = []
        card = 0
        for x in self.black_cards:
            if card_id == x[0]:
                card = x
        if not card:
            print "Card not found."
        print card
        self.draw = int(card[3])
        self.played_black = card[1].encode('ascii', 'ignore')
        self.msg(self.main_chan, self.played_black)
        self.rando_plays()
            

    def draw_black(self):
        card_id = randint(0, len(self.black_cards)-1)
        card = self.black_cards[card_id]
        self.black_cards.remove(card)
        print card
        self.draw = int(card[3])
        self.played_black = card[1].encode('ascii', 'ignore')
        self.sendmessage('', self.main_chan, self.played_black)
        

    def show_hand(self, username):
        for x in self.players:
            if x.name == username:
                player = x.name
                msg = ''
                for i in x.hand:
                    player_card = "%d - %s\n" %(i[0], i[1])
                    msg = msg + player_card                        
        self.msg(player, msg)


    def construct_sentence(self, black, white):
        pc = []
        for x in white:
            if x[1][len(x[1])-1] == ".":
                pc.append(x[1][:-1])
            else:
                pc.append(x[1])            
        if "____" in black:
            msg = ''
            black = black.split("____")
            for x in range(len(pc)):
                msg = msg+black[x]+pc[x]
            msg = msg + black[len(black)-1]
            return msg
        else:
            msg = black + " " + pc[0]
            return msg
        
                    

    def next_round(self):
            try:
                self.current_dealer = self.current_dealer + 1
                self.players[self.current_dealer-1].dealer = False
                self.players[self.current_dealer].dealer = True
            except:
                self.current_dealer = 0
                self.players[self.current_dealer].dealer = True
            msg = "%s <- NEW CARD CZAR, ALL HAIL THE CARD CZAR" %self.players[self.current_dealer].name
            self.sendmessage('', self.main_chan, msg)
            self.vote_count = 0
            self.draw_black()
            if self.rando:
                self.rando_plays()

    def haiku(self, channel):
        my_haiku = []
        msg = ''
        for x in range(0, 3):
            key = randint(1, len(self.white_cards)-1)
            print key
            #while key not in self.white_cards:
                #key = randint(1, len(self.white_cards)-1)
            card = self.white_cards[key][1]
            print card
            card = card.encode('ascii', 'ignore')
            msg = msg+card+" \ "
        msg = msg[:-2]
        self.msg(channel, msg)

        

    def rando_plays(self):
        randos_cards = []
        for x in range(0, self.draw):
            key = randint(1, len(self.white_cards)-1)
            print key
            #while key not in self.white_cards:
                #key = randint(1, len(self.white_cards)-1)
            card = self.white_cards[key][1]
            print card
            card = card.encode('ascii', 'ignore')
            card = (key, card, 'Rando')
            randos_cards.append(card)
            del self.white_cards[key]
        msg = self.construct_sentence(self.played_black, randos_cards)
        self.played_white.append((len(self.played_white), msg, 'Rando'))
            

    def deal_cards(self, count, who):
        for x in who:
            print x.name
            msg = ''
            for i in range(0, count):
                key = randint(1, len(self.white_cards)-1)
##                #while key not in self.white_cards:
                    #key = randint(1, len(self.white_cards)-1)
                card = self.white_cards[key]
                print card
                card = (int(card[0]), card[1].encode('ascii', 'ignore'))
                dealt_card = "%d - %s\n" %(card[0], card[1])
                msg = msg + dealt_card
                del self.white_cards[key]
                x.hand[card[0]] = card[1]
            self.sendmessage(x.name, x.name, msg)

    def add_player(self, username, channel):
        print "adding" + username
        for x in self.players:
            if x.name == username:
                msg = "%s is already playing!" %username
                self.sendmessage('', channel, msg)
                return
            
        x = Player(username)
        self.players.append(x)
        msg = "%s added to game." %username
        self.msg(channel, msg)
        msg = "Once the game starts, type !hand to see hand, or enter card number to play."
        self.msg(username, msg)
            

    def remove_player(self, player, channel):
        print player
        for x in self.players:
            if x.name.lower() == player.lower():
                print x.name
                print player
                self.players.remove(x)
                msg = "%s removed from the game." %player
                self.sendmessage('', self.main_chan, msg)
        


    def setup(self):
        self.played_white = []
        self.rando_score = 0
        conn = sqlite3.connect(db)
        cur = conn.execute('SELECT * FROM black')
        if self.multi_only:
            for x in cur:
                if x[3] > 1:
                    self.black_cards.append(x)
        else:
            for x in cur:
                self.black_cards.append(x)
        print len(self.black_cards)
        cur = conn.execute('SELECT * FROM white')
        for x in cur:
            self.white_cards.append(x)
        print len(self.white_cards)
        conn.close()
        for x in self.players:
            x.hand = {}
            x.score = 0
            x.dealer = False
            
            
    
        
class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self, channel, nickname='CAHbot'):
        self.channel = channel
        self.nickname = nickname
        self.lineRate = 10

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)




if __name__ == "__main__":
    reactor.connectTCP(network, 6667, BotFactory(chan))
    reactor.run()
        
    
