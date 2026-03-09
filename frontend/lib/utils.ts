export function formatNumber(n: number | undefined | null): string {
    if (n == null) return '—'
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
    return n.toLocaleString()
}

export function formatCurrency(n: number | undefined | null): string {
    if (n == null) return '—'
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
    if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`
    return `$${n.toFixed(2)}`
}

export function formatPct(n: number | undefined | null): string {
    if (n == null) return '—'
    return `${n.toFixed(2)}%`
}

export function formatDate(d: string): string {
    if (!d) return ''
    try {
        return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
        return d
    }
}

export function formatWeek(d: string): string {
    if (!d) return ''
    try {
        return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
        return d
    }
}
