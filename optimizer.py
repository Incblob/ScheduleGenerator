import numpy as np
class SA_optimiser:
    slots = ('dates', 'actors', 'availabilities',)


    def __init__(self, requirements:np.ndarray, availabilities:np.ndarray) -> None:
        self.requirements = requirements
        self.availabilities = availabilities
        self.scene_index = [i for i in range(len(requirements[0]))]

    def train(self, iterations=1000):
        from random import random
        from math import exp
        temp = 100
        config = np.ones(self.availabilities.shape[1],dtype=np.int8)*-1
        # print(config)
        # print(self.requirements)
        loss = 0
        for i in range(0, iterations):
            if i%(iterations/5) ==0:
                print(f'loss for config {config} is {loss}, at prob {exp(+(-1)/temp)}') 
            new_config = self.make_move(config.copy())
            new_loss = self.calculate_loss(new_config)
            if new_loss > loss:
                config = new_config
                loss = new_loss
            elif exp(+(new_loss - loss)/temp)>random():
                config = new_config
                loss = new_loss
            temp *= 0.999
        return config

    @staticmethod
    def calculate_overlap(one_requirements:np.ndarray,one_availabilities:np.ndarray):
        return sum(one_requirements*one_availabilities)

    def calculate_loss(self,config)-> float:
        loss:float = 0
        for ind,cur_date in enumerate(config):
            if cur_date ==-1:
                loss -= 1
                continue
            
            loss +=  self.calculate_overlap(self.requirements[:,cur_date], self.availabilities[:,ind])
        return loss

    def make_move(self,config):
        from random import choice
        if any(x == -1 for x in config):
            return choice([self.move_add, self.move_remove, self.move_replace, self.move_swap])(config) 
        else:
            return choice([self.move_remove, self.move_replace, self.move_swap])(config) 
    
    def move_swap(self,config):
        from random import randint
        ind1 = randint(0,len(config)-1)
        ind2 = randint(0,len(config)-1)
        config[ind1], config[ind2]=config[ind2], config[ind1]
        return config

    def move_add(self,config):
        from random import choice
        if all(config!=-1):
            return config
        options=[i for i,v in enumerate(config) if v==-1]
        avail = self.filter_availabilities(config)
        if avail:
            config[choice(options)] = choice(avail)
        return config

    def move_remove(self,config):
        from random import choice
        if np.all(config==-1):
            return config
        config[choice([i for i,v in enumerate(config) if v!=-1])] = -1
        return config
    
    def move_replace(self,config):
        config = self.move_remove(config)
        config = self.move_add(config)
        return config

    def filter_availabilities(self,config):
        return [x for x in self.scene_index if x not in config]