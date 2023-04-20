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
        self.arguments = declaration_list[1]
        self.body = declaration_list[2]

    def print(self):
        print(f"Method {self.name}'s arguments are {self.arguments} and body is {self.body}")

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
                # error
                None

    def print(self):
        print(f"Class {self.name}'s fields and methods are:")
        for _, field in self.fields.items():
            field.print()
        for _, method in self.methods.items():
            method.print()
    
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

def main():
    program_source = ['(class main (method main () (print "hello world!")))']
    
    interpreter = Interpreter()

    interpreter.run(program_source)

if __name__ == "__main__":
    main()