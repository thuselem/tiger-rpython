from src.environment import Environment
from src.rpythonized_object import RPythonizedObject

# Begin RPython setup; catch import errors so this can still run in CPython...
try:
    from rpython.rlib.jit import JitDriver, elidable, promote, unroll_safe, jit_debug, we_are_jitted
except ImportError:
    class JitDriver(object):
        def __init__(self, **kw): pass

        def jit_merge_point(self, **kw): pass

        def can_enter_jit(self, **kw): pass


    def elidable(func):
        return func


    def promote(x):
        return x


    def unroll_safe(func):
        return func


    def jit_debug(string, arg1=0, arg2=0, arg3=0, arg4=0):
        pass


    def we_are_jitted():
        return False


def get_location(code):
    return "%s" % code.to_string()


jitdriver = JitDriver(greens=['code'], reds='auto', get_printable_location=get_location)


def jitpolicy(driver):
    try:
        from rpython.jit.codewriter.policy import JitPolicy
        return JitPolicy()
    except ImportError:
        raise NotImplemented("Abandon if we are unable to use RPython's JitPolicy")


# end of RPython setup


class InterpretationError(Exception):
    def __init__(self, reason):
        self.reason = reason

    def to_string(self):
        return self.reason

    def __str__(self):
        return self.to_string()


class Program(RPythonizedObject):
    def evaluate(self, env=None):
        pass
        # TODO implement in sub-classes

    def equals(self, other):
        return RPythonizedObject.equals(self, other)
        # TODO implement in sub-classes


def list_equals(list1, list2):
    """Helper function for comparing two iterable sequences of expressions using .equals()"""
    if len(list1) != len(list2):
        return False
    else:
        for i in range(len(list1)):
            if not list1[i].equals(list2[i]):
                print("not equal: %s" % list1[i].to_string())
                return False
    return True


def dict_equals(dict1, dict2):
    """Helper function for comparing two iterable sequences of expressions using .equals()"""
    if len(dict1) != len(dict2):
        return False
    else:
        for i in dict1:
            if not dict1[i].equals(dict2[i]):
                return False
    return True


def nullable_equals(obj1, obj2):
    if obj1 is None and obj2 is None:
        return True
    elif obj1 is not None and obj2 is not None:
        return obj1.equals(obj2)
    else:
        return False


def list_to_string(list):
    stringified = []
    for item in list:
        stringified.append(item.to_string())
    return '[%s]' % (', '.join(stringified))


def dict_to_string(dict):
    stringified = []
    for key in dict:
        stringified.append(key + '=' + dict[key].to_string())
    return '{%s}' % (', '.join(stringified))


def nullable_to_string(obj):
    return obj.to_string() if obj is not None else 'None'


class Exp(Program):
    pass


class Declaration(Program):
    def __init__(self, name):
        self.name = name

    def evaluate(self, env=None):
        env.set_current_level(self.name, self)


class Type(Program):
    pass


class Value(Exp):
    def __init__(self):
        pass

    def value(self):
        pass

    def equals(self, other):
        return RPythonizedObject.equals(self, other)

    def evaluate(self, env=None):
        return self


class NilValue(Value):
    def __init__(self):
        Value.__init__(self)

    def value(self):
        return None

    def to_string(self):
        return '%s' % (self.__class__.__name__,)


class IntegerValue(Value):
    def __init__(self, value):
        Value.__init__(self)
        assert isinstance(value, int)
        self.integer = value

    def value(self):
        return self.integer

    @staticmethod
    def from_string(number):
        assert isinstance(number, str)
        return IntegerValue(int(number))

    def to_string(self):
        return '%s(%d)' % (self.__class__.__name__, self.integer)

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.integer == other.integer


class StringValue(Value):
    def __init__(self, value):
        Value.__init__(self)
        self.string = value

    def value(self):
        return self.string

    def to_string(self):
        return '%s(%s)' % (self.__class__.__name__, self.string)

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.string == other.string


class ArrayCreation(Exp):
    def __init__(self, type, inner, outer):
        self.outer = outer
        self.inner = inner
        self.type = type

    def to_string(self):
        return '%s(outer=%s, inner=%s, type=%s)' % (
            self.__class__.__name__, self.outer.to_string(), self.inner.to_string(), self.type.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.outer.equals(other.outer) and self.inner.equals(
            other.inner) and self.type.equals(other.type)


class RecordCreation(Exp):
    def __init__(self, type, fields):
        self.type = type
        self.fields = fields

    def to_string(self):
        return '%s(type=%s, fields=%s)' % (self.__class__.__name__, self.type.to_string(), dict_to_string(self.fields))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.type.equals(other.type) and dict_equals(self.fields,
                                                                                                      other.fields)


class ObjectCreation(Exp):
    def __init__(self, type):
        self.type = type

    def to_string(self):
        return '%s(type=%s)' % (self.__class__.__name__, self.type.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.type.equals(other.type)


class TypeId(Declaration):
    def __init__(self, name):
        Declaration.__init__(self, name)

    def to_string(self):
        return '%s(name=%s)' % (self.__class__.__name__, self.name)

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name


class LValue(Exp):
    def __init__(self, name, next=None):
        self.name = name
        self.next = next

    def to_string(self):
        return '%s(name=%s, next=%s)' % (
            self.__class__.__name__, self.name, nullable_to_string(self.next))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name \
               and nullable_equals(self.next, other.next)

    def evaluate(self, env=None):
        if not env:
            raise InterpretationError('No environment available at %s' % self.to_string())
        return env.get(self.name)
        # TODO handle self.next


class RecordLValue(LValue):
    pass


class ArrayLValue(LValue):
    def __init__(self, exp, next=None):
        self.exp = exp
        self.next = next

    def to_string(self):
        return '%s(exp=%s, next=%s)' % (
            self.__class__.__name__, self.exp.to_string(), nullable_to_string(self.next))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.exp.equals(other.exp) \
               and nullable_equals(self.next, other.next)


class FunctionCall(Exp):
    def __init__(self, name, arguments):
        self.name = name
        assert (isinstance(arguments, list))
        self.arguments = arguments

    def to_string(self):
        return '%s(name=%s, args=%s)' % (self.__class__.__name__, self.name, list_to_string(self.arguments))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name \
               and list_equals(self.arguments, other.arguments)

    def evaluate(self, env=None):
        # find declaration
        declaration = env.get(self.name)
        if not declaration:
            raise InterpretationError('Could not find function %s' % self.name)

        # check arguments
        if len(self.arguments) != len(declaration.parameters):
            raise InterpretationError('Incorrect number of arguments passed (%d); expected %d for function %s' % (
                len(self.arguments), len(declaration.parameters), self.name))

        # evaluate arguments
        env.push()
        value = None
        for i in range(len(self.arguments)):
            name = declaration.parameters[i].name
            value = self.arguments[i].evaluate(env)
            # TODO type-check
            env.set(name, value)

        # evaluate body
        result = None
        if isinstance(declaration, FunctionDeclaration):
            result = declaration.body.evaluate(env)
            # TODO type-check result
        elif isinstance(declaration, NativeFunctionDeclaration):
            # only one argument is allowed due to calling RPythonized functions with var-args
            if len(self.arguments) == 1:
                result = declaration.function(value)
                assert isinstance(result, Value) if result is not None else True
                # TODO type-check result
            else:
                raise InterpretationError('Only one argument allowed in native functions: %s' % self.name)
        else:
            raise InterpretationError('Unknown function type: %s' % declaration.__class__.__name__)

        env.pop()
        return result


class MethodCall(Exp):
    # TODO remove
    def __init__(self, instance, name, args):
        self.instance = instance
        self.name = name
        self.args = args

    def to_string(self):
        return '%s(instance=%s, name=%s, args=%s)' % (
            self.__class__.__name__, self.instance, self.name, list_to_string(self.args))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.instance.equals(other.instance) and self.name.equals(
            other.name) and list_equals(self.args, other.args)


class Assign(Exp):
    def __init__(self, lvalue, expression):
        self.lvalue = lvalue
        self.expression = expression

    def to_string(self):
        return '%s(lvalue=%s, exp=%s)' % (self.__class__.__name__, self.lvalue.to_string(), self.expression.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.lvalue.equals(other.lvalue) and self.expression.equals(
            other.expression)

    def evaluate(self, env=None):
        # TODO handle other types of lvalues
        value = self.expression.evaluate(env)
        env.set(self.lvalue.name, value)


class If(Exp):
    def __init__(self, condition, body_if_true, body_if_false=None):
        self.condition = condition
        self.body_if_true = body_if_true
        self.body_if_false = body_if_false

    def to_string(self):
        return '%s(condition=%s, body_if_true=%s, body_if_false=%s)' % (
            self.__class__.__name__, self.condition.to_string(), self.body_if_true.to_string(),
            nullable_to_string(self.body_if_false))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.condition.equals(other.condition) \
               and self.body_if_true.equals(other.body_if_true) \
               and nullable_equals(self.body_if_false, other.body_if_false)

    def evaluate(self, env=None):
        condition_value = self.condition.evaluate(env)
        assert isinstance(condition_value, IntegerValue)
        if condition_value.integer != 0:
            result = self.body_if_true.evaluate(env)
        else:
            result = self.body_if_false.evaluate(env)
        return result


class While(Exp):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def to_string(self):
        return '%s(condition=%s, body=%s)' % (
            self.__class__.__name__, self.condition.to_string(), self.body.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.condition.equals(other.condition) and self.body.equals(
            other.body)

    def evaluate(self, env=None):
        condition_value = self.condition.evaluate(env)
        assert isinstance(condition_value, IntegerValue)
        result = None
        while condition_value.integer != 0:
            result = self.body.evaluate(env)
            # TODO break
            condition_value = self.condition.evaluate(env)
            # TODO jitdriver.jit_merge_point(code=self)
        return result


class For(Exp):
    def __init__(self, var, start, end, body):
        self.var = var
        self.start = start
        self.end = end
        self.body = body

    def to_string(self):
        return '%s(var=%s, start=%s, end=%s, body=%s)' % (
            self.__class__.__name__, self.var, self.start.to_string(), self.end.to_string(), self.body.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.var == other.var and self.start.equals(
            other.start) and self.end.equals(other.end) and self.body.equals(other.body)

    def evaluate(self, env=None):
        # TODO remove env is None checks
        env.push()
        start_value = self.start.evaluate(env)
        assert isinstance(start_value, IntegerValue)
        end_value = self.end.evaluate(env)
        assert isinstance(end_value, IntegerValue)
        iterator = start_value

        for i in range(iterator.integer, end_value.integer + 1):
            iterator.integer = i
            env.set_current_level(self.var, iterator)
            result = self.body.evaluate(env)
            # TODO break
            assert result is None
            jitdriver.jit_merge_point(code=self)

        env.pop()


class Break(Exp):
    pass


class Let(Exp):
    def __init__(self, declarations, expressions):
        self.declarations = declarations
        self.expressions = expressions

    def to_string(self):
        return '%s(declarations=%s, expressions=%s)' % (
            self.__class__.__name__, list_to_string(self.declarations), list_to_string(self.expressions))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) \
               and list_equals(self.declarations, other.declarations) \
               and list_equals(self.expressions, other.expressions)

    def evaluate(self, env=None):
        if not isinstance(env, Environment):
            raise InterpretationError('No environment in %s' % self.to_string())

        env.push()

        for declaration in self.declarations:
            assert isinstance(declaration, Declaration)
            declaration.evaluate(env)
        value = None
        for expression in self.expressions:
            value = expression.evaluate(env)

        env.pop()

        return value


class TypeDeclaration(Declaration):
    def __init__(self, name, type):
        Declaration.__init__(self, name)
        self.type = type

    def to_string(self):
        return '%s(name=%s, type=%s)' % (self.__class__.__name__, self.name, self.type.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name and self.type.equals(other.type)


class VariableDeclaration(Declaration):
    def __init__(self, name, type, exp):
        Declaration.__init__(self, name)
        self.type = type
        self.exp = exp

    def to_string(self):
        return '%s(name=%s, type=%s, exp=%s)' % (
            self.__class__.__name__, self.name, nullable_to_string(self.type), self.exp.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name \
               and nullable_equals(self.type, other.type) and self.exp.equals(other.exp)

    def evaluate(self, env=None):
        value = self.exp.evaluate(env)
        # TODO type-check
        env.set_current_level(self.name, value)


class FunctionParameter(Declaration):
    def __init__(self, name, type=None):
        self.name = name
        assert isinstance(type, TypeId) or type is None
        self.type = type

    def to_string(self):
        return '%s(name=%s, type=%s)' % (self.__class__.__name__, self.name, nullable_to_string(self.type))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name \
               and nullable_equals(self.type, other.type)


class FunctionDeclaration(Declaration):
    def __init__(self, name, parameters, return_type, body):
        Declaration.__init__(self, name)
        assert isinstance(parameters, list)
        self.parameters = parameters
        assert isinstance(return_type, TypeId) or return_type is None
        self.return_type = return_type
        assert isinstance(body, Exp)
        self.body = body

    def to_string(self):
        return '%s(name=%s, parameters=%s, return_type=%s, body=%s)' % (
            self.__class__.__name__, self.name, list_to_string(self.parameters), nullable_to_string(self.return_type),
            self.body.to_string())

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name \
               and list_equals(self.parameters, other.parameters) \
               and nullable_equals(self.return_type, other.return_type) \
               and self.body.equals(other.body)


class NativeFunctionDeclaration(Declaration):
    def __init__(self, name, parameters=[], return_type=None, function=None):
        Declaration.__init__(self, name)
        assert isinstance(parameters, list)
        self.parameters = parameters
        assert isinstance(return_type, TypeId) or return_type is None
        self.return_type = return_type
        self.function = function

    def to_string(self):
        return '%s(name=%s, parameters=%s, return_type=%s)' % (
            self.__class__.__name__, self.name, list_to_string(self.parameters), nullable_to_string(self.return_type))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.name == other.name \
               and list_equals(self.parameters, other.parameters) \
               and nullable_equals(self.return_type, other.return_type) \
               and nullable_equals(self.function, other.function)


class ArrayType(Type):
    def __init__(self, element_type):
        self.type_name = element_type

    def to_string(self):
        return '%s(type_name=%s)' % (self.__class__.__name__, self.type_name)

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.type_name == other.type_name


class RecordType(Type):
    def __init__(self, type_fields):
        self.type_fields = type_fields

    def to_string(self):
        return '%s(type_fields=%s)' % (self.__class__.__name__, dict_to_string(self.type_fields))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and dict_equals(self.type_fields, other.type_fields)


class Sequence(Exp):
    def __init__(self, expressions):
        self.expressions = expressions

    def to_string(self):
        return '%s(expressions=%s)' % (self.__class__.__name__, list_to_string(self.expressions))

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and list_equals(self.expressions, other.expressions)

    def evaluate(self, env=None):
        value = None
        for expression in self.expressions:
            value = expression.evaluate(env)
        return value


class BinaryOperation(Exp):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def equals(self, other):
        return RPythonizedObject.equals(self, other) and self.left.equals(other.left) and self.right.equals(other.right)

    def to_string(self):
        return '%s(left=%s, right=%s)' % (self.__class__.__name__, self.left.to_string(), self.right.to_string())

    # TODO inline
    def evaluate_sides_to_value(self, env):
        left_value = self.left.evaluate(env)
        assert isinstance(left_value, Value)
        right_value = self.right.evaluate(env)
        assert isinstance(right_value, Value)
        return left_value, right_value

    # TODO inline
    def evaluate_sides_to_int(self, env):
        left_value = self.left.evaluate(env)
        assert isinstance(left_value, IntegerValue)
        right_value = self.right.evaluate(env)
        assert isinstance(right_value, IntegerValue)
        return left_value.integer, right_value.integer


class Multiply(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(left_int * right_int)


class Divide(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(left_int // right_int)


class Add(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(left_int + right_int)


class Subtract(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(left_int - right_int)


class GreaterThanOrEquals(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(1) if left_int >= right_int else IntegerValue(0)


class LessThanOrEquals(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(1) if left_int <= right_int else IntegerValue(0)


class Equals(BinaryOperation):
    def evaluate(self, env=None):
        (left, right) = self.evaluate_sides_to_value(env)
        return IntegerValue(1) if left.equals(right) else IntegerValue(0)


class NotEquals(BinaryOperation):
    def evaluate(self, env=None):
        (left, right) = self.evaluate_sides_to_value(env)
        return IntegerValue(1) if not left.equals(right) else IntegerValue(0)


class GreaterThan(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(1) if left_int > right_int else IntegerValue(0)


class LessThan(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(1) if left_int < right_int else IntegerValue(0)


class And(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(1) if left_int and right_int else IntegerValue(0)


class Or(BinaryOperation):
    def evaluate(self, env=None):
        (left_int, right_int) = self.evaluate_sides_to_int(env)
        return IntegerValue(1) if left_int or right_int else IntegerValue(0)
