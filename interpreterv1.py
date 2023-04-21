from bparser import BParser
from intbase import InterpreterBase

class ClassField:
    # Pass in the list without the "field" part
    def __init__(self, declaration_list):
        self.name = declaration_list[0]
        self.value = declaration_list[1]

    def print(self):
        print(f"Field {self.name} equals {self.value}")

class ClassMethod:
    # Pass in the list without the "method" part
    def __init__(self, declaration_list):
        self.name = declaration_list[0]
        self.parameters = declaration_list[1]
        self.body = declaration_list[2]

    def print(self):
        print(f"Method {self.name}'s parameters are {self.parameters} and body is {self.body}")

class ClassDefinition:
    def __init__(self, name, declaration_list):
        self.name = name
        self.fields = {}
        self.methods = {}

        for declaration in declaration_list:
            if (declaration[0] == InterpreterBase.FIELD_DEF):
                self.fields[declaration[1]] = ClassField(declaration[1:])
            elif (declaration[0] == InterpreterBase.METHOD_DEF):
                self.methods[declaration[1]] = ClassMethod(declaration[1:])
            else:
                # TODO: Error
                None

    def print(self):
        print(f"Class {self.name}'s fields and methods are:")
        for _, field in self.fields.items():
            field.print()
        for _, method in self.methods.items():
            method.print()

class ClassInstance:
    def __init__(self, interpreter, name, class_type):
        self.interpreter = interpreter
        self.name = name
        self.class_type = class_type
        self.fields = {}
        self.methods = {}

        for key, value in self.class_type.fields.items():
            self.fields[key] = value.value

        for key, value in self.class_type.methods.items():
            self.methods[key] = (value.parameters, value.body)

    def run_method(self, method, arguments=[]):
        method_body = self.methods[method][1]
        method_parameters = self.methods[method][0]

        if len(method_parameters) != len(arguments):
            # TODO: Error
            None

        argument_binding = {}
        
        for i in range(0, len(arguments)):
            argument_binding[method_parameters[i]] = arguments[i]

        if method_body[0] == InterpreterBase.PRINT_DEF:
            value_to_be_printed = None
            argument = method_body[1]

            if (argument[0] == '"' and argument[-1] == '"') or argument == InterpreterBase.TRUE_DEF or argument == InterpreterBase.FALSE_DEF or ClassInstance.__is_number(argument):
                value_to_be_printed = argument
            else:
                if argument in argument_binding.keys():
                    value_to_be_printed = argument_binding[argument]
                else:
                    value_to_be_printed = self.fields[argument]
            self.interpreter.output(value_to_be_printed)
    
    def __is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
    
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

def main():
    program_source = ['(class main (field hello_world "hello world!") (method main () (print hello_world)))']
    
    interpreter = Interpreter()

    interpreter.run(program_source)

if __name__ == "__main__":
    main()