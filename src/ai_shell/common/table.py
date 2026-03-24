from typing import List, Optional, Sequence, Type

from pydantic import BaseModel
from rich.table import Table


class Column(BaseModel):
    name: str
    max_width: Optional[int] = None
    no_wrap: bool = False


def default_rich_table(
    T: Type[BaseModel], items: Sequence[BaseModel], columns: List[Column] = None
) -> Table:
    if not columns:
        columns = [Column(name=x) for x in T.model_fields.keys()]
    table = Table()
    for column in columns:
        table.add_column(
            column.name, max_width=column.max_width, no_wrap=column.no_wrap
        )
    for item in items:
        json_item = item.model_dump(mode="json")
        table.add_row(*[json_item.get(column.name) for column in columns])
    return table
