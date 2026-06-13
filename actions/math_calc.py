# math_calc.py
import ast
import operator as op

# Safe math evaluator using AST
_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

def _eval_node(node):
    if isinstance(node, ast.Num):  # python < 3.8
        return node.n
    elif isinstance(node, ast.Constant):  # python >= 3.8
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Operator {op_type.__name__} is not allowed.")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](operand)
        raise ValueError(f"Unary operator {op_type.__name__} is not allowed.")
    else:
        raise ValueError(f"Expression type {type(node).__name__} is not allowed.")

def safe_eval(expr: str):
    """Safely evaluates math expressions."""
    # Clean the expression
    expr = expr.replace("x", "*").replace("X", "*").strip()
    try:
        tree = ast.parse(expr, mode='eval')
        return _eval_node(tree.body)
    except Exception as e:
        raise ValueError(f"Invalid math expression: {e}")


def math_calc(
    parameters: dict,
    player=None,
) -> str:
    """
    Evaluates math expressions or performs unit conversions.
    """
    action = parameters.get("action", "").lower().strip()
    
    if player:
        player.write_log(f"[MathCalc] Action: {action}")

    if not action:
        return "Sir, please specify an action ('evaluate' or 'convert')."

    if action in ("evaluate", "calc", "calculate"):
        expression = parameters.get("expression", "")
        if not expression:
            return "Sir, please provide a math expression to calculate."
        try:
            result = safe_eval(expression)
            return f"Calculation Result: {result}"
        except Exception as e:
            return f"Sir, I couldn't evaluate that expression. Error: {e}"

    elif action in ("convert", "unit_convert"):
        value_str = parameters.get("value", "0")
        try:
            value = float(value_str)
        except ValueError:
            return f"Sir, '{value_str}' is not a valid number."

        from_unit = parameters.get("from", "").lower().strip()
        to_unit = parameters.get("to", "").lower().strip()

        if not from_unit or not to_unit:
            return "Sir, please provide both 'from' and 'to' units."

        # Temperature
        if from_unit in ("c", "celsius") and to_unit in ("f", "fahrenheit"):
            res = (value * 9/5) + 32
            return f"{value}°C = {res:.2f}°F"
        elif from_unit in ("f", "fahrenheit") and to_unit in ("c", "celsius"):
            res = (value - 32) * 5/9
            return f"{value}°F = {res:.2f}°C"
        elif from_unit in ("c", "celsius") and to_unit in ("k", "kelvin"):
            res = value + 273.15
            return f"{value}°C = {res:.2f} K"
        elif from_unit in ("k", "kelvin") and to_unit in ("c", "celsius"):
            res = value - 273.15
            return f"{value} K = {res:.2f}°C"

        # Length / Distance
        elif from_unit in ("km", "kilometer", "kilometers") and to_unit in ("mi", "mile", "miles"):
            res = value * 0.621371
            return f"{value} km = {res:.4f} miles"
        elif from_unit in ("mi", "mile", "miles") and to_unit in ("km", "kilometer", "kilometers"):
            res = value / 0.621371
            return f"{value} miles = {res:.4f} km"
        elif from_unit in ("m", "meter", "meters") and to_unit in ("ft", "feet"):
            res = value * 3.28084
            return f"{value} meters = {res:.2f} feet"
        elif from_unit in ("ft", "feet") and to_unit in ("m", "meter", "meters"):
            res = value / 3.28084
            return f"{value} feet = {res:.2f} meters"

        # Weight / Mass
        elif from_unit in ("kg", "kilogram", "kilograms") and to_unit in ("lb", "lbs", "pound", "pounds"):
            res = value * 2.20462
            return f"{value} kg = {res:.2f} lbs"
        elif from_unit in ("lb", "lbs", "pound", "pounds") and to_unit in ("kg", "kilogram", "kilograms"):
            res = value / 2.20462
            return f"{value} lbs = {res:.2f} kg"

        # Volume
        elif from_unit in ("l", "liter", "liters") and to_unit in ("gal", "gallon", "gallons"):
            res = value * 0.264172
            return f"{value} liters = {res:.3f} gallons"
        elif from_unit in ("gal", "gallon", "gallons") and to_unit in ("l", "liter", "liters"):
            res = value / 0.264172
            return f"{value} gallons = {res:.3f} liters"

        else:
            return f"Sir, conversion from '{from_unit}' to '{to_unit}' is currently unsupported."

    else:
        return f"Sir, math_calc action '{action}' is not recognized."
