from fuzzingbook.Grammars import is_valid_grammar,trim_grammar, opts, srange,Grammar
from fuzzingbook.GeneratorGrammarFuzzer import GeneratorGrammarFuzzer,ProbabilisticGeneratorGrammarFuzzer
import grammar
import random 
import string
from copy import deepcopy

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


    def fuzz_one_input(self) -> str:
       
        input = self.fuzz()
        
        return input

# fuzzer = Fuzzer()
# for _ in range(10000):
#     print(fuzzer.fuzz())