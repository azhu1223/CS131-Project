from bparser import BParser
from intbase import InterpreterBase, ErrorType
from classes import ClassDefinition, ClassInstance, Type, Value

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.classes = {}

    def __discover_all_classes_and_track_them(self, parsed_program):
        for c in parsed_program:
            if c[0] == InterpreterBase.CLASS_DEF:
                # print(f"Detected class {c[1]}. Adding to dictionary.")
                if c[1] in self.classes.keys():
                    self.error(ErrorType.TYPE_ERROR)
                self.classes[c[1]] = ClassDefinition(c[1], c[2:], self)
    
    def run(self, program):
        result, parsed_program = BParser.parse(program)
        if result == True:
            print(parsed_program)
        else:
            print("Parsing failed. There must have been a mismatched parenthesis.")

        self.__discover_all_classes_and_track_them(parsed_program)

        # for _, c in self.classes.items():
        #     c.print()

        obj = ClassInstance(self, "main", self.classes["main"])
        obj.run_method("main")

    # Before calling this function, must merge fields and other environment variables into a single dictionary. Must add a "me" key mapped to "self".
    def call_function(self, object, method_name, arguments_passed):
        return object.value.run_method(method_name, arguments_passed)