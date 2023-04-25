from intbase import InterpreterBase
from enum import Enum

class Type(Enum):
    NUMBER = 1
    BOOLEAN = 2
    STRING = 3
    NULL = 4

    def type(s):
        type = None

        if (s == InterpreterBase.NULL_DEF):
            type = Type.NULL
        else:
            if (s == InterpreterBase.TRUE_DEF or s == InterpreterBase.FALSE_DEF):
                type = Type.BOOLEAN
            else:
                if (s[0] == '"' and s[-1] == '"'):
                    type = Type.STRING
                else:
                    try:
                        float(s)
                        type = Type.NUMBER
                    except:
                        pass

        return type

class Value:
    def __init__(self, type, value):
        self.type = type
        self.value = value

class ClassField:
    # Pass in the list without the "field" part
    def __init__(self, declaration_list):
        self.name = declaration_list[0]

        value = declaration_list[1]
        type = Type.type(value)

        self.value = Value(type, value)

    def print(self):
        print(f"Field {self.name} equals {self.value.value} of type {self.value.type}")

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

        self.__execute_statement(method_body, argument_binding)

        
    def __execute_statement(self, method_body, argument_binding):
        if method_body[0] == InterpreterBase.PRINT_DEF:
            value_to_be_printed = None
            argument = method_body[1]
            argument_type = Type.type(argument)

            if argument_type is not None:
                value_to_be_printed = argument
            elif argument == InterpreterBase.CALL_DEF:
                None
            else:
                if argument in argument_binding.keys():
                    value_to_be_printed = argument_binding[argument].value
                else:
                    value_to_be_printed = self.fields[argument].value
            self.interpreter.output(value_to_be_printed)

        elif method_body[0] == InterpreterBase.CALL_DEF:
            obj = method_body[1]
            method_name = method_body[2]
            argument_bindings = method_body[3:]
            environment = self.fields | argument_binding
            environment["me"] = self

            self.interpreter.call_function(obj, method_name, argument_bindings, environment)
        
        elif method_body[0] == InterpreterBase.SET_DEF:
            variable_name = method_body[1]
            value_expression = method_body[2]
            value_type = Type.type(value_expression)

            if value_type is None:
                value = self.__execute_statement(method_body[2], argument_binding)

            else:
                value = Value(value_type, value_expression)

            if variable_name in argument_binding.keys():
                argument_binding[variable_name] = value
            else:
                self.fields[variable_name] = value


        # Need to fix this
        elif method_body[0] == InterpreterBase.NEW_DEF:
            class_name = method_body[1]
            class_type = self.interpreter.classes[class_name]

            return ClassInstance(self.interpreter, class_type.name, class_type)

        elif method_body[0] == InterpreterBase.BEGIN_DEF:
            self.__handle_begin_statement(method_body[1:], argument_binding)
    
    def __handle_begin_statement(self, begin_body, argument_binding):
        for line in begin_body:
            self.__execute_statement(line, argument_binding)