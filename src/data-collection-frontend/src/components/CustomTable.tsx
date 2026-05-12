import { useEffect, useState } from 'react'
import type { Key, ReactNode } from 'react'
import { toast } from 'sonner'
import { requestJson } from '../actions'
import { panelLabelClass, summaryPillClass } from '../ui/classes'

const tableHeaderCellClass =
  'border-b border-slate-400/10 bg-[#070b12]/50 px-[18px] py-4 text-left align-top text-xs font-semibold tracking-[0.12em] text-[#738099] uppercase'
const tableBodyCellClass =
  'border-b border-slate-400/10 px-[18px] py-4 align-top'
const actionButtonClass =
  'inline-flex h-9 w-9 cursor-pointer items-center justify-center rounded-[12px] border border-slate-400/15 bg-slate-400/5 text-[#738099] transition duration-150 hover:-translate-y-px hover:border-emerald-300/35 hover:bg-slate-400/10 hover:text-[#f5f7fb] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300/60 disabled:cursor-not-allowed disabled:opacity-50'

export type CustomTableColumn<Row> = {
  id: string
  header: string
  render: (row: Row) => ReactNode
  className?: string
  headerClassName?: string
}

export type CustomTableAction<Row> = {
  id: string
  label: string
  onClick: (row: Row) => void | Promise<void>
  icon: ReactNode | ((row: Row) => ReactNode)
  ariaLabel?: (row: Row) => string
  className?: string
  isDisabled?: (row: Row) => boolean
}

type CustomTableProps<Row> = {
  label: string
  columns: CustomTableColumn<Row>[]
  actions?: CustomTableAction<Row>[]
  url: string
  getRowKey: (row: Row) => Key
  onRowClick?: (row: Row) => void
  rowAriaLabel?: (row: Row) => string
  refreshKey?: number
  emptyDescription?: string
}

export default function CustomTable<Row>({
  label,
  columns,
  actions = [],
  url,
  getRowKey,
  onRowClick,
  rowAriaLabel,
  refreshKey = 0,
  emptyDescription,
}: CustomTableProps<Row>) {
  const [rows, setRows] = useState<Row[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const normalizedLabel = label.trim()
  const heading = toTitleCase(normalizedLabel)

  useEffect(() => {
    let isCancelled = false

    const loadRows = async () => {
      setIsLoading(true)

      try {
        const nextRows = await requestJson<Row[]>(url)

        if (!isCancelled) {
          setRows(nextRows)
        }
      } catch {
        if (!isCancelled) {
          setRows([])
          toast.error(`Unable to load ${normalizedLabel}`)
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadRows()

    return () => {
      isCancelled = true
    }
  }, [normalizedLabel, refreshKey, url])

  if (isLoading) {
    return (
      <>
        <TableHeader heading={heading} statusLabel="Loading" />
        <TableState title={`Loading ${normalizedLabel}`} />
      </>
    )
  }

  if (rows.length === 0) {
    return (
      <>
        <TableHeader heading={heading} statusLabel={`0 ${normalizedLabel}`} />
        <TableState
          title={`No ${normalizedLabel} found`}
          description={emptyDescription}
        />
      </>
    )
  }

  const isRowClickable = Boolean(onRowClick)

  return (
    <>
      <TableHeader
        heading={heading}
        statusLabel={`${rows.length} ${normalizedLabel}`}
      />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[780px] border-collapse">
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.id}
                  className={[tableHeaderCellClass, column.headerClassName]
                    .filter(Boolean)
                    .join(' ')}
                  scope="col"
                >
                  {column.header}
                </th>
              ))}
              {actions.length > 0 ? (
                <th
                  className="w-16 border-b border-slate-400/10 bg-[#070b12]/50 px-[18px] py-4 text-right align-top"
                  scope="col"
                  aria-label="Actions"
                />
              ) : null}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={getRowKey(row)}
                className={[
                  '[&:last-child>td]:border-b-0',
                  isRowClickable
                    ? 'cursor-pointer outline-none transition-colors duration-150 hover:bg-slate-400/5 focus-visible:bg-slate-400/5 focus-visible:[&>td:first-child]:shadow-[inset_3px_0_0_#3dd9b3]'
                    : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
                tabIndex={isRowClickable ? 0 : undefined}
                role={isRowClickable ? 'button' : undefined}
                aria-label={isRowClickable ? rowAriaLabel?.(row) : undefined}
                onClick={isRowClickable ? () => onRowClick?.(row) : undefined}
                onKeyDown={
                  isRowClickable
                    ? (event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault()
                          onRowClick?.(row)
                        }
                      }
                    : undefined
                }
              >
                {columns.map((column) => (
                  <td
                    key={column.id}
                    className={[tableBodyCellClass, column.className]
                      .filter(Boolean)
                      .join(' ')}
                  >
                    {column.render(row)}
                  </td>
                ))}
                {actions.length > 0 ? (
                  <td className={`${tableBodyCellClass} text-right`}>
                    <div className="inline-flex items-center justify-end gap-2">
                      {actions.map((action) => {
                        const actionIcon =
                          typeof action.icon === 'function'
                            ? action.icon(row)
                            : action.icon

                        return (
                          <button
                            key={action.id}
                            className={[actionButtonClass, action.className]
                              .filter(Boolean)
                              .join(' ')}
                            type="button"
                            aria-label={action.ariaLabel?.(row) ?? action.label}
                            disabled={action.isDisabled?.(row) ?? false}
                            onClick={(event) => {
                              event.stopPropagation()
                              void action.onClick(row)
                            }}
                            onKeyDown={(event) => {
                              event.stopPropagation()
                            }}
                          >
                            {actionIcon}
                          </button>
                        )
                      })}
                    </div>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

type TableHeaderProps = {
  heading: string
  statusLabel: string
}

function TableHeader({ heading, statusLabel }: TableHeaderProps) {
  return (
    <header className="flex items-start justify-between gap-[18px] border-b border-slate-400/10 px-[22px] py-5 max-[720px]:grid">
      <h2 className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]">
        {heading}
      </h2>
      <div className={`${summaryPillClass} max-[720px]:w-fit`}>{statusLabel}</div>
    </header>
  )
}

type TableStateProps = {
  title: string
  description?: string
}

function TableState({ title, description }: TableStateProps) {
  return (
    <div className="grid min-h-[220px] place-items-center p-9 text-center text-[#a8b0c3]">
      <div className="max-w-[460px]">
        <p className={panelLabelClass}>Status</p>
        <h3 className="mt-2.5 mb-2 text-[1.05rem] font-semibold tracking-normal text-current">
          {title}
        </h3>
        {description ? <p className="mb-0">{description}</p> : null}
      </div>
    </div>
  )
}

function toTitleCase(value: string) {
  if (!value) {
    return value
  }

  return value.charAt(0).toUpperCase() + value.slice(1)
}
