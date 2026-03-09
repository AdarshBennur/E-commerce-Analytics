'use client'

import { formatDate, formatNumber, formatCurrency, formatPct } from '@/lib/utils'

type FormatType = 'number' | 'currency' | 'percent' | 'auto'

interface TooltipEntry {
    dataKey: string
    name: string
    value: number | string
    color?: string
}

interface ChartTooltipProps {
    active?: boolean
    payload?: TooltipEntry[]
    label?: string
    labelFormat?: 'date' | 'text'
    valueFormats?: Record<string, FormatType>
}

function autoFormat(value: number, dataKey: string): string {
    const k = dataKey.toLowerCase()
    if (k.includes('revenue') || k.includes('aov') || k.includes('price') || k.includes('spend')) {
        return formatCurrency(value)
    }
    if (k.includes('pct') || k.includes('rate') || k.includes('cvr') || k.includes('retention')) {
        return `${Number(value).toFixed(2)}%`
    }
    return formatNumber(value)
}

export function ChartTooltip({ active, payload, label, labelFormat = 'date', valueFormats }: ChartTooltipProps) {
    if (!active || !payload?.length) return null

    const formattedLabel = labelFormat === 'date' ? formatDate(label ?? '') : (label ?? '')

    return (
        <div className="glass-tooltip rounded-2xl px-4 py-3 text-xs min-w-[130px]">
            {formattedLabel && (
                <p className="font-bold text-slate-800 mb-2.5 pb-2 border-b border-slate-100/80 text-[12px]">
                    {formattedLabel}
                </p>
            )}
            <div className="space-y-1.5">
                {payload.map((p, i) => {
                    const fmt = valueFormats?.[p.dataKey] ?? 'auto'
                    const val = typeof p.value === 'number'
                        ? fmt === 'auto'
                            ? autoFormat(p.value, p.dataKey)
                            : fmt === 'currency'
                                ? formatCurrency(p.value)
                                : fmt === 'number'
                                    ? formatNumber(p.value)
                                    : fmt === 'percent'
                                        ? formatPct(p.value)
                                        : String(p.value)
                        : String(p.value)

                    return (
                        <div key={i} className="flex items-center justify-between gap-5">
                            <div className="flex items-center gap-1.5">
                                <div
                                    className="w-2 h-2 rounded-full flex-shrink-0"
                                    style={{ backgroundColor: p.color }}
                                />
                                <span className="text-slate-500 font-medium">{p.name}</span>
                            </div>
                            <span className="font-bold text-slate-900 tabular-nums">{val}</span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
