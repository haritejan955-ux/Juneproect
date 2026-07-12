interface Column<T> {
  header: string;
  render: (row: T) => React.ReactNode;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  emptyMessage?: string;
}

export function Table<T>({ columns, rows, emptyMessage = "No data." }: TableProps<T>) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-500">{emptyMessage}</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-slate-500">
            {columns.map((column) => (
              <th key={column.header} className="py-2 pr-4 font-medium">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-slate-100 last:border-0">
              {columns.map((column) => (
                <td key={column.header} className="py-2 pr-4">
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
