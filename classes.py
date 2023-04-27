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
            value_to_be_printed = ""

            for expression in method_body[1:]:
                value_to_be_printed += self.__execute_expression(expression, argument_binding).value.replace('"', "")
            
            self.interpreter.output(value_to_be_printed)
        
        elif method_body[0] == InterpreterBase.SET_DEF:
            variable_name = method_body[1]
            value = self.__execute_expression(method_body[2], argument_binding)

            self.fields[variable_name] = value

        elif method_body[0] == InterpreterBase.BEGIN_DEF:
            self.__handle_begin_statement(method_body[1:], argument_binding)

        elif method_body[0] == InterpreterBase.IF_DEF:
            expression = method_body[1]
            true_statement = method_body[2]
            false_statement = None if len(method_body) == 3 else method_body[3]

            expression_value = self.__execute_expression(expression, argument_binding)

            if expression_value.type != Type.BOOLEAN:
                # TODO: Exception
                pass
            elif expression_value.value == "true":
                self.__execute_statement(true_statement, argument_binding)
            elif false_statement is not None:
                self.__execute_statement(false_statement, argument_binding)

        else:
            self.__execute_expression(method_body, argument_binding)

    
    def __handle_begin_statement(self, begin_body, argument_binding):
        for line in begin_body:
            self.__execute_statement(line, argument_binding)

    # Call on one expression at a time
    def __execute_expression(self, expression, argument_binding):
        expression_type = Type.type(expression)

        if expression_type is not None:
            return Value(expression_type, expression)

        elif isinstance(expression, str):
            if expression in argument_binding.keys():
                return argument_binding[expression]
            else:
                return self.fields[expression]

        elif expression[0] == '+':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, int(left_value.value) + int(right_value.value))

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.STRING, int(left_value.value) + int(right_value.value))

            else:
                # TODO: Exception
                pass

        elif expression[0] == '-':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, int(left_value.value) - int(right_value.value))

            else:
                # TODO: Exception
                pass

        elif expression[0] == '*':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, int(left_value.value) * int(right_value.value))

            else:
                # TODO: Exception
                pass

        elif expression[0] == '/':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, int(left_value.value) // int(right_value.value))

            else:
                # TODO: Exception
                pass

        elif expression[0] == '%':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, int(left_value.value) % int(right_value.value))

            else:
                # TODO: Exception
                pass

        elif expression[0] == '==':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) == int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value) or ClassInstance.__check_both_bool(left_value, right_value) or ClassInstance.__check_both_null(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value == right_value.value).lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == '!=':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) != int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value) or ClassInstance.__check_both_bool(left_value, right_value) or ClassInstance.__check_both_null(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value != right_value.value).lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == '!':
            value = self.__execute_expression(expression[1], argument_binding)
            return Value(Type.BOOLEAN, str(value.value == "false").lower())

        elif expression[0] == '>':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) > int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value > right_value.value).lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == '>=':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) >= int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value >= right_value.value).lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == '<':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) < int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value < right_value.value).lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == '<=':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) <= int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value <= right_value.value).lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == '&':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value == "true" and right_value.value == "true").lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == '|':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value == "true" or right_value.value == "true").lower())

            else:
                # TODO: Exception
                pass

        elif expression[0] == InterpreterBase.NEW_DEF:
            class_name = expression[1]
            class_type = self.interpreter.classes[class_name]

            return ClassInstance(self.interpreter, class_type.name, class_type)

        elif expression[0] == InterpreterBase.CALL_DEF:
            obj = expression[1]
            method_name = expression[2]
            argument_bindings = expression[3:]
            environment = self.fields | argument_binding
            environment[InterpreterBase.ME_DEF] = self

            return_value = self.interpreter.call_function(obj, method_name, argument_bindings, environment)

            if return_value is not None:
                return return_value

    def __parse_binary_arguments(self, expression, argument_binding):
        left_value = self.__execute_expression(expression[1], argument_binding)
        right_value = self.__execute_expression(expression[2], argument_binding)

        return left_value, right_value

    def __check_both_numeric(left_value, right_value):
        return left_value.type == Type.NUMBER and right_value.type == Type.NUMBER

    def __check_both_string(left_value, right_value):
        return left_value.type == Type.STRING and right_value.type == Type.STRING

    def __check_both_bool(left_value, right_value):
        return left_value.type == Type.BOOLEAN and right_value.type == Type.BOOLEAN

    def __check_both_null(left_value, right_value):
        return left_value.type == Type.NULL and right_value.type == Type.NULL