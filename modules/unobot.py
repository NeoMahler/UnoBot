# -*- coding: cp1252 -*-
import random
from datetime import datetime, timedelta
import time

random.seed()

away_last = 0

# Remember to change these 3 lines or nothing will work
CHANNEL = '#CatBots'
SCOREFILE = "unoscores.txt"
# Only the owner (starter of the game) can call .unostop to stop the game.
# But this calls for a way to allow others to stop it after the game has been idle for a while.
# After this set time, anyone can stop the game via .unostop
# Set the time ___in minutes___ here: (default is 5 mins)
INACTIVE_TIMEOUT = 3

STRINGS = {
    'ALREADY_STARTED': u'\x0300,01%s ja ha iniciat el joc. Escriu ".ujoin" per jugar!',
    'GAME_STARTED': u'\x0300,01%s ha iniciat el joc de l\'UNO - Escriu ".ujoin" per jugar!',
    'GAME_STOPPED': u'\x0300,01Joc aturat.',
    'CANT_STOP': u'\x0300,01Nom�s el propietari del joc (%s) pot aturar el joc, tu no el pots aturar! Per aturar el joc de manera forcada, espera %s segons.',
    'DEALING_IN': u'\x0300,01El jugador %s ha entrat al joc en la posici� n�m. %s!',
    'JOINED': u'\x0300,01El jugador %s ha entrat al joc en la posici� n�m. %s!',
    'ALREADY_JOINED': u'\x0300,01El jugador %s ja ha entrat, en la posici� %s!',
    'ENOUGH': u'\x0300,01Ja hi han suficients jugadors. Escriu ".deal" per iniciar el joc!',
    'NOT_STARTED': u'\x0300,01El joc no s\'ha iniciat. Escriu ".uno" per iniciar-lo!',
    'NOT_ENOUGH': u'\x0300,01No hi han suficients jugadors per repartir les cartes.',
    'NEEDS_TO_DEAL': u'\x0300,01%s ha de repartir.',
    'ALREADY_DEALT': u'\x0300,01Ja s\'han repartit les cartes.',
    'ON_TURN': u'\x0300,01�s el torn de %s.',
    'DONT_HAVE': u'\x0300,01No tens aquesta carta, %s',
    'DOESNT_PLAY': u'\x0300,01No pots jugar aquesta carta, %s',
    'UNO': u'\x0300,01UNO! %s t� nom�s una carta!',
    'WIN': u'\x0300,01Ja tenim un guanyador! %s!!!! Aquest joc ha durat %s',
    'DRAWN_ALREADY': u'\x0300,01Ja has agafat una carta. Pots .pass o .play!',
    'DRAWS': u'\x0300,01%s agafa una carta',
    'DRAWN_CARD': u'\x0300,01Has agafat la carta %s',
    'DRAW_FIRST': u'\x0300,01%s, abans has d\'agafar!',
    'PASSED': u'\x0300,01%s ha passat!',
    'NO_SCORES': u'\x0300,01Encara no hi han puntuacions',
    'TOP_CARD': u'\x0300,01Torn de %s. Carta de sobre de la pila: %s',
    'YOUR_CARDS': u'\x0300,01Les teves cartes: %s',
    'NEXT_START': u'\x0300,01Seg�ent: ',
    'NEXT_PLAYER': u'\x0300,01%s (%s cartes)',
    'D2': u'\x0300,01%s agafa dues cartes i passa!',
    'CARDS': u'\x0300,01Cartes: %s',
    'WD4': u'\x0300,01%s agafa quatre cartes i passa!',
    'SKIPPED': u'\x0300,01%s passa!',
    'REVERSED': u'\x0300,01Ordre invertit!',
    'GAINS': u'\x0300,01%s gains %s points!',
    'SCORE_ROW': u'\x0300,01%s: #%s %s (%s punts, %s jocs, %s guanyats, %.2f punts per joc, %.2f percentatge de vict�ries)',
    'GAME_ALREADY_DEALT': u'\x0300,01Ja s\'han repartit les cartes. Espera a que s\'acabi.',
    'PLAYER_COLOR_ENABLED': u'\x0300,01Colors de les cartes \x0309,01activats\x0300,01! Format: <COLOR>/[<CARTA>].  Exemple: R/[D2] �s un +2 vermell. Escriu \'.uno-help\' per m�s ajuda.',
    'PLAYER_COLOR_DISABLED': u'\x0300,01Colors de les cartes \x0304,01desactivats\x0300,01.',
    'DISABLED_PCE': u'\x0300,01Els colors de les cartes estan \x0304,01desactivats\x0300,01 per %s. Per activar-los, \'.pce-on\'',
    'ENABLED_PCE': u'\x0300,01Els colors de les cartes estan \x0309,01activats\x0300,01 per %s. Per desactivar-los, \'.pce-off\'',
    'PCE_CLEARED': u'\x0300,01All players\' hand card color setting is reset by %s.',
    'PLAYER_LEAVES': u'\x0300,01El jugador %s ha marxat.',
    'OWNER_CHANGE': u'\x0300,01El propietari del joc, %s, ha marxat. El nou propietari �s %s.',
}

class UnoBot:
    def __init__(self):
        self.colored_card_nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'R', 'S', 'D2']
        self.special_scores = {'R' : 20, 'S' : 20, 'D2' : 20, 'W' : 50, 'WD4' : 50}
        self.colors = 'RGBY'
        self.special_cards = ['W', 'WD4']
        self.players = dict()
        self.owners = dict()
        self.players_pce = dict()  # Player color enabled hash table
        self.playerOrder = list()
        self.game_on = False
        self.currentPlayer = 0
        self.topCard = None
        self.way = 1
        self.drawn = False
        self.scoreFile = SCOREFILE
        self.deck = list()
        self.prescores = list()
        self.dealt = False
        self.lastActive = datetime.now()
        self.timeout = timedelta(minutes=INACTIVE_TIMEOUT)

    def start(self, phenny, owner):
        owner = owner.lower()
        if self.game_on:
            phenny.msg(CHANNEL, STRINGS['ALREADY_STARTED'] % self.game_on)
        else:
            self.lastActive = datetime.now()
            self.game_on = owner
            self.deck = list()
            phenny.msg(CHANNEL, STRINGS['GAME_STARTED'] % owner)
            self.players = dict()
            self.players[owner] = list()
            self.playerOrder = [owner]
            phenny.msg(CHANNEL, STRINGS['JOINED'] % (owner, self.playerOrder.index(owner) + 1))
            if self.players_pce.get(owner, 0):
                phenny.notice(owner, STRINGS['ENABLED_PCE'] % owner)

    def stop(self, phenny, input):
        nickk = (input.nick).lower()
        tmptime = datetime.now()
        if nickk == self.game_on or tmptime - self.lastActive > self.timeout:
            phenny.msg(CHANNEL, STRINGS['GAME_STOPPED'])
            self.game_on = False
            self.dealt = False
        elif self.game_on:
            phenny.msg(CHANNEL, STRINGS['CANT_STOP'] % (self.game_on, self.timeout.seconds - (tmptime - self.lastActive).seconds))

    def join(self, phenny, input):
        #print dir(phenny.bot)
        #print dir(input)
        nickk = (input.nick).lower()
        if self.game_on:
            if not self.dealt:
                if nickk not in self.players:
                    self.players[nickk] = list()
                    self.playerOrder.append(nickk)
                    self.lastActive = datetime.now()
                    if self.players_pce.get(nickk, 0):
                        phenny.notice(nickk, STRINGS['ENABLED_PCE'] % nickk)
                    if self.deck:
                        for i in xrange(0, 7):
                            self.players[nickk].append(self.getCard())
                        phenny.msg(CHANNEL, STRINGS['DEALING_IN'] % (nickk, self.playerOrder.index(nickk) + 1))
                    else:
                        phenny.msg(CHANNEL, STRINGS['JOINED'] % (nickk, self.playerOrder.index(nickk) + 1))
                        if len (self.players) == 2:
                            phenny.msg(CHANNEL, STRINGS['ENOUGH'])
                else:
                    phenny.msg(CHANNEL, STRINGS['ALREADY_JOINED'] % (nickk, self.playerOrder.index(nickk) + 1))
            else:
                phenny.msg(CHANNEL, STRINGS['GAME_ALREADY_DEALT'])
        else:
            phenny.msg(CHANNEL, STRINGS['NOT_STARTED'])

    def deal(self, phenny, input):
        nickk = (input.nick).lower()
        if not self.game_on:
            phenny.msg(CHANNEL, STRINGS['NOT_STARTED'])
            return
        if len(self.players) < 2:
            phenny.msg(CHANNEL, STRINGS['NOT_ENOUGH'])
            return
        if nickk != self.game_on:
            phenny.msg(CHANNEL, STRINGS['NEEDS_TO_DEAL'] % self.game_on)
            return
        if len(self.deck):
            phenny.msg(CHANNEL, STRINGS['ALREADY_DEALT'])
            return
        self.startTime = datetime.now()
        self.lastActive = datetime.now()
        self.deck = self.createnewdeck()
        for i in xrange(0, 7):
            for p in self.players:
                self.players[p].append(self.getCard ())
        self.topCard = self.getCard()
        while self.topCard in ['R', 'S', 'D2', 'W', 'WD4']: self.topCard = self.getCard()
        self.currentPlayer = 1
        self.cardPlayed(phenny, self.topCard)
        self.showOnTurn(phenny)
        self.dealt = True

    def play(self, phenny, input):
        nickk = (input.nick).lower()
        if not self.game_on or not self.deck:
            return
        if nickk != self.playerOrder[self.currentPlayer]:
            phenny.msg(CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        tok = [z.strip() for z in str(input).upper().split(' ')]
        if len(tok) != 3:
            return
        searchcard = str()
        if tok[1] in self.special_cards and tok[2] in self.colors:
            searchcard = tok[1]
        elif tok[1] in self.colors:
            searchcard = (tok[1] + tok[2])
        else:
            phenny.msg(CHANNEL, STRINGS['DOESNT_PLAY'] % self.playerOrder[self.currentPlayer])
            return
        if searchcard not in self.players[self.playerOrder[self.currentPlayer]]:
            phenny.msg(CHANNEL, STRINGS['DONT_HAVE'] % self.playerOrder[self.currentPlayer])
            return
        playcard = (tok[1] + tok[2])
        if not self.cardPlayable(playcard):
            phenny.msg(CHANNEL, STRINGS['DOESNT_PLAY'] % self.playerOrder[self.currentPlayer])
            return

        self.drawn = False
        self.players[self.playerOrder[self.currentPlayer]].remove(searchcard)

        pl = self.currentPlayer

        self.incPlayer()
        self.cardPlayed(phenny, playcard)

        if len(self.players[self.playerOrder[pl]]) == 1:
            phenny.msg(CHANNEL, STRINGS['UNO'] % self.playerOrder[pl])
        elif len(self.players[self.playerOrder[pl]]) == 0:
            phenny.msg(CHANNEL, STRINGS['WIN'] % (self.playerOrder[pl], (datetime.now() - self.startTime)))
            self.gameEnded(phenny, self.playerOrder[pl])
            return

        self.lastActive = datetime.now()
        self.showOnTurn(phenny)

    def draw(self, phenny, input):
        nickk = (input.nick).lower()
        if not self.game_on or not self.deck:
            return
        if nickk != self.playerOrder[self.currentPlayer]:
            phenny.msg(CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        if self.drawn:
            phenny.msg(CHANNEL, STRINGS['DRAWN_ALREADY'])
            return
        self.drawn = True
        phenny.msg(CHANNEL, STRINGS['DRAWS'] % self.playerOrder[self.currentPlayer])
        c = self.getCard()
        self.players[self.playerOrder[self.currentPlayer]].append(c)
        self.lastActive = datetime.now()
        phenny.notice(nickk, STRINGS['DRAWN_CARD'] % self.renderCards (nickk, [c], 0))

    # this is not a typo, avoiding collision with Python's pass keyword
    def passs(self, phenny, input):
        nickk = (input.nick).lower()
        if not self.game_on or not self.deck:
            return
        if nickk != self.playerOrder[self.currentPlayer]:
            phenny.msg(CHANNEL, STRINGS['ON_TURN'] % self.playerOrder[self.currentPlayer])
            return
        if not self.drawn:
            phenny.msg(CHANNEL, STRINGS['DRAW_FIRST'] % self.playerOrder[self.currentPlayer])
            return
        self.drawn = False
        phenny.msg(CHANNEL, STRINGS['PASSED'] % self.playerOrder[self.currentPlayer])
        self.incPlayer()
        self.lastActive = datetime.now()
        self.showOnTurn(phenny)

    def top10(self, phenny, input):
        nickk = (input.nick).lower()
        self.rankings("ppg")
        i = 1
        for z in self.prescores[:10]:
            phenny.msg(nickk, STRINGS['SCORE_ROW'] % ('ppg', i, z[0], z[3], z[1], z[2], float(z[3])/float(z[1]), float(z[2])/float(z[1])*100))
            i += 1

    def createnewdeck(self):
        ret = list()
        for a in self.colored_card_nums:
            for b in self.colors:
                ret.append(b + a)
        for a in self.special_cards:
            ret.append(a)
            ret.append(a)

        if len(self.playerOrder) > 4:
            ret *= 2
            random.shuffle(ret)

        random.shuffle(ret)

        return ret

    def getCard(self):
        ret = self.deck[0]
        self.deck.pop(0)
        if not self.deck:
            self.deck = self.createnewdeck()
        return ret

    def showOnTurn(self, phenny):
        phenny.msg(CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))
        phenny.notice(self.playerOrder[self.currentPlayer], STRINGS['YOUR_CARDS'] % self.renderCards(self.playerOrder[self.currentPlayer], self.players[self.playerOrder[self.currentPlayer]], 0))
        msg = STRINGS['NEXT_START']
        tmp = self.currentPlayer + self.way
        if tmp == len(self.players):
            tmp = 0
        if tmp < 0:
            tmp = len(self.players) - 1
        arr = list()
        while tmp != self.currentPlayer:
            arr.append(STRINGS['NEXT_PLAYER'] % (self.playerOrder[tmp], len(self.players[self.playerOrder[tmp]])))
            tmp = tmp + self.way
            if tmp == len(self.players):
                tmp = 0
            if tmp < 0:
                tmp = len(self.players) - 1
        msg += ' - '.join(arr)
        phenny.notice(self.playerOrder[self.currentPlayer], msg)

    def showCards(self, phenny, user):
        user = user.lower()
        if not self.game_on or not self.deck:
            return
        msg = STRINGS['NEXT_START']
        tmp = self.currentPlayer + self.way
        if tmp == len(self.players):
            tmp = 0
        if tmp < 0:
            tmp = len(self.players) - 1
        arr = list()
        k = len(self.players)
        while k > 0:
            arr.append(STRINGS['NEXT_PLAYER'] % (self.playerOrder[tmp], len(self.players[self.playerOrder[tmp]])))
            tmp = tmp + self.way
            if tmp == len(self.players):
                tmp = 0
            if tmp < 0:
                tmp = len(self.players) - 1
            k-=1
        msg += ' - '.join(arr)
        if user not in self.players:
            phenny.notice(user, msg)
        else:
            phenny.notice(user, STRINGS['YOUR_CARDS'] % self.renderCards(user, self.players[user], 0))
            phenny.notice(user, msg)

    def renderCards(self, nick, cards, is_chan):
        nickk = nick
        if nick:
            nickk = (nick).lower()
        ret = list()
        for c in sorted(cards):
            if c in ['W', 'WD4']:
                sp = str()
                if not is_chan and self.players_pce.get(nickk, 0):
                    sp = ' '
                ret.append('\x0300,01[' + c + ']' + sp)
                continue
            if c[0] == 'W':
                c = c[-1] + '*'
            t = '\x0300,01\x03'
            if c[0] == 'B':
                t += '11,01'
            elif c[0] == 'Y':
                t += '08,01'
            elif c[0] == 'G':
                t += '09,01'
            elif c[0] == 'R':
                t += '04,01'
            if not is_chan:
                if self.players_pce.get(nickk, 0):
                    t += '%s/ [%s]  ' % (c[0], c[1:])
                else:
                    t += '[%s]' % c[1:]
            else:
                t += '(%s) [%s]' % (c[0], c[1:])
            t += "\x0300,01"
            ret.append(t)
        return ''.join(ret)

    def cardPlayable(self, card):
        if card[0] == 'W' and card[-1] in self.colors:
            return True
        if self.topCard[0] == 'W':
            return card[0] == self.topCard[-1]
        return (card[0] == self.topCard[0]) or (card[1] == self.topCard[1])

    def cardPlayed(self, phenny, card):
        if card[1:] == 'D2':
            phenny.msg(CHANNEL, STRINGS['D2'] % self.playerOrder[self.currentPlayer])
            z = [self.getCard(), self.getCard()]
            phenny.notice(self.playerOrder[self.currentPlayer], STRINGS['CARDS'] % self.renderCards(self.playerOrder[self.currentPlayer], z, 0))
            self.players[self.playerOrder[self.currentPlayer]].extend (z)
            self.incPlayer()
        elif card[:2] == 'WD':
            phenny.msg(CHANNEL, STRINGS['WD4'] % self.playerOrder[self.currentPlayer])
            z = [self.getCard(), self.getCard(), self.getCard(), self.getCard()]
            phenny.notice(self.playerOrder[self.currentPlayer], STRINGS['CARDS'] % self.renderCards(self.playerOrder[self.currentPlayer], z, 0))
            self.players[self.playerOrder[self.currentPlayer]].extend(z)
            self.incPlayer()
        elif card[1] == 'S':
            phenny.msg(CHANNEL, STRINGS['SKIPPED'] % self.playerOrder[self.currentPlayer])
            self.incPlayer()
        elif card[1] == 'R' and card[0] != 'W':
            phenny.msg(CHANNEL, STRINGS['REVERSED'])
            if len(self.players) > 2:
                self.way = -self.way
                self.incPlayer()
                self.incPlayer()
            else:
                self.incPlayer()
        self.topCard = card

    def gameEnded(self, phenny, winner):
        try:
            score = 0
            for p in self.players:
                for c in self.players[p]:
                    if c[0] == 'W':
                        score += self.special_scores[c]
                    elif c[1] in [ 'S', 'R', 'D' ]:
                        score += self.special_scores[c[1:]]
                    else:
                        score += int(c[1])
            phenny.msg(CHANNEL, STRINGS['GAINS'] % (winner, score))
            self.saveScores(self.players.keys(), winner, score, (datetime.now() - self.startTime).seconds)
        except Exception, e:
            print 'Score error: %s' % e
        self.players = dict()
        self.playerOrder = list()
        self.game_on = False
        self.currentPlayer = 0
        self.topCard = None
        self.way = 1
        self.dealt = False


    def incPlayer(self):
        self.currentPlayer = self.currentPlayer + self.way
        if self.currentPlayer == len(self.players):
            self.currentPlayer = 0
        if self.currentPlayer < 0:
            self.currentPlayer = len(self.players) - 1

    def saveScores(self, players, winner, score, time):
        from copy import copy
        prescores = dict()
        try:
            f = open(self.scoreFile, 'r')
            for l in f:
                t = l.replace('\n', '').split(' ')
                if len (t) < 4: continue
                if len (t) == 4: t.append(0)
                prescores[t[0]] = [t[0], int(t[1]), int(t[2]), int(t[3]), int(t[4])]
            f.close()
        except: pass
        for p in players:
            p = p.lower()
            if p not in prescores:
                prescores[p] = [ p, 0, 0, 0, 0 ]
            prescores[p][1] += 1
            prescores[p][4] += time
        prescores[winner][2] += 1
        prescores[winner][3] += score
        try:
            f = open(self.scoreFile, 'w')
            for p in prescores:
                f.write(' '.join ([str(s) for s in prescores[p]]) + '\n')
            f.close()
        except Exception, e:
            print 'Failed to write score file %s' % e

    # Custom added functions ============================================== #
    def rankings(self, rank_type):
        from copy import copy
        self.prescores = list()
        try:
            f = open(self.scoreFile, 'r')
            for l in f:
                t = l.replace('\n', '').split(' ')
                if len(t) < 4: continue
                self.prescores.append(copy (t))
                if len(t) == 4: t.append(0)
            f.close()
        except: pass
        if rank_type == "ppg":
            self.prescores = sorted(self.prescores, lambda x, y: cmp((y[1] != '0') and (float(y[3]) / int(y[1])) or 0, (x[1] != '0') and (float(x[3]) / int(x[1])) or 0))
        elif rank_type == "pw":
            self.prescores = sorted(self.prescores, lambda x, y: cmp((y[1] != '0') and (float(y[2]) / int(y[1])) or 0, (x[1] != '0') and (float(x[2]) / int(x[1])) or 0))

    def showTopCard_demand(self, phenny):
        if not self.game_on or not self.deck:
            return
        phenny.say(STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))

    def leave(self, phenny, input):
        nickk = (input.nick).lower()
        self.remove_player(phenny, nickk)

    def remove_player(self, phenny, nick):
        if not self.game_on:
            return

        user = self.players.get(nick, None)
        if user is not None:
            numPlayers = len(self.playerOrder)

            self.playerOrder.remove(nick)
            del self.players[nick]

            if self.way == 1 and self.currentPlayer == numPlayers - 1:
                self.currentPlayer = 0
            elif self.way == -1:
                if self.currentPlayer == 0:
                    self.currentPlayer = numPlayers - 2
                else:
                    self.currentPlayer -= 1

            phenny.msg(CHANNEL, STRINGS['PLAYER_LEAVES'] % nick)
            if numPlayers == 2 and self.dealt or numPlayers == 1:
                phenny.msg(CHANNEL, STRINGS['GAME_STOPPED'])
                self.game_on = None
                self.dealt = None
                return

            if self.game_on == nick:
                self.game_on = self.playerOrder[0]
                phenny.msg(CHANNEL, STRINGS['OWNER_CHANGE'] % (nick, self.playerOrder[0]))

            if self.dealt:
                phenny.msg(CHANNEL, STRINGS['TOP_CARD'] % (self.playerOrder[self.currentPlayer], self.renderCards(None, [self.topCard], 1)))

    def enablePCE(self, phenny, nick):
        nickk = nick.lower()
        if not self.players_pce.get(nickk, 0):
            self.players_pce.update({ nickk : 1})
            phenny.notice(nickk, STRINGS['PLAYER_COLOR_ENABLED'])
        else:
            phenny.notice(nickk, STRINGS['ENABLED_PCE'] % nickk)

    def disablePCE(self, phenny, nick):
        nickk = nick.lower()
        if self.players_pce.get(nickk, 0):
            self.players_pce.update({ nickk : 0})
            phenny.notice(nickk, STRINGS['PLAYER_COLOR_DISABLED'])
        else:
            phenny.notice(nickk, STRINGS['DISABLED_PCE'] % nickk)

    def isPCEEnabled(self, phenny, nick):
        nickk = nick.lower()
        if not self.players_pce.get(nickk, 0):
            phenny.notice(nickk, STRINGS['DISABLED_PCE'] % nickk)
        else:
            phenny.notice(nickk, STRINGS['ENABLED_PCE'] % nickk)

    def PCEClear(self, phenny, nick):
        nickk = nick.lower()
        if not self.owners.get(nickk, 0):
            self.players_pce.clear()
            phenny.msg(CHANNEL, STRINGS['PCE_CLEARED'] % nickk)

    def unostat(self, phenny, input):
        text = input.group().lower().split()

        if len(text) != 3:
            phenny.reply("Invalid input for stats command. Try '.unostats ppg 10' to show the top 10 ranked by points per game. You can also show rankings by percent-wins 'pw'.")
            return

        if text[1] == "pw" or text[1] == "ppg":
            self.rankings(text[1])
            self.rank_assist(phenny, input, text[2], text[1])

        if not self.prescores:
            phenny.reply(STRINGS['NO_SCORES'])

    def rank_assist(self, phenny, input, nicknum, ranktype):
        nickk = (input.nick).lower()
        if nicknum.isdigit():
            i = 1
            s = int(nicknum)
            for z in self.prescores[:s]:
                phenny.msg(nickk, STRINGS['SCORE_ROW'] % (ranktype, i, z[0], z[3], z[1], z[2], float(z[3])/float(z[1]), float(z[2])/float(z[1])*100))
                i += 1
        else:
            j = 1
            t = str(nicknum)
            for y in self.prescores:
                if y[0] == t:
                    phenny.say(STRINGS['SCORE_ROW'] % (ranktype, j, y[0], y[3], y[1], y[2], float(y[3])/float(y[1]), float(y[2])/float(y[1])*100))
                j += 1

unobot = UnoBot ()

def uno(phenny, input):
    if input.sender != CHANNEL:
        phenny.reply("Please join %s to play uno!" % (CHANNEL))
    elif input.sender == CHANNEL:
        unobot.start(phenny, input.nick)
uno.commands = ['uno']
uno.priority = 'low'
uno.thread = False
uno.rate = 0

def unostop(phenny, input):
    if not (input.sender).startswith('#'):
        return
    unobot.stop(phenny, input)
unostop.commands = ['unostop']
unostop.priority = 'low'
unostop.thread = False
unostop.rate = 0

def join(phenny, input):
    if not (input.sender).startswith('#'):
        return
    if input.sender == CHANNEL:
        unobot.join(phenny, input)
join.commands = ['ujoin']
join.priority = 'low'
join.thread = False
join.rate = 0

def deal(phenny, input):
    if not (input.sender).startswith('#'):
        return
    unobot.deal(phenny, input)
deal.commands = ['deal']
deal.priority = 'low'
deal.thread = False
deal.rate = 0

def play(phenny, input):
    if not (input.sender).startswith('#'):
        return
    unobot.play(phenny, input)
play.commands = ['play', 'p']
play.priority = 'low'
play.thread = False
play.rate = 0

def draw(phenny, input):
    if not (input.sender).startswith('#'):
        return
    unobot.draw(phenny, input)
draw.commands = ['draw', 'd', 'dr']
draw.priority = 'low'
draw.thread = False
draw.rate = 0

def passs(phenny, input):
    if not (input.sender).startswith('#'):
        return
    unobot.passs(phenny, input)
passs.commands = ['pass', 'pa']
passs.priority = 'low'
passs.thread = False
passs.rate = 0

def unotop10(phenny, input):
    unobot.top10(phenny, input)
unotop10.commands = ['unotop10']
unotop10.priority = 'low'
unotop10.thread = False
unotop10.rate = 0

def show_user_cards(phenny, input):
    unobot.showCards(phenny, input.nick)
show_user_cards.commands = ['cards']
show_user_cards.priority = 'low'
show_user_cards.thread = False
show_user_cards.rate = 0

def top_card(phenny, input):
    if not (input.sender).startswith('#'):
        return
    unobot.showTopCard_demand(phenny)
top_card.commands = ['top']
top_card.priority = 'low'
top_card.thread = False
top_card.rate = 0

def leave(phenny, input):
    if not (input.sender).startswith('#'):
        return
    unobot.leave(phenny, input)
leave.commands = ['leave']
leave.priority = 'low'
leave.thread = False
leave.rate = 0

def remove_on_part(phenny, input):
    unobot.remove_player(phenny, (input.nick).lower())
remove_on_part.event = 'PART'
remove_on_part.rule = '.*'
remove_on_part.priority = 'low'
remove_on_part.thread = False
remove_on_part.rate = 0

def remove_on_quit(phenny, input):
    unobot.remove_player(phenny, (input.nick).lower())
remove_on_quit.event = 'QUIT'
remove_on_quit.rule = '.*'
remove_on_quit.priority = 'low'
remove_on_quit.thread = False
remove_on_quit.rate = 0

def remove_on_kick(phenny, input):
    unobot.remove_player(phenny, (input.group(2)).lower())
remove_on_kick.event = 'KICK'
remove_on_kick.rule = '.*'
remove_on_kick.priority = 'low'
remove_on_kick.thread = False
remove_on_kick.rate = 0

def remove_on_nickchg(phenny, input):
    unobot.remove_player(phenny, (input.nick).lower())
remove_on_nickchg.event = 'NICK'
remove_on_nickchg.rule = '.*'
remove_on_nickchg.priority = 'low'
remove_on_nickchg.thread = False
remove_on_nickchg.rate = 0

def unostats(phenny, input):
    unobot.unostat(phenny, input)
unostats.commands = ['unostats']
unostats.priority = 'low'
unostats.thread = False
unostats.rate = 0

def uno_help(phenny, input):
    nick = input.group(2)
    txt = 'For rules, examples, and getting started: https://j.mp/esl47K'
    if nick:
        nick = (nick).strip()
        output = "%s: %s" % (nick, txt)
    else:
        output = txt
    phenny.say(output)
uno_help.commands = ['uno-help', 'unohelp']
uno_help.priority = 'low'
uno_help.thread = False
uno_help.rate = 0

def uno_pce_on(phenny, input):
    unobot.enablePCE(phenny, input.nick)
uno_pce_on.commands = ['pce-on']
uno_pce_on.priority = 'low'
uno_pce_on.thread = False
uno_pce_on.rate = 0

def uno_pce_off(phenny, input):
    unobot.disablePCE(phenny, input.nick)
uno_pce_off.commands = ['pce-off']
uno_pce_off.priority = 'low'
uno_pce_off.thread = False
uno_pce_off.rate = 0

def uno_ispce(phenny, input):
    unobot.isPCEEnabled(phenny, input.nick)
uno_ispce.commands = ['pce']
uno_ispce.priority = 'low'
uno_ispce.thread = False
uno_ispce.rate = 0

def uno_pce_clear(phenny, input):
    unobot.PCEClear(phenny, input.nick)
uno_pce_clear.commands = ['.pce-clear']
uno_pce_clear.priority = 'low'
uno_pce_clear.thread = False
uno_pce_clear.rate = 0

user_triggered = False

def uno_names(phenny, input, override=False):
    if not input.admin:
       return
    global away_last
    global user_triggered
    if input.sender != CHANNEL:
        return phenny.reply('Try: "/ctcp %s ping" or simply "%s!"' % (phenny.nick, phenny.nick))
    if time.time() - away_last < 480 and not override:
        phenny.notice(input.nick, u'Aquesta ordre t� un �s limitat.')
        return
    away_last = time.time()

    if input.sender != CHANNEL:
        return
    phenny.say(['NAMES'], CHANNEL, raw=False)
    user_triggered = True
uno_names.commands = ['ping']

def uno_get_names(phenny, input):
    global user_triggered
    incoming = input.args
    if incoming and len(incoming) >= 2 and incoming[2] != CHANNEL:
        return
    txt = input.group()
    txt = txt.replace('+', '')
    txt = txt.replace('@', '')
    names = txt.split()
    new_list = list()
    away_list = load_away()
    for x in names:
        if x not in away_list:
            new_list.append(x)
    new_list.remove(phenny.config.nick)
    new_list.sort()
    final_string = ', '.join(new_list)
    if user_triggered:
        phenny.write(['PRIVMSG ' + CHANNEL], 'PING! ' + final_string,
                raw=True)
    user_triggered = False
uno_get_names.event = '353'
uno_get_names.rule = '.*'

def load_away():
    try:
        f = open('uno_away.txt', 'r')
        lines = f.readlines()
        f.close()
    except:
        f = open('uno_away.txt', 'w')
        f.write('ChanServ\n')
        f.close()
        lines = ['ChanServ']
    return [x.strip() for x in lines]

def save_away(phenny, aways):
    f = open('uno_away.txt', 'w')
    for nick in aways:
        f.write(nick)
        f.write('\n')
    f.close()

def uno_away(phenny, input):
    if input.sender != CHANNEL:
        return
    nickk = input.nick
    away_list = load_away()
    if nickk in away_list:
        away_list.remove(nickk)
        save_away(phenny, away_list)
        phenny.reply('Estas marcat com a disponible!')
    else:
        away_list.append(nickk)
        save_away(phenny, away_list)
        phenny.reply('Estas marcat com a absent!')
    test_list = load_away()
uno_away.commands = ['away']
uno_away.rate = 0

def uno_ping_force(phenny, input):
    if input.admin:
        uno_names(phenny, input, True)
uno_ping_force.commands = ['fping']

if __name__ == '__main__':
    print __doc__.strip()
