import React from "react";
import clsx from "clsx";

export default function DataTable({ columns, rows, onRowClick }) {
  return (
    <div className="panel overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-stone-800">
            {columns.map((c) => (
              <th
                key={c.key}
                className={clsx(
                  "micro text-stone-500 px-4 py-2 text-left font-normal",
                  c.align === "right" && "text-right",
                  c.align === "center" && "text-center"
                )}
                style={{ width: c.width }}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr
              key={r.id ?? i}
              onClick={() => onRowClick?.(r)}
              className={clsx(
                "border-b border-stone-800/60 hover:bg-stone-800/40 transition-colors",
                onRowClick && "cursor-pointer"
              )}
              style={{ height: 28 }}
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={clsx(
                    "px-4 text-[13px]",
                    c.align === "right" && "text-right",
                    c.align === "center" && "text-center",
                    c.mono && "num"
                  )}
                >
                  {c.render ? c.render(r) : r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
