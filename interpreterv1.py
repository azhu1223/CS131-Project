from bparser import BParser
from intbase import InterpreterBase

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)

def main():
    program_source = ['(class main (method main () (print "hello world!")))']
    
    result, parsed_program = BParser.parse(program_source)
    if result == True:
        print(parsed_program)
    else:
        print("Parsing failed. There must have been a mismatched parenthesis.")

if __name__ == "__main__":
    main()