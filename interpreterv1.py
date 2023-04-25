from bparser import BParser
from intbase import InterpreterBase
from classes import *

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.classes = {}

    def __discover_all_classes_and_track_them(self, parsed_program):
        for c in parsed_program:
            if (c[0] == InterpreterBase.CLASS_DEF):
                # print(f"Detected class {c[1]}. Adding to dictionary.")
                self.classes[c[1]] = ClassDefinition(c[1], c[2:])
    
    def run(self, program):
        result, parsed_program = BParser.parse(program)
        if result == True:
            print(parsed_program)
        else:
            print("Parsing failed. There must have been a mismatched parenthesis.")

        self.__discover_all_classes_and_track_them(parsed_program)

        for _, c in self.classes.items():
            c.print()

        obj = ClassInstance(self, "main", self.classes["main"])
        obj.run_method("main")

    # Before calling this function, must merge fields and other environment variables into a single dictionary. Must add a "me" key with the class type.
    def call_function(self, obj, method_name, arguments, environment):
        object = environment[obj]

        resolved_arguments = []
        for argument in arguments:
            argument_type = Type.type(argument)

            if argument_type is not None:
                resolved_arguments.append(argument)
            else:
                resolved_arguments.append(environment[argument])

        object.run_method(method_name, resolved_arguments)


# def main():
#     program_source = ['(class main (field hello_world "hello world!") (method main () (print hello_world)))']
    
#     interpreter = Interpreter()

#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()