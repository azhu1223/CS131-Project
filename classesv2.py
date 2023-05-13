from intbase import InterpreterBase, ErrorType
from enum import Enum
from inspect import isclass
from copy import copy

class Type(Enum):
    NUMBER = 1
    BOOLEAN = 2
    STRING = 3
    NULL = 4

    def type(s):
        type = None

        if s == InterpreterBase.NULL_DEF:
            type = Type.NULL
        elif isinstance(s, ClassInstance):
            type = s.name
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

    def string_to_type(s):
        type = s

        if s == "int":
            type = Type.NUMBER
        elif s == "bool":
            type = Type.BOOLEAN
        elif s == "string":
            type = Type.STRING

        return type

class Value:
    def __init__(self, value):
        self.type = Type.type(value)
        self.value = value

class Variable:
    def __init__(self, type : str, name : str, value : Value):
        self.type = Type.string_to_type(type)
        self.name = name
        self.assign(value)
    
    def assign(self, value : Value):
        if (self.type == value.type):
            self.value = value
        else:
            # TODO: Error
            pass

    def get_value(self):
        return self.value.value

    def print(self):
        print(f"Variable {self.name} equals {self.value.value} of type {self.type}")

class ClassField(Variable):
    # Pass in the list without the "field" part
    def __init__(self, declaration_list):
        type = declaration_list[0]
        value = Value(declaration_list[2])

        super().__init__(type, declaration_list[1], value)

    def print(self):
        print(f"Field {self.name} equals {self.value.value} of type {self.type}")

class ClassMethod:
    # Pass in the list without the "method" part
    def __init__(self, declaration_list):
        self.type = Type.string_to_type(declaration_list[0])
        self.name = declaration_list[1]
        self.parameters = declaration_list[2]
        self.body = declaration_list[3]

    def print(self):
        print(f"Method {self.name}'s parameters are {self.parameters}, body is {self.body}, and type is {self.type}")

class ClassDefinition:
    def __init__(self, name, declaration_list, interpreter):
        self.name = name
        self.interpreter = interpreter
        self.fields = {}
        self.methods = {}

        for declaration in declaration_list:
            if (declaration[0] == InterpreterBase.FIELD_DEF):
                if declaration[2] in self.fields.keys():
                    self.interpreter.error(ErrorType.NAME_ERROR)
                self.fields[declaration[2]] = ClassField(declaration[1:])
            elif (declaration[0] == InterpreterBase.METHOD_DEF):
                if declaration[2] in self.methods.keys():
                    self.interpreter.error(ErrorType.NAME_ERROR)
                self.methods[declaration[2]] = ClassMethod(declaration[1:])
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
            self.fields[key] = Variable(value.type, key, value.value)

        for key, value in self.class_type.methods.items():
            self.methods[key] = (value.type, value.parameters, value.body)

    def run_method(self, environment_stack, method, arguments=[]):
        if method not in self.methods.keys():
            self.interpreter.error(ErrorType.NAME_ERROR)

        method_body = self.methods[method][2]
        method_parameters = self.methods[method][1]
        method_type = self.methods[method][0]

        if len(method_parameters) != len(arguments):
            self.interpreter.error(ErrorType.TYPE_ERROR)

        argument_binding = {}
        
        for i in range(0, len(arguments)):
            parameter = method_parameters[i]
            parameter_type = parameter[0]
            parameter_name = parameter[1]

            parameter_variable = Variable(parameter_type, parameter_name, arguments[i])

            argument_binding[parameter_name] = parameter_variable

        environment_stack.append(argument_binding)

        return_value = self.__execute_statement(method_body, environment_stack)

        environment_stack.pop()

        if (method_type == 'void' and return_value is not None):
            # TODO: Error
            pass
        elif method_type != 'void' and return_value == None:
            return_value = self.__get_default_return_value(method_type)

        return return_value

    def __get_default_return_value(self, method_type):
        if method_type == 'int':
            return Value(0)
        elif method_type == 'bool':
            return Value(InterpreterBase.FALSE_DEF)
        elif method_type == 'string':
            return Value('""')
        else:
            return Value(InterpreterBase.NULL_DEF)
        
    def __execute_statement(self, method_body, environment_stack):
        if method_body[0] == InterpreterBase.PRINT_DEF:
            value_to_be_printed = ""

            for expression in method_body[1:]:
                value_to_be_printed += self.__execute_expression(expression, environment_stack).value.replace('"', "")
            
            self.interpreter.output(value_to_be_printed)
        
        elif method_body[0] == InterpreterBase.SET_DEF:
            variable_name = method_body[1]
            value = self.__execute_expression(method_body[2], environment_stack)

            variable = self.__get_variable_from_environment(environment_stack, variable_name)

            variable.assign(value)

        elif method_body[0] == InterpreterBase.LET_DEF:
            variable_declarations = method_body[1]
            statement_body = method_body[2]

            variable_bindings = {}

            for variable_declaration in variable_declarations:
                type = variable_declaration[0]
                name = variable_declaration[1]
                value = self.__execute_expression(variable_declaration[2], environment_stack)

                variable_bindings[name] = Variable(type, name, value)

            environment_stack.append(variable_bindings)

            return_value = self.__execute_statement([InterpreterBase.BEGIN_DEF, statement_body], environment_stack)

            environment_stack.pop()

            return return_value

        elif method_body[0] == InterpreterBase.BEGIN_DEF:
            for line in method_body[1:]:
                return_value = self.__execute_statement(line, environment_stack)
                if return_value is not None:
                    return return_value

        elif method_body[0] == InterpreterBase.IF_DEF:
            expression = method_body[1]
            true_statement = method_body[2]
            false_statement = None if len(method_body) == 3 else method_body[3]

            expression_value = self.__execute_expression(expression, environment_stack)

            if expression_value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)
            elif expression_value.value == InterpreterBase.TRUE_DEF:
                return self.__execute_statement(true_statement, environment_stack)
            elif false_statement is not None:
                return self.__execute_statement(false_statement, environment_stack)

        elif method_body[0] == InterpreterBase.WHILE_DEF:
            expression = method_body[1]
            statement = method_body[2]
            return_value = None

            expression_value = self.__execute_expression(expression, environment_stack)
            if expression_value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)

            while expression_value.value == InterpreterBase.TRUE_DEF:
                return_value = self.__execute_statement(statement, environment_stack)
                
                expression_value = self.__execute_expression(expression, environment_stack)
                if expression_value.type != Type.BOOLEAN:
                    self.interpreter.error(ErrorType.TYPE_ERROR)

            return return_value

        elif method_body[0] == InterpreterBase.INPUT_INT_DEF:
            variable_name = method_body[1]
            integer_value = self.interpreter.get_input()
            value = Value(integer_value)

            variable = self.__get_variable_from_environment(environment_stack, variable_name)
            variable.assign(value)

        elif method_body[0] == InterpreterBase.INPUT_STRING_DEF:
            variable_name = method_body[1]
            string_value = self.interpreter.get_input()
            value = Value('"' + string_value + '"')

            variable = self.__get_variable_from_environment(environment_stack, variable_name)
            variable.assign(value)

        elif method_body[0] == InterpreterBase.RETURN_DEF:
            expression_value = None
            
            if len(method_body) != 1:
                expression = method_body[1]
                expression_value = self.__execute_expression(expression, environment_stack)

            return expression_value

        else:
            self.__execute_expression(method_body, environment_stack)

    # Call on one expression at a time
    def __execute_expression(self, expression, environment_stack):
        expression_type = Type.type(expression)

        if expression_type is not None:
            return Value(expression)

        elif isinstance(expression, str):
            variable = self.__get_variable_from_environment(environment_stack, expression)
            return variable.value

        elif expression[0] == '+':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) + int(right_value.value)))

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value + right_value.value))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '-':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) - int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '*':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) * int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '/':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) // int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '%':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) % int(right_value.value)))

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '==':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) == int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value) or ClassInstance.__check_both_bool(left_value, right_value) or ClassInstance.__check_second_null(left_value, right_value):
                return Value(str(left_value.value == right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '!=':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) != int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value) or ClassInstance.__check_both_bool(left_value, right_value) or ClassInstance.__check_second_null(left_value, right_value):
                return Value(str(left_value.value != right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '!':
            value = self.__execute_expression(expression[1], environment_stack)
            if value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)
            return Value(str(value.value == InterpreterBase.FALSE_DEF).lower())

        elif expression[0] == '>':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) > int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value > right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '>=':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) >= int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value >= right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '<':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) < int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value < right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '<=':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) <= int(right_value.value)).lower())

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value <= right_value.value).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '&':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(str(left_value.value == InterpreterBase.TRUE_DEF and right_value.value == InterpreterBase.TRUE_DEF).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '|':
            left_value, right_value = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(str(left_value.value == InterpreterBase.TRUE_DEF or right_value.value == InterpreterBase.TRUE_DEF).lower())

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == InterpreterBase.NEW_DEF:
            class_name = expression[1]

            if class_name not in self.interpreter.classes.keys():
                self.interpreter.error(ErrorType.TYPE_ERROR)

            class_type = self.interpreter.classes[class_name]

            return Value(ClassInstance(self.interpreter, class_type.name, class_type))

        elif expression[0] == InterpreterBase.CALL_DEF:
            method_name = expression[2]
            
            environment_stack.append({InterpreterBase.ME_DEF : Variable(Type.type(self), InterpreterBase.ME_DEF, Value(self))})

            obj = self.__execute_expression(expression[1], environment_stack)

            environment_stack.pop()

            if obj.type == Type.NULL:
                self.interpreter.error(ErrorType.FAULT_ERROR)

            arguments_passed = []
            for argument in expression[3:]:
                arguments_passed.append(self.__execute_expression(argument, environment_stack))

            return_value = self.interpreter.call_function([], obj, method_name, arguments_passed)

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

    def __get_variable_from_environment(self, environment_stack, variable_name : str):
        environment_stack = copy(environment_stack)

        variable = None

        while environment_stack and variable is None:
            dictionary = environment_stack.pop()
            
            if variable_name in dictionary.keys():
                variable = dictionary[variable_name]

        if variable is not None:
            return variable
        else:
            self.interpreter.error(ErrorType.NAME_ERROR)