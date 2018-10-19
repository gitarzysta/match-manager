
import os
import copy
import json
import shutil
import skills
from skills import trueskill
from subprocess import Popen, PIPE, call

record_dir = "replays"

def update_skills(players, ranks):
    """ Update player skills based on ranks from a match """
    teams = [skills.Team({player.name: skills.GaussianRating(player.mu, player.sigma)}) for player in players]
    match = skills.Match(teams, ranks)
    calc = trueskill.FactorGraphTrueSkillCalculator()
    game_info = trueskill.TrueSkillGameInfo()
    updated = calc.new_ratings(match, game_info)
    print ("Updating ranks")
    for team in updated:
        player_name, skill_data = next(iter(team.items()))    #in Halite, teams will always be a team of one player
        player = next(player for player in players if player.name == str(player_name))   #this suggests that players should be a dictionary instead of a list
        player.mu = skill_data.mean
        player.sigma = skill_data.stdev
        player.update_skill()
        print("skill = %4f  mu = %3f  sigma = %3f  name = %s" % (player.skill, player.mu, player.sigma, str(player_name)))

class Match:
    def __init__(self, players, width, height, seed, turn_limit, keep_replays, keep_logs):
        print("Seed = " + str(seed))
        self.map_seed = seed
        self.map_height = height
        self.map_width = width
        self.players = players
        self.paths = [player.path for player in players]
        self.finished = False
        self.results = [0 for _ in players]
        self.return_code = None
        self.results_string = ""
        self.replay_file = ""
        self.turn_limit = turn_limit
        self.total_time_limit = 1200 # 20 minutes may be too long
        self.timeouts = []
        self.num_players = len(players)
        self.keep_replay = keep_replays
        self.keep_logs = keep_logs
        self.parameters = None
        self.logs = None
        self.map_generator = None

    def __repr__(self):
        title1 = "Match between " + ", ".join([p.name for p in self.players]) + "\n"
        title2 = "Binaries are " + ", ".join(self.paths) + "\n"
        dims = "dimensions = " + str(self.map_width) + ", " + str(self.map_height) + "\n"
        results = "\n".join([str(i) + " " + j for i, j in zip(self.results, [p.name for p in self.players])]) + "\n"
        replay = self.replay_file + "\n" #\n"
        return title1 + title2 + dims + results + replay

    def get_command(self, halite_binary):
        dim_height = "--height " + str(self.map_height)
        dim_width = "--width " + str(self.map_width)
        turn_limit = "--turn-limit " + str(self.turn_limit)
        json = "--results-as-json"
        #seed = "-s " + str(self.map_seed)
        result = [halite_binary, dim_height, dim_width, json]
        return result + self.paths

    def run_match(self, halite_binary):
        command = self.get_command(halite_binary)
        print("Command = " + str(command))
        p = Popen(command, stdin=None, stdout=PIPE, stderr=None)
        results, _ = p.communicate(None, self.total_time_limit)
        self.results_string = results.decode('ascii')
        self.return_code = p.returncode
        self.parse_results_string()
        update_skills(self.players, copy.deepcopy(self.results))
        if self.keep_replay:
            print("Keeping replay\n")
            if not os.path.exists(record_dir):
                os.makedirs(record_dir)
            try:
                shutil.move(self.replay_file, record_dir)
                if self.replay_file.startswith('./'):
                    self.replay_file = self.replay_file[2:]
                self.replay_file = os.path.join(record_dir, self.replay_file)
            except Exception as e:
                print(e)
        else: 
            print("Deleting replay\n")
            os.remove(self.replay_file)

        if self.keep_logs:
            print("Keeping logs\n")
            if not os.path.exists(record_dir):
                os.makedirs(record_dir)
            try:
                for key, filename in self.logs.items():
                    shutil.move(filename, record_dir)
                    self.logs[key] = os.path.join(record_dir, filename)
            except Exception as e:
                print(e)
        else: 
            print("Deleting logs\n")
            for file in self.logs.values():
                os.remove(file)
#        self.fix_logs()

#    def fix_logs(self):
#        print("Fixing logs")
#        for index in range(0, self.num_players):
#            if not self.logs[index]:
#                self.logs[index] = None
#        print(self.logs)
        

    def parse_results_string(self):
        print ("parsing results a")
        data = json.loads(self.results_string)
        print ("parsing results b")
        self.logs = data['error_logs']
        print ("parsing results c")
        self.map_height = data['map_height']
        print ("parsing results d")
        self.map_width = data['map_width']
        print ("parsing results e")
        self.map_seed = data['map_seed']
        print ("parsing results f")
        self.map_generator = data['map_generator']
        print ("parsing results g")
        self.replay_file = data['replay']
        print ("parsing results h")
        stats = data['stats']
        print ("parsing results i")
        for player_index_string in stats:
            player_index = int(player_index_string)
            rank_string = stats[player_index_string]['rank']
            self.results[player_index] = int(rank_string)
