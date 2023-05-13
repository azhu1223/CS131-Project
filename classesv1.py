from intbase import InterpreterBase, ErrorType
from enum import Enum
from inspect import isclass

class Type(Enum):
    NUMBER = 1
    BOOLEAN = 2
    STRING = 3
    NULL = 4
    OBJECT = 5

    def type(s):
        type = None

        if s == InterpreterBase.NULL_DEF:
            type = Type.NULL
        elif isclass(s):
            type = Type.OBJECT
        elif s == InterpreterBase.TRUE_DEF or s == InterpreterBase.FALSE_DEF:
            type = Type.BOOLEAN
        elif s[0] == '"' and s[-1] == '"':
            type = Type.STRING
        else:
            try:
                float(s)
                type = Type.NUMBER
            except:
                pass

        return type

class Value:
    def __init__(self, type : Type, value):
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
    def __init__(self, name, declaration_list, interpreter):
        self.name = name
        self.interpreter = interpreter
        self.fields = {}
        self.methods = {}

        for declaration in declaration_list:
            if (declaration[0] == InterpreterBase.FIELD_DEF):
                if declaration[1] in self.fields.keys():
                    self.interpreter.error(ErrorType.NAME_ERROR)
                self.fields[declaration[1]] = ClassField(declaration[1:])
            elif (declaration[0] == InterpreterBase.METHOD_DEF):
                if declaration[1] in self.methods.keys():
                    self.interpreter.error(ErrorType.NAME_ERROR)
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
        if method not in self.methods.keys():
            self.interpreter.error(ErrorType.NAME_ERROR)

        method_body = self.methods[method][1]
        method_parameters = self.methods[method][0]

        if len(method_parameters) != len(arguments):
            self.interpreter.error(ErrorType.TYPE_ERROR)

        argument_binding = {}
        
        for i in range(0, len(arguments)):
            argument_binding[method_parameters[i]] = arguments[i]

        return self.__execute_statement(method_body, argument_binding)

        
    def __execute_statement(self, method_body, argument_binding):
        if method_body[0] == InterpreterBase.PRINT_DEF:
            value_to_be_printed = ""

            for expression in method_body[1:]:
                value_to_be_printed += self.__execute_expression(expression, argument_binding).value.replace('"', "")
            
            self.interpreter.output(value_to_be_printed)
        
        elif method_body[0] == InterpreterBase.SET_DEF:
            variable_name = method_body[1]
            value = self.__execute_expression(method_body[2], argument_binding)

            if variable_name in argument_binding.keys():
                argument_binding[variable_name] = value
            elif variable_name in self.fields.keys():
                self.fields[variable_name] = value
            else:
                self.interpreter.error(ErrorType.NAME_ERROR)

        elif method_body[0] == InterpreterBase.BEGIN_DEF:
            for line in method_body[1:]:
                return_value = self.__execute_statement(line, argument_binding)
                if return_value is not None:
                    return return_value

        elif method_body[0] == InterpreterBase.IF_DEF:
            expression = method_body[1]
            true_statement = method_body[2]
            false_statement = None if len(method_body) == 3 else method_body[3]

            expression_value = self.__execute_expression(expression, argument_binding)

            if expression_value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)
            elif expression_value.value == InterpreterBase.TRUE_DEF:
                return self.__execute_statement(true_statement, argument_binding)
            elif false_statement is not None:
                return self.__execute_statement(false_statement, argument_binding)

        elif method_body[0] == InterpreterBase.WHILE_DEF:
            expression = method_body[1]
            statement = method_body[2]
            return_value = None

            expression_value = self.__execute_expression(expression, argument_binding)
            if expression_value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)

            while expression_value.value == InterpreterBase.TRUE_DEF:
                return_value = self.__execute_statement(statement, argument_binding)
                
                expression_value = self.__execute_expression(expression, argument_binding)
                if expression_value.type != Type.BOOLEAN:
                    self.interpreter.error(ErrorType.TYPE_ERROR)

            return return_value

        elif method_body[0] == InterpreterBase.INPUT_INT_DEF:
            variable_name = method_body[1]
            integer_value = self.interpreter.get_input()
            value = Value(Type.NUMBER, integer_value)

            if variable_name in argument_binding.keys():
                argument_binding[variable_name] = value
            else:
                self.fields[variable_name] = value

        elif method_body[0] == InterpreterBase.INPUT_STRING_DEF:
            variable_name = method_body[1]
            string_value = self.interpreter.get_input()
            value = Value(Type.STRING, '"' + string_value + '"')

            if variable_name in argument_binding.keys():
                argument_binding[variable_name] = value
            else:
                self.fields[variable_name] = value

        elif method_body[0] == InterpreterBase.RETURN_DEF:
            expression_value = None
            
            if len(method_body) != 1:
                expression = method_body[1]
                expression_value = self.__execute_expression(expression, argument_binding)

            return expression_value

        else:
            self.__execute_expression(method_body, argument_binding)

    # Call on one expression at a time
    def __execute_expression(self, expression, argument_binding):
        expression_type = Type.type(expression)

        if expression_type is not None:
            return Value(expression_type, expression)

        elif isinstance(expression, str):
            if expression in argument_binding.keys():
                return argument_binding[expression]
            elif expression in self.fields.keys():
                return self.fields[expression]
            else:
                self.interpreter.error(ErrorType.NAME_ERROR)

        elif expression[0] == '+':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, str(int(left_value.value) + int(right_value.value)))

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.STRING, str(left_value.value + right_value.value))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '-':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, str(int(left_value.value) - int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '*':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, str(int(left_value.value) * int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '/':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, str(int(left_value.value) // int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '%':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.NUMBER, str(int(left_value.value) % int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '==':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) == int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value) or ClassInstance.__check_both_bool(left_value, right_value) or ClassInstance.__check_second_null(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value == right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '!=':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) != int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value) or ClassInstance.__check_both_bool(left_value, right_value) or ClassInstance.__check_second_null(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value != right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '!':
            value = self.__execute_expression(expression[1], argument_binding)
            if value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)
            return Value(Type.BOOLEAN, str(value.value == InterpreterBase.FALSE_DEF).lower())

        elif expression[0] == '>':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) > int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value > right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '>=':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) >= int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value >= right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '<':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) < int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value < right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '<=':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(Type.BOOLEAN, str(int(left_value.value) <= int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value <= right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '&':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value == InterpreterBase.TRUE_DEF and right_value.value == InterpreterBase.TRUE_DEF).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '|':
            left_value, right_value = self.__parse_binary_arguments(expression, argument_binding)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(Type.BOOLEAN, str(left_value.value == InterpreterBase.TRUE_DEF or right_value.value == InterpreterBase.TRUE_DEF).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == InterpreterBase.NEW_DEF:
            class_name = expression[1]

            if class_name not in self.interpreter.classes.keys():
                self.interpreter.error(ErrorType.TYPE_ERROR)

            class_type = self.interpreter.classes[class_name]

            return Value(Type.OBJECT, ClassInstance(self.interpreter, class_type.name, class_type))

        elif expression[0] == InterpreterBase.CALL_DEF:
            method_name = expression[2]
            environment = self.fields | argument_binding
            environment[InterpreterBase.ME_DEF] = Value(Type.OBJECT, self)

            obj = self.__execute_expression(expression[1], environment)

            if obj.type == Type.NULL:
                self.interpreter.error(ErrorType.FAULT_ERROR)

            arguments_passed = []
            for argument in expression[3:]:
                arguments_passed.append(self.__execute_expression(argument, argument_binding))

            return_value = self.interpreter.call_function(obj, method_name, arguments_passed)

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

    def __check_second_null(left_value, right_value):
        return (left_value.type == Type.NULL or left_value.type == Type.OBJECT) and right_value.type == Type.NULL