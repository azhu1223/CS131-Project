from intbase import InterpreterBase, ErrorType
from enum import Enum
from inspect import isclass
from copy import copy

class Type(Enum):
    NUMBER = 1
    BOOLEAN = 2
    STRING = 3
    NULL = 4
    RETURN_NULL = 5
    NOT_A_VARIABLE = 6

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
        elif s == InterpreterBase.NULL_DEF:
            type = Type.NULL
        elif s == "void":
            type = Type.RETURN_NULL

        return type

class Value:
    def __init__(self, value, returned_nothing=False, null_type=None):
        if returned_nothing:
            self.type = Type.RETURN_NULL
        else: 
            self.type = Type.type(value)
            if self.type == Type.NULL:
                self.null_type = null_type
            self.value = value

class Variable:
    def __init__(self, type : str, name : str, value : Value, interpreter):
        self.type = Type.string_to_type(type)
        self.name = name
        self.interpreter = interpreter
        self.assign(value)
    
    def assign(self, value : Value):
        if (self.type == value.type or
            (isinstance(self.type, str) and value.type == Type.NULL) or
            (isinstance(value.type, str) and (self.type == Type.NULL or value.value.is_instance(self.type)))
        ):
            self.value = value

            if self.value.type == Type.NULL:
                self.value.null_type = self.type

        else:
            self.interpreter.error(ErrorType.TYPE_ERROR)

    def get_value(self):
        return self.value.value

    def print(self):
        print(f"Variable {self.name} equals {self.value.value} of type {self.type}")

class ClassField:
    # Pass in the list without the "field" part
    def __init__(self, declaration_list, interpreter):
        self.interpreter = interpreter
        self.name = declaration_list[1]
        self.type = declaration_list[0]
        self.value = Value(declaration_list[2])

    def print(self):
        print(f"Field {self.name} equals {self.value.value} of type {self.type}")

class ClassMethod:
    # Pass in the list without the "method" part
    def __init__(self, declaration_list, interpreter):
        self.type = Type.string_to_type(declaration_list[0])
        self.name = declaration_list[1]
        self.parameters = declaration_list[2]
        self.body = declaration_list[3]

        self.parameter_types = []

        parameter_names = []

        for parameter in self.parameters:
            self.parameter_types.append(parameter[0])

            parameter_name = parameter[1]

            if parameter_name in parameter_names:
                interpreter.error(ErrorType.NAME_ERROR)
            else:
                parameter_names.append(parameter[1])

    def print(self):
        print(f"Method {self.name}'s parameters are {self.parameters}, body is {self.body}, and type is {self.type}")

class ClassDefinition:
    def __init__(self, name, declaration_list, interpreter, parent_class=None):
        self.name = name
        self.interpreter = interpreter
        self.parent_class = parent_class
        self.fields = {}
        self.methods = {}
        self.valid_types = [name]

        for declaration in declaration_list:
            if (declaration[0] == InterpreterBase.FIELD_DEF):
                if declaration[2] in self.fields.keys():
                    self.interpreter.error(ErrorType.NAME_ERROR)
                self.fields[declaration[2]] = ClassField(declaration[1:], self.interpreter)
            elif (declaration[0] == InterpreterBase.METHOD_DEF):
                if declaration[2] in self.methods.keys():
                    self.interpreter.error(ErrorType.NAME_ERROR)
                self.methods[declaration[2]] = ClassMethod(declaration[1:], self.interpreter)
            else:
                # TODO: Error
                None

        if parent_class is not None:
            self.valid_types.extend(self.parent_class.valid_types)

        if Type.NULL not in self.valid_types:
            self.valid_types.append(Type.NULL)
            self.valid_types.append(Type.NOT_A_VARIABLE)

    def print(self):
        print(f"Class {self.name}'s fields and methods are:")
        for _, field in self.fields.items():
            field.print()
        for _, method in self.methods.items():
            method.print()

class ClassInstance:
    def __init__(self, interpreter, name, class_type, null_instance=False):
        if not null_instance:
            self.interpreter = interpreter
            self.type = name
            self.name = name
            self.class_type = class_type
            self.fields = {}
            self.methods = {}
            self.parent_object = None
            self.me = []

            for key, value in self.class_type.fields.items():
                self.fields[key] = Variable(value.type, key, value.value, self.interpreter)

            for key, value in self.class_type.methods.items():
                self.methods[key] = value

            parent_class = class_type.parent_class

            self.override_stack = []

            if parent_class is not None:
                self.parent_object = ClassInstance(interpreter, parent_class.name, parent_class)
                self.override_stack.extend(self.parent_object.override_stack)
                self.me = self.parent_object.me
                self.me.pop()
            else:
                self.parent_object = ClassInstance(None, None, None, True)

            self.me.append(self)

            self.override_stack.append((self.fields, self.methods, self))
        else:
            self.type = Type.NULL
            self.name = Type.NULL

    def run_method(self, environment_stack, method, arguments=[]):
        method_body = method.body
        method_parameters = method.parameters
        method_type = Type.string_to_type(method.type)

        if len(method_parameters) != len(arguments):
            self.interpreter.error(ErrorType.TYPE_ERROR)

        argument_binding = {}
        
        for i in range(0, len(arguments)):
            parameter = method_parameters[i]
            parameter_type = parameter[0]
            parameter_name = parameter[1]

            parameter_variable = Variable(parameter_type, parameter_name, arguments[i], self.interpreter)

            argument_binding[parameter_name] = parameter_variable

        environment_stack.append(argument_binding)

        return_value = self.__execute_statement(method_body, environment_stack, method_type)

        environment_stack.pop()

        if (method_type != Type.RETURN_NULL and (return_value is None or return_value.type == Type.RETURN_NULL)):
            return_value = ClassInstance.__get_default_return_value(method_type)

        if (return_value is not None and 
            (
                (
                    (method_type != return_value.type) and not 
                    (return_value.type == Type.NULL and method_type in self.interpreter.classes.keys()) and not
                    (isinstance(return_value.type, str) and return_value.value.is_instance(method_type))
                ) or 
                return_value.type == Type.NULL and method_type in self.interpreter.classes.keys() and return_value.null_type not in self.interpreter.classes[method_type].valid_types
            )
            ):
            self.interpreter.error(ErrorType.TYPE_ERROR)

        return return_value
    
    def is_instance(self, type):
        return_value = False

        if type == Type.NULL or type == Type.NOT_A_VARIABLE:
            return_value = True

        test_object = self
        while test_object.type != Type.NULL and not return_value:
            if test_object.type == type:
                return_value = True
            else:
                test_object = test_object.parent_object
        
        return return_value

    def __get_default_return_value(method_type):
        if method_type == Type.NUMBER:
            return Value("0")
        elif method_type == Type.BOOLEAN:
            return Value(InterpreterBase.FALSE_DEF)
        elif method_type == Type.STRING:
            return Value('""')
        elif method_type == Type.RETURN_NULL:
            return Value(0, True)
        else:
            return Value(InterpreterBase.NULL_DEF)
        
    def __execute_statement(self, method_body, environment_stack, method_type=Type.RETURN_NULL):
        if method_body[0] == InterpreterBase.PRINT_DEF:
            value_to_be_printed = ""

            for expression in method_body[1:]:
                value_to_be_printed += self.__execute_expression(expression, environment_stack)[0].value.replace('"', "")
            
            self.interpreter.output(value_to_be_printed)
        
        elif method_body[0] == InterpreterBase.SET_DEF:
            variable_name = method_body[1]

            expression = method_body[2]

            variable = self.__get_variable_from_environment(environment_stack, variable_name)

            value = None

            if expression == InterpreterBase.ME_DEF:
                value = Value(self.me[0])
            else:
                value, _ = self.__execute_expression(expression, environment_stack, variable.type)

            variable.assign(value)

        elif method_body[0] == InterpreterBase.LET_DEF:
            variable_declarations = method_body[1]
            statement_body = method_body[2:]

            variable_bindings = {}

            for variable_declaration in variable_declarations:
                type = variable_declaration[0]
                name = variable_declaration[1]

                if name in variable_bindings.keys():
                    self.interpreter.error(ErrorType.NAME_ERROR)

                value, _ = self.__execute_expression(variable_declaration[2], environment_stack)

                variable_bindings[name] = Variable(type, name, value, self.interpreter)

            environment_stack.append(variable_bindings)

            new_method_body = [InterpreterBase.BEGIN_DEF]
            new_method_body.extend(statement_body)

            return_value = self.__execute_statement(new_method_body, environment_stack)

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

            expression_value, _ = self.__execute_expression(expression, environment_stack)

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

            expression_value, _ = self.__execute_expression(expression, environment_stack)
            if expression_value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)

            while expression_value.value == InterpreterBase.TRUE_DEF:
                return_value = self.__execute_statement(statement, environment_stack)
                
                expression_value, _ = self.__execute_expression(expression, environment_stack)
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

                if (expression == "me"):
                    expression_value = Value(self.me[0])
                else:
                    expression_value, _ = self.__execute_expression(expression, environment_stack)

            if expression_value is None:
                expression_value = ClassInstance.__get_default_return_value(method_type)

            if expression_value.type == Type.NULL and expression_value.null_type == None:
                expression_value.null_type = method_type

            return expression_value

        else:
            self.__execute_expression(method_body, environment_stack)

    # Call on one expression at a time
    def __execute_expression(self, expression, environment_stack, variable_type=None):
        expression_type = Type.type(expression)

        if expression_type is not None:
            return Value(expression), Type.NOT_A_VARIABLE

        elif isinstance(expression, str):
            variable = self.__get_variable_from_environment(environment_stack, expression)
            return variable.value, variable.type

        elif expression[0] == '+':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) + int(right_value.value))), Type.NOT_A_VARIABLE

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value + right_value.value)), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '-':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) - int(right_value.value))), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '*':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) * int(right_value.value))), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '/':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) // int(right_value.value))), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '%':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) % int(right_value.value))), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '==':
            left_value, right_value, left_variable_type, right_variable_type = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) == int(right_value.value)).lower()), Type.NOT_A_VARIABLE

            elif (ClassInstance.__check_both_string(left_value, right_value) or 
                ClassInstance.__check_both_bool(left_value, right_value) or 
                self.__check_both_objects(left_value, right_value, left_variable_type, right_variable_type)):

                return Value(str(left_value.value == right_value.value).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '!=':
            left_value, right_value, left_variable_type, right_variable_type = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) != int(right_value.value)).lower()), Type.NOT_A_VARIABLE

            elif (ClassInstance.__check_both_string(left_value, right_value) or 
                ClassInstance.__check_both_bool(left_value, right_value) or 
                self.__check_both_objects(left_value, right_value, left_variable_type, right_variable_type)):

                return Value(str(left_value.value != right_value.value).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '!':
            value, _ = self.__execute_expression(expression[1], environment_stack)
            if value.type != Type.BOOLEAN:
                self.interpreter.error(ErrorType.TYPE_ERROR)
            return Value(str(value.value == InterpreterBase.FALSE_DEF).lower()), Type.NOT_A_VARIABLE

        elif expression[0] == '>':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) > int(right_value.value)).lower()), Type.NOT_A_VARIABLE

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value > right_value.value).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '>=':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) >= int(right_value.value)).lower()), Type.NOT_A_VARIABLE

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value >= right_value.value).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '<':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) < int(right_value.value)).lower()), Type.NOT_A_VARIABLE

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value < right_value.value).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '<=':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_numeric(left_value, right_value):
                return Value(str(int(left_value.value) <= int(right_value.value)).lower()), Type.NOT_A_VARIABLE

            elif ClassInstance.__check_both_string(left_value, right_value):
                return Value(str(left_value.value <= right_value.value).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '&':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(str(left_value.value == InterpreterBase.TRUE_DEF and right_value.value == InterpreterBase.TRUE_DEF).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == '|':
            left_value, right_value, _, _ = self.__parse_binary_arguments(expression, environment_stack)

            if ClassInstance.__check_both_bool(left_value, right_value):
                return Value(str(left_value.value == InterpreterBase.TRUE_DEF or right_value.value == InterpreterBase.TRUE_DEF).lower()), Type.NOT_A_VARIABLE

            else:
                self.interpreter.error(ErrorType.TYPE_ERROR)

        elif expression[0] == InterpreterBase.NEW_DEF:
            class_name = expression[1]

            if class_name not in self.interpreter.classes.keys():
                self.interpreter.error(ErrorType.TYPE_ERROR)

            class_type = self.interpreter.classes[class_name]

            return Value(ClassInstance(self.interpreter, class_type.name, class_type)), Type.NOT_A_VARIABLE

        elif expression[0] == InterpreterBase.CALL_DEF:
            method_name = expression[2]

            special_keyword_references = {InterpreterBase.ME_DEF : Variable(Type.type(self.me[0]), InterpreterBase.ME_DEF, Value(self.me[0]), self.interpreter)}

            if self.parent_object.name != Type.NULL:
                special_keyword_references[InterpreterBase.SUPER_DEF] = Variable(Type.type(self.parent_object), InterpreterBase.SUPER_DEF, Value(self.parent_object), self.interpreter)

            if expression[1] == InterpreterBase.SUPER_DEF and self.parent_object.name == Type.NULL:
                self.interpreter.error(ErrorType.TYPE_ERROR)
            
            environment_stack.append(special_keyword_references)

            obj, _ = self.__execute_expression(expression[1], environment_stack)

            environment_stack.pop()

            if obj.type == Type.NULL:
                self.interpreter.error(ErrorType.FAULT_ERROR)

            arguments_passed = []
            for argument in expression[3:]:
                arguments_passed.append(self.__execute_expression(argument, environment_stack)[0])

            return_value = self.interpreter.call_function([], obj, method_name, arguments_passed, variable_type)

            if return_value is not None:
                return return_value, Type.NOT_A_VARIABLE

    def __parse_binary_arguments(self, expression, environment_stack):
        #TODO: Fix this
        left_value, left_variable_type = self.__execute_expression(expression[1], environment_stack)
        right_value, right_variable_type = self.__execute_expression(expression[2], environment_stack)

        if left_value.type == Type.NULL and left_value.null_type is not None:
            left_variable_type = left_value.null_type

        if right_value.type == Type.NULL and right_value.null_type is not None:
            right_variable_type = right_value.null_type

        return left_value, right_value, left_variable_type, right_variable_type

    def __check_both_numeric(left_value, right_value):
        return left_value.type == Type.NUMBER and right_value.type == Type.NUMBER

    def __check_both_string(left_value, right_value):
        return left_value.type == Type.STRING and right_value.type == Type.STRING

    def __check_both_bool(left_value, right_value):
        return left_value.type == Type.BOOLEAN and right_value.type == Type.BOOLEAN

    def __check_both_objects(self, left_value, right_value, left_variable_type, right_variable_type):
        return_value = False

        if left_value.type == Type.NULL and right_value.type == Type.NULL:
            return_value = ((left_variable_type in self.interpreter.classes.keys() and right_variable_type in self.interpreter.classes[left_variable_type].valid_types) or 
                                    (right_variable_type in self.interpreter.classes.keys() and left_variable_type in self.interpreter.classes[right_variable_type].valid_types))

        else:
            return_value = (left_value.type == right_value.type or
                            (not isinstance(Type.type(left_value.value), Type) and left_value.value.is_instance(right_variable_type)) or 
                            (not isinstance(Type.type(right_value.value), Type) and right_value.value.is_instance(left_variable_type)))

        return return_value

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

    def find_method_from_override_stack(self, method_name, passed_argument_types=None):
        override_stack = copy(self.override_stack)

        return_method_and_fields = None

        while override_stack and return_method_and_fields is None:
            methods_and_fields = override_stack.pop()
            methods = methods_and_fields[1]

            if method_name in methods.keys():
                method = methods[method_name]

                if passed_argument_types == None:
                    return method
                else:
                    method_parameter_types = copy(method.parameter_types)
                    temp_passed_argument_types = copy(passed_argument_types)

                    is_correct_method = True

                    while method_parameter_types and temp_passed_argument_types and is_correct_method:
                        method_parameter_type = Type.string_to_type(method_parameter_types.pop())
                        temp_passed_argument_type = Type.string_to_type(temp_passed_argument_types.pop())

                        if not (method_parameter_type == temp_passed_argument_type or (isinstance(temp_passed_argument_type, str) and method_parameter_type in self.interpreter.classes[temp_passed_argument_type].valid_types)):
                            if not isinstance(method_parameter_type, str) or temp_passed_argument_type not in self.interpreter.classes[method_parameter_type].valid_types:
                                is_correct_method = False

                    if is_correct_method and not (method_parameter_types or temp_passed_argument_types):
                        return_method_and_fields = (methods_and_fields[0], method, methods_and_fields[2])

        if return_method_and_fields is None:
            self.interpreter.error(ErrorType.NAME_ERROR)

        return return_method_and_fields

                

