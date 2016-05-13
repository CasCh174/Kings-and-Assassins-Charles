#!/usr/bin/env python3
# kingandassassins.py
# Author: Sébastien Combéfis
# Version: April 29, 2016

import argparse
import json
import random
import socket
import sys

from lib import game

BUFFER_SIZE = 2048

CARDS = (
    # (AP King, AP Knight, Fetter, AP Population/Assassins)
    (1, 6, True, 5),
    (1, 5, False, 4),
    (1, 6, True, 5),
    (1, 6, True, 5),
    (1, 5, True, 4),
    (1, 5, False, 4),
    (2, 7, False, 5),
    (2, 7, False, 4),
    (1, 6, True, 5),
    (1, 6, True, 5),
    (2, 7, False, 5),
    (2, 5, False, 4),
    (1, 5, True, 5),
    (1, 5, False, 4),
    (1, 5, False, 4)
)

POPULATION = {
    'monk', 'plumwoman', 'appleman', 'hooker', 'fishwoman', 'butcher',
    'blacksmith', 'shepherd', 'squire', 'carpenter', 'witchhunter', 'farmer'
}

BOARD = (
    ('R', 'R', 'R', 'R', 'R', 'G', 'G', 'R', 'R', 'R'),
    ('R', 'R', 'R', 'R', 'R', 'G', 'G', 'R', 'R', 'R'),
    ('R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'R'),
    ('R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'),
    ('R', 'G', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('G', 'G', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G')
)

# Coordinates of pawns on the board
KNIGHTS = {(1, 3), (3, 0), (7, 8), (8, 7), (8, 8), (8, 9), (9, 8)}
VILLAGERS = {
    (1, 7), (2, 1), (3, 4), (3, 6), (5, 2), (5, 5),
    (5, 7), (5, 9), (7, 1), (7, 5), (8, 3), (9, 5)
}

# Separate board containing the position of the pawns
PEOPLE = [[None for column in range(10)] for row in range(10)]

# Place the king in the right-bottom corner
PEOPLE[9][9] = 'king'

# Place the knights on the board
for coord in KNIGHTS:
    PEOPLE[coord[0]][coord[1]] = 'knight'

# Place the villagers on the board
# random.sample(A, len(A)) returns a list where the elements are shuffled
# this randomizes the position of the villagers
for villager, coord in zip(random.sample(POPULATION, len(POPULATION)), VILLAGERS):
    PEOPLE[coord[0]][coord[1]] = villager

KA_INITIAL_STATE = {
    'board': BOARD,
    'people': PEOPLE,
    'castle': [(2, 2, 'N'), (4, 1, 'W')],
    'card': None,
    'king': 'healthy',
    'lastopponentmove': [],
    'arrested': [],
    'killed': {
        'knights': 0,
        'assassins': 0
    }
}


class KingAndAssassinsState(game.GameState):
    '''Class representing a state for the King & Assassins game.'''

    DIRECTIONS = {
        'E': (0, 1),
        'W': (0, -1),
        'S': (1, 0),
        'N': (-1, 0)
    }

    def __init__(self, initialstate=KA_INITIAL_STATE):
        super().__init__(initialstate)

    def _nextfree(self, x, y, d):
        people = self._state['visible']['people']
        nx, ny = self._getcoord((x, y, d))
        ix, iy = nx, ny
        while 0 <= ix <= 9 and 0 <= iy <= 9 and people[ix][iy] is not None:
            # Must be a villager
            if people[ix][iy] not in POPULATION:
                return None
            # Cannot be a roof
            if (ix, iy) != (nx, ny) and BOARD[ix][iy] == 'R':
                return None
            ix, iy = self._getcoord((ix, iy, d))
        if 0 <= ix <= 9 and 0 <= iy <= 9:
            return (ix, iy)
        return None

    def update(self, moves, player):
        visible = self._state['visible']
        hidden = self._state['hidden']
        people = visible['people']
        for move in moves:
            print(move)
            # ('move', x, y, dir): moves person at position (x,y) of one cell in direction dir
            if move[0] == 'move':
                x, y, d = int(move[1]), int(move[2]), move[3]
                p = people[x][y]
                if p is None:
                    raise game.InvalidMoveException('{}: there is no one to move'.format(move))
                nx, ny = self._getcoord((x, y, d))
                new = people[nx][ny]
                # King, assassins, villagers can only move on a free cell
                if p != 'knight' and new is not None:
                    raise game.InvalidMoveException('{}: cannot move on a cell that is not free'.format(move))
                if p == 'king' and BOARD[nx][ny] == 'R':
                    raise game.InvalidMoveException('{}: the king cannot move on a roof'.format(move))
                if p in {'assassin'} or p in POPULATION and player != 0:
                    raise game.InvalidMoveException('{}: villagers and assassins can only be moved by player 0'.format(move))
                if p in {'king', 'knight'} and player != 1:
                    raise game.InvalidMoveException('{}: the king and knights can only be moved by player 1'.format(move))
                # Move granted if cell is free
                if new is None:
                    people[x][y], people[nx][ny] = people[nx][ny], people[x][y]
                # If cell is not free, check if the knight can push villagers
                else:
                    nf = self._nextfree((x, y, d))
                    if nf is None:
                        raise game.InvalidMoveException('{}: cannot move-and-push in the given direction'.format(move))
                    nfx, nfy = nf
                    while (nfx, nfy) != (x, y):
                        px, py = self._getcoord((nfx, nfx, {'E': 'W', 'W': 'E', 'S': 'N', 'N': 'S'}[d]))
                        people[nfx][nfy] = people[px][py]
                        nfx, nfy = px, py
            # ('arrest', x, y, dir): arrests the villager in direction dir with knight at position (x, y)
            elif move[0] == 'arrest':
                if player != 1:
                    raise game.InvalidMoveException('arrest action only possible for player 1')
                x, y, d = int(move[1]), int(move[2]), move[3]
                arrester = people[x][y]
                if arrester != 'knight':
                    raise game.InvalidMoveException('{}: the attacker is not a knight'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target not in POPULATION:
                    raise game.InvalidMoveException('{}: only villagers can be arrested'.format(move))
                visible['arrested'].append(people[tx][ty])
                people[tx][ty] = None
            # ('kill', x, y, dir): kills the assassin/knight in direction dir with knight/assassin at position (x, y)
            elif move[0] == 'kill':
                x, y, d = int(move[1]), int(move[2]), move[3]
                killer = people[x][y]
                if killer == 'assassin' and player != 0:
                    raise game.InvalidMoveException('{}: kill action for assassin only possible for player 0'.format(move))
                if killer == 'knight' and player != 1:
                    raise game.InvalidMoveException('{}: kill action for knight only possible for player 1'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target is None:
                    raise game.InvalidMoveException('{}: there is no one to kill'.format(move))
                if killer == 'assassin' and target == 'knight':
                    visible['killed']['knights'] += 1
                    people[tx][tx] = None
                elif killer == 'knight' and target == 'assassin':
                    visible['killed']['assassins'] += 1
                    people[tx][tx] = None
                else:
                    raise game.InvalidMoveException('{}: forbidden kill'.format(move))
            # ('attack', x, y, dir): attacks the king in direction dir with assassin at position (x, y)
            elif move[0] == 'attack':
                if player != 0:
                    raise game.InvalidMoveException('attack action only possible for player 0')
                x, y, d = int(move[1]), int(move[2]), move[3]
                attacker = people[x][y]
                if attacker != 'assassin':
                    raise game.InvalidMoveException('{}: the attacker is not an assassin'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target != 'king':
                    raise game.InvalidMoveException('{}: only the king can be attacked'.format(move))
                visible['king'] = 'injured' if visible['king'] == 'healthy' else 'dead'
            # ('reveal', x, y): reveals villager at position (x,y) as an assassin
            elif move[0] == 'reveal':
                if player != 0:
                    raise game.InvalidMoveException('raise action only possible for player 0')
                x, y = int(move[1]), int(move[2])
                p = people[x][y]
                if p not in hidden['assassins']:
                    raise game.InvalidMoveException('{}: the specified villager is not an assassin'.format(move))
                people[x][y] = 'assassin'
        # If assassins' team just played, draw a new card
        if player == 0:
            visible['card'] = hidden['cards'].pop()

    def _getcoord(self, coord):
        return tuple(coord[i] + KingAndAssassinsState.DIRECTIONS[coord[2]][i] for i in range(2))

    def winner(self):
        visible = self._state['visible']
        hidden = self._state['hidden']
        # The king reached the castle
        for doors in visible['castle']:
            coord = self._getcoord(doors)
            if visible['people'][coord[0]][coord[1]] == 'king':
                return 1
        # The are no more cards
        if len(hidden['cards']) == 0:
            return 0
        # The king has been killed
        if visible['king'] == 'dead':
            return 0
        # All the assassins have been arrested or killed
        if visible['killed']['assassins'] + len(set(visible['arrested']) & hidden['assassins']) == 3:
            return 1
        return -1

    def isinitial(self):
        return self._state['hidden']['assassins'] is None
    
    def setassassins(self, assassins):
        self._state['hidden']['assassins'] = set(assassins)

    def prettyprint(self):
        visible = self._state['visible']
        hidden = self._state['hidden']
        result = ''
        if hidden is not None:
            result += '   - Assassins: {}\n'.format(hidden['assassins'])
            result += '   - Remaining cards: {}\n'.format(len(hidden['cards']))
        result += '   - Current card: {}\n'.format(visible['card'])
        result += '   - King: {}\n'.format(visible['king'])
        result += '   - People:\n'
        result += '   +{}\n'.format('----+' * 10)
        for i in range(10):
            result += '   | {} |\n'.format(' | '.join(['  ' if e is None else e[0:2] for e in visible['people'][i]]))
            result += '   +{}\n'.format(''.join(['----+' if e == 'G' else '^^^^+' for e in visible['board'][i]]))
        print(result)

    @classmethod
    def buffersize(cls):
        return BUFFER_SIZE


class KingAndAssassinsServer(game.GameServer):
    '''Class representing a server for the King & Assassins game'''

    def __init__(self, verbose=False):
        super().__init__('King & Assassins', 2, KingAndAssassinsState(), verbose=verbose)
        self._state._state['hidden'] = {
            'assassins': None,
            'cards': random.sample(CARDS, len(CARDS))
        }

    def _setassassins(self, move):
        state = self._state
        if 'assassins' not in move:
            raise game.InvalidMoveException('The dictionary must contain an "assassins" key')
        if not isinstance(move['assassins'], list):
            raise game.InvalidMoveException('The value of the "assassins" key must be a list')
        for assassin in move['assassins']:
            if not isinstance(assassin, str):
                raise game.InvalidMoveException('The "assassins" must be identified by their name')
            if not assassin in POPULATION:
                raise game.InvalidMoveException('Unknown villager: {}'.format(assassin))
        state.setassassins(move['assassins'])
        state.update([], 0)

    def applymove(self, move):
        try:
            state = self._state
            move = json.loads(move)
            if state.isinitial():
                self._setassassins(move)
            else:
                self._state.update(move['actions'], self.currentplayer)
        except game.InvalidMoveException as e:
            raise e
        except Exception as e:
            print(e)
            raise game.InvalidMoveException('A valid move must be a dictionary')


class KingAndAssassinsClient(game.GameClient):
    '''Class representing a client for the King & Assassins game'''

    def __init__(self, name, server, verbose=False):
        super().__init__(server, KingAndAssassinsState, verbose=verbose)
        self.__name = name

    def _handle(self, message):
        pass

    def strat_roi(self,state):
        self.depl={'action':[],'PA_caval':self.state['card'][1]}     
        if self.pos_roi(self.state)[0]==9 and self.pos_roi(self.state)[1]==9:   #au premier coup mise en place de la stratégie
            self.depl['action'].append(('move',9,8,'W'))
            self.depl['action'].append(('move',9,9,'W'))
            self.depl['action'].append(('move',8,9,'S'))
            self.depl['action'].append(('move',8,7,'N'))
            self.depl['PA_caval']-=2
        else:       #deplacement horizontal du roi et puis vertical
            if self.pos_roi(self.state)[1]==2:  #si le roi est dans la deuxieme colonne, deplacement vers le nord
                self.deplacement_groupe(state,'N')
                if self.state['card'][0]==2:
                    self.deplacement_groupe(state,'N')
            else:   #sinon deplacement vers l ouest
                self.deplacement_groupe(state,'W')
                if self.state['card'][0]==2 and self.pos_roi(self.state)[1]!=3 and self.depl['PA_caval']>=4:
                    self.deplacement_groupe(state,'W')        
        return self.depl['action']

    def deplacement_groupe (self,state,ori):
        if self.ref_roi(state,'W','pion') == 'knight':
            self.ref_roi(state,'W','deplacement',ori)
            self.depl['PA_caval']-=1 #pas besoin de prendre en compte les toits (en tout cas pour le deplacement horizontal), car toujours assez de PA
        if self.ref_roi(state,'N','pion') == 'knight':
            self.ref_roi(state,'N','deplacement',ori)
            self.depl['PA_caval']-=1
        self.depl['action'].append(('move',self.pos_roi(self.state)[0],self.pos_roi(self.state)[1],ori))
        if self.ref_roi(state,'E','pion') == 'knight':
            self.ref_roi(state,'E','deplacement',ori)
            self.depl['PA_caval']-=1

    def ref_roi(self, state, direction_pion, demande, direction_deplacement=''):
        if direction_pion == 'N':
            x_corr,y_corr=0,-1
        elif direction_pion == 'E':
            x_corr,y_corr=1,0
        elif direction_pion == 'S':
            x_corr,y_corr=0,1
        else:
            x_corr,y_corr=-1,0
        if demande == 'pion':
            pion=self.state['people'][self.pos_roi(self.state)[0]+y_corr][self.pos_roi(self.state)[1]+x_corr]
            return pion
        if demande == 'deplacement':
            deplacement=self.depl['action'].append(('move',self.pos_roi(self.state)[0]+y_corr,self.pos_roi(self.state)[1]+x_corr,direction_deplacement))
            return deplacement
    
    def pos_roi(self,state):
        for num_ligne, listeligne in enumerate(self.state['people']):
            for colonne,pion in enumerate(listeligne):
                if pion == 'king':
                    position_roi=(num_ligne,colonne)
        return (position_roi)

    def strat_ass(self, state):
        self.strat={'action':[]}
        positions = [(3,0),(1,2),(0,2)]
        if self.state[people][postions[0][0]][postions[0][1]] not in POPULATION:
            if self.pos_vill(state,positions[0])[0]>positions[0][0]:
                self.strat['action'].append(('move',self.pos_vill(state,positions[0])[0],self.pos_vill(state,positions[0])[1],'N'))
            else if self.pos_vill(state,positions[0])[0]<positions[0][0]:
                self.strat['action'].append(('move',self.pos_vill(state,positions[0])[0],self.pos_vill(state,positions[0])[1],'S'))
            else if self.pos_vill(state,positions[0])[1]<positions[0][1]:
                self.strat['action'].append(('move',self.pos_vill(state,positions[0])[0],self.pos_vill(state,positions[0])[1],'E'))
            else
                self.strat['action'].append(('move',self.pos_vill(state,positions[0])[0],self.pos_vill(state,positions[0])[1],'W'))
        else if self.state[people][postions[1][0]][postions[1][1]] not in POPULATION:
            pass
        else if self.state[people][postions[0][0]][postions[0][1]] not in POPULATION:        
            pass
            

    def pos_vill(self,state,pos_fin):
        dist=100
        for num_ligne, listeligne in enumerate(self.state['people']):
            for colonne,pion in enumerate(listeligne):
                if distance((num_ligne,colonne),pos_fin)<dist:
                    postition_vill=num_ligne,colonne
        return position_vill

    def distance(self,pos_pion,pos_but):
        x,y=pos_pion
        nx,ny=pos_but
        x_dist=x-nx
        y_dist=y-ny
        if x_dist<0:
            x_dist=-x_dist
        if y_dist<0:
            y_dist=-y_dist
        return x_dist+y_dist

    def _nextmove(self, state):
        # Two possible situations:
        # - If the player is the first to play, it has to select his/her assassins
        #   The move is a dictionary with a key 'assassins' whose value is a list of villagers' names
        # - Otherwise, it has to choose a sequence of actions
        #   The possible actions are:
        #   ('move', x, y, dir): moves person at position (x,y) of one cell in direction dir
        #   ('arrest', x, y, dir): arrests the villager in direction dir with knight at position (x, y)
        #   ('kill', x, y, dir): kills the assassin/knight in direction dir with knight/assassin at position (x, y)
        #   ('attack', x, y, dir): attacks the king in direction dir with assassin at position (x, y)
        #   ('reveal', x, y): reveals villager at position (x,y) as an assassin
        self.state = state._state['visible']
        if self.state['card'] is None:
            return json.dumps({'assassins': ['monk', 'hooker', 'fishwoman']}, separators=(',', ':'))
        else:
            if self._playernb == 0:
                for i in range(10):
                    for j in range(10):
                        if self.state['people'][i][j] in {'monk', 'hooker', 'fishwoman'}:
                            return json.dumps({'actions': [('reveal', i, j)]}, separators=(',', ':'))
                return json.dumps({'actions': self.strat_ass(self.state)}, separators=(',', ':'))
            else:
                return json.dumps({'actions': self.strat_roi(self.state)}, separators=(',', ':'))


if __name__ == '__main__':
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='King & Assassins game')
    subparsers = parser.add_subparsers(
        description='server client',
        help='King & Assassins game components',
        dest='component'
    )

    # Create the parser for the 'server' subcommand
    server_parser = subparsers.add_parser('server', help='launch a server')
    server_parser.add_argument('--host', help='hostname (default: localhost)', default='localhost')
    server_parser.add_argument('--port', help='port to listen on (default: 5000)', default=5000)
    server_parser.add_argument('-v', '--verbose', action='store_true')
    # Create the parser for the 'client' subcommand
    client_parser = subparsers.add_parser('client', help='launch a client')
    client_parser.add_argument('name', help='name of the player')
    client_parser.add_argument('--host', help='hostname of the server (default: localhost)',
                               default=socket.gethostbyname(socket.gethostname()))
    client_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    client_parser.add_argument('-v', '--verbose', action='store_true')
    # Parse the arguments of sys.args
    args = parser.parse_args()

    if args.component == 'server':
        KingAndAssassinsServer(verbose=args.verbose).run()
    else:
        KingAndAssassinsClient(args.name, (args.host, args.port), verbose=args.verbose)
        
