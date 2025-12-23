from typing import Any

class Field:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

Char: Field
Many2one: Field
One2many: Field
Many2many: Field
Boolean: Field
Selection: Field
Float: Field
Integer: Field
Date: Field
Datetime: Field
Binary: Field
Html: Field
Text: Field
Monetary: Field
