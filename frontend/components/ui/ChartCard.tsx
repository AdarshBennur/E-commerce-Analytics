'use client'

import { clsx } from 'clsx'
import type { ReactNode } from 'react'

interface ChartCardProps {
    title:         string
    subtitle?:     string
    children:      ReactNode
    action?:       ReactNode
    className?:    string
    bodyClassName?: string
    noPadding?:    boolean
}

export function ChartCard({ title, subtitle, children, action, className, bodyClassName, noPadding }: ChartCardProps) {
    return (
        <div className={clsx('card animate-fade-in', className)}
            style={noPadding ? { padding: 0 } : undefined}>

            <div className={clsx(
                'flex items-start justify-between gap-4',
                noPadding ? 'px-[18px] pt-[18px] pb-4' : 'mb-4',
            )}>
                <div className="min-w-0">
                    <h3 className="section-title">{title}</h3>
                    {subtitle && <p className="section-sub">{subtitle}</p>}
                </div>
                {action && <div className="flex-shrink-0">{action}</div>}
            </div>

            <div className={clsx(noPadding ? 'px-[18px] pb-[18px]' : '', bodyClassName)}>
                {children}
            </div>
        </div>
    )
}

/* ── Section header used above grids ──────────────────────────────────── */
interface SectionHeaderProps {
    title:    string
    subtitle?: string
    action?:  ReactNode
    className?: string
}

export function SectionHeader({ title, subtitle, action, className }: SectionHeaderProps) {
    return (
        <div className={clsx('flex items-start justify-between gap-3', className)}>
            <div>
                <h2 className="text-[14px] font-semibold leading-tight" style={{ color: 'var(--text-primary)' }}>{title}</h2>
                {subtitle && <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>}
            </div>
            {action && <div className="flex-shrink-0">{action}</div>}
        </div>
    )
}

/* ── Toggle group ─────────────────────────────────────────────────────── */
interface ToggleGroupProps {
    options: { label: string; value: string }[]
    value:   string
    onChange: (v: string) => void
}

export function ToggleGroup({ options, value, onChange }: ToggleGroupProps) {
    return (
        <div className="toggle-group">
            {options.map(opt => (
                <button
                    key={opt.value}
                    onClick={() => onChange(opt.value)}
                    className={clsx('toggle-btn', value === opt.value && 'toggle-btn-active')}
                >
                    {opt.label}
                </button>
            ))}
        </div>
    )
}
