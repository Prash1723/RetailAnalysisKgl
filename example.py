from typing import IO, Iterator
import python_calamine
import pandas as pd

def iter_ec(file: IO[bytes]) -> Iterator[dict[str, object]]:
    workbook = python_calamine.CalamineWorkbook.from_filelike(file)
    rows = iter(workbook.get_sheet_by_index(0).to_python())
    headers = list(map(str, next(rows)))
    for row in rows:
        yield dict(zip(headers, row))

def load_data(file_path: str) -> pd.DataFrame:
    with open(file_path, 'rb') as f:
        rows = iter_ec(f)
        row = list(rows)
    df = pd.DataFrame(row)
    return df

if __name__ == "__main__":
    load_data("data/customer.xlsx")
