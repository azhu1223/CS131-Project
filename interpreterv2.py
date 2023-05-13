from bparser import BParser
from intbase import InterpreterBase, ErrorType
from classesv2 import ClassDefinition, ClassInstance, Value

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

        if not result:
            print("Parsing failed. There must have been a mismatched parenthesis.")

        self.__discover_all_classes_and_track_them(parsed_program)

        # for _, c in self.classes.items():
        #     c.print()

        obj = ClassInstance(self, InterpreterBase.MAIN_CLASS_DEF, self.classes[InterpreterBase.MAIN_CLASS_DEF])

        environment_stack = []

        main_object = Value(obj)

        self.call_function(environment_stack, main_object, InterpreterBase.MAIN_FUNC_DEF, [])

    # Before calling this function, must merge fields and other environment variables into a single dictionary. Must add a "me" key mapped to "self".
    def call_function(self, environment_stack, object, method_name, arguments_passed):
        obj = object.value

        environment_stack.append(obj.fields)
        
        return_value = obj.run_method(environment_stack, method_name, arguments_passed)
        
        environment_stack.pop()

        return return_value