from fuzzingbook.GeneratorGrammarFuzzer import GeneratorGrammarFuzzer,ProbabilisticGeneratorGrammarFuzzer
import grammar
import random 

class InitialStageFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar,start_symbol='<initial_stage>')

class BusyFuzzer(ProbabilisticGeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar, start_symbol = '<busy_stage>')

class PostStageFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar, start_symbol = '<post_stage>')  
            
class MISCFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar,start_symbol='<misc>')

class BruteForceFuzzer(GeneratorGrammarFuzzer):
    def __init__(self):
        super().__init__(grammar = grammar.grammar,start_symbol='<brute_force_stage>')



class Fuzzer:
    def __init__(self):
        # This function must not be changed.
        self.grammar = grammar.grammar
        self.round = 0
        self.counter = 0
        self.stage = 'initial'
        self.running_fuzzer = None

        self.setup_fuzzer()
    def setup_fuzzer(self):
        # This function may be changed.
        random.seed()
        self.initial_fuzzer = InitialStageFuzzer()
        self.busy_fuzzer = BusyFuzzer()
        self.post_fuzzer = PostStageFuzzer()
        self.misc_fuzzer = MISCFuzzer()
        self.brute_fuzzer = BruteForceFuzzer()
        print(f"entering into round {self.round}!")

    def fuzz(self):
        if self.round <= 3:
            if self.counter < 3000:
                if self.stage == 'initial':
                    print("intial stage")
                    self.stage = 'busy'
                self.running_fuzzer = self.initial_fuzzer
            elif self.counter >= 3000 and self.counter < 8000:
                if self.stage == 'busy':
                    print("busy stage")
                    self.stage = 'post'
                self.running_fuzzer = self.busy_fuzzer
            elif self.counter >= 8000 and self.counter < 10000:
                    if self.stage == 'post':
                        print("post stage")
                        self.stage = 'initial'
                    self.running_fuzzer = self.post_fuzzer
        elif self.round > 3:

            if self.counter < 3000:
                if self.stage == 'initial':
                    print("brute force stage")  
                    self.stage = 'brute'
                self.running_fuzzer = self.brute_fuzzer
            elif self.counter >= 3000:
                if self.stage == 'brute':
                    print("misc stage ")  
                    self.stage = 'initial'  

                self.running_fuzzer = self.misc_fuzzer
        
        self.counter += 1

        def reset_database_state():
            print("reseting database state")
            grammar.VALID_INDEX = []
            grammar.VALID_TRIGGER = []
            grammar.VALID_VIEW = []
            grammar.VALID_TABLE = dict()


        if self.counter % 10000 == 0:
            self.counter = 0
            self.round += 1
            self.round = self.round % 5
            self.stage = 'initial'
            # reset_database_state()
            print(f"entering into round {self.round}!")
    
        input = self.running_fuzzer.fuzz() + '; '
        
        return input

    def fuzz_one_input(self) -> str:
        try:
        	input = self.fuzz()
        except:
        	input = ";"

        return input


