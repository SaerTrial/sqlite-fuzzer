from fuzzingbook.Grammars import is_valid_grammar,trim_grammar, opts, srange,Grammar
from fuzzingbook.GeneratorGrammarFuzzer import GeneratorGrammarFuzzer,ProbabilisticGeneratorGrammarFuzzer
import grammar
import random 
import string
from copy import deepcopy






# TC_MAP: dict = {}
# def intialize_simple_tc_map():
#         for i in range(100):
#             val = random.randrange(1,10,1)
#             l = random.sample(string.ascii_lowercase,val)
#             TC_MAP['t' + str(i)] = tuple(l)

    


# class createTableSimpleFuzzer(ProbabilisticGeneratorGrammarFuzzer):
#     def __init__(self, update_create):
#         g = deepcopy(grammar.grammar)
#         for symbol in update_create:
#             g[symbol] = deepcopy(update_create[symbol])
#         super().__init__(trim_grammar(g), start_symbol = '<create_table_stmt>')

# class createTableSimpleFuzzerFactory():
   

        
#     def table_producer(self):
#         key = random.choice(list(TC_MAP.keys()))
#         column = TC_MAP[key]
#         return str(key) + '(' + ','.join(column) + ')'
    
#     def get_tc_map(self):
#         return TC_MAP
#     def initial_fuzzer(self):
#         update = {
#             '<create_table_stmt>' :[ "CREATE TABLE IF NOT EXISTS  <table_name_and_column_list>"], 
#             '<table_name_and_column_list>':[('t', opts(pre=self.table_producer))]
#         }
#         fuzzer = createTableSimpleFuzzer(update_create=update)
#         return fuzzer

        



# class InsertSimpleFuzzer(ProbabilisticGeneratorGrammarFuzzer):
#     def __init__(self, update_insert:dict):
#         g = deepcopy(grammar.grammar)
#         for symbol in update_insert:
#             g[symbol] = deepcopy(update_insert[symbol])
#         super().__init__(trim_grammar(g), start_symbol = '<insert_stmt>')



# class InsertSimpleFuzzerFactory():
        
#     def get_name(self):
#             name = random.choice(list(TC_MAP.keys()))
#             return name 
#     def get_digit(self,name:str):
#         val = len(TC_MAP[name])
#         l = random.sample(string.digits,val)
#         return '(' + ','.join(l) + ')'
#     def set_name_value(self):
#          name = random.choice(list(TC_MAP.keys()))
#          l = TC_MAP[name]
#          return 'INSERT INTO ' + str(name) + '(' + ','.join(l) + ')' + ' VALUES ' + self.get_digit(name)
#     def set_name_value_without_column(self):
#          name = random.choice(list(TC_MAP.keys()))
#          return 'INSERT INTO ' + str(name)  + ' VALUES ' + self.get_digit(name)

#     def initial_fuzzer(self):
            
#             update = {            
#             '<insert_stmt>':[(' INSERT INTO <table_name> VALUES<insert_stmt_6>', opts(pre=self.set_name_value_without_column)),
#                              ('INSERT INTO <table_name> (<column_name_list>) VALUES<insert_stmt_6>,', opts(pre=self.set_name_value))
#                              ],
 
#         }
#             fuzzer = InsertSimpleFuzzer(update)
#             return fuzzer


# class DropTableSimpleFuzzer(ProbabilisticGeneratorGrammarFuzzer):
#     def __init__(self, update_create):
#         g = deepcopy(grammar.grammar)
#         for symbol in update_create:
#             g[symbol] = deepcopy(update_create[symbol])
#         super().__init__(trim_grammar(g), start_symbol = '<drop_table_stmt>')

# class DropTableSimpleFuzzerFactory():
#     def delete_table(self):
#          name = random.choice(list(TC_MAP.keys()))
#          del TC_MAP[name]
#          return name
#     @staticmethod
#     def initial_fuzzer(self):
#         update = {
#            '<drop_table_stmt_2>':[ '', ('<database_name>', opts(pre=self.delete_table, prob = 0.995)) ],
#         }
#         fuzzer = createTableSimpleFuzzer(update_create=update)
#         return fuzzer


# class GeneralFuzzer(GeneratorGrammarFuzzer):
#     def __init__(self, update_create):
#         g = deepcopy(grammar.grammar)
#         for symbol in update_create:
#             g[symbol] = deepcopy(update_create[symbol])
#         super().__init__(grammar  = trim_grammar(g))

# class GeneralFuzzerFactory():
#     def select_table(self):
#          name = random.choice(list(TC_MAP.keys()))
#          return name
#     @staticmethod
#     def initial_fuzzer(self):
#         update = {
#            '<table_name>':[ self.select_table() ],
#         }
#         fuzzer = createTableSimpleFuzzer(update_create=update)
#         return fuzzer

class createTableFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar,start_symbol='<create_table_stmt>')

class pragmaFuzzer(ProbabilisticGeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar, start_symbol = '<pragma_stmt>')
class insertFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar, start_symbol = '<insert_stmt>')  
            

class selectFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar,start_symbol='<select_core>')

class expertFuzzer(selectFuzzer):
    def fuzz():
        s = super().fuzz()
        if random.choice([True,False]):
            return '.expert --verbose \n' + s 
        else:
            return '.expert --sample 70\n' + s
        
class generalFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar)

class testFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar, start_symbol = '<maybe_crash_stmt>')

class Fuzzer:
    def __init__(self):
        # This function must not be changed.
        self.grammar = grammar.grammar
        self.setup_fuzzer()
        self.counter = 0
    
    def setup_fuzzer(self):
        # This function may be changed.
        self.create_fuzzer = createTableFuzzer()
        self.insert_fuzzer = insertFuzzer()
        self.select_fuzzer = selectFuzzer()  # + [expertFuzzer() for _ in range(5)]
        self.general_fuzzer = generalFuzzer()
        # self.test_fuzzer  = testFuzzer()


    def fuzz(self):
        random.seed()
        
        if self.counter < 200:
            cur_fuzzer = self.create_fuzzer
        elif self.counter >= 200 and self.counter < 1000:
            cur_fuzzer = self.insert_fuzzer
        elif self.counter >= 1000 and self.counter < 5000:
            cur_fuzzer = self.select_fuzzer
        else:
            cur_fuzzer = self.general_fuzzer

        self.counter = self.counter + 1

        input = cur_fuzzer.fuzz() + '; '
        
        return input

        # if  self.counter % 5 == 0:
        #     return 'BEGIN;' + input
        # elif self.counter % 5 == 4:
        #     return input + 'COMMIT;'
        # elif self.counter > 90000:
        #     return 'ROLLBACK;'
        # else:
        #     return input
        
    

    def fuzz_one_input(self) -> str:
       
        input = self.fuzz()
        
        return input

# fuzzer = Fuzzer()
# for _ in range(10000):
#     print(fuzzer.fuzz())