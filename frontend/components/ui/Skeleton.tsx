export function Skeleton({ className = '', style }: { className?: string; style?: React.CSSProperties }) {
    return <div className={`skeleton ${className}`} style={style} />
}

export function KpiSkeleton() {
    return (
        <div className="card flex flex-col gap-3 pt-4">
            <div className="flex justify-between items-start">
                <Skeleton className="h-2.5 w-20" />
                <Skeleton className="h-8 w-8 rounded-xl" />
            </div>
            <Skeleton className="h-7 w-28 mt-1" />
            <Skeleton className="h-2.5 w-24" />
        </div>
    )
}

export function ChartSkeleton({ height = 260 }: { height?: number }) {
    return (
        <div className="card">
            <div className="flex justify-between items-start mb-4">
                <Skeleton className="h-3.5 w-44" />
                <Skeleton className="h-7 w-24 rounded-lg" />
            </div>
            <Skeleton style={{ height }} />
        </div>
    )
}

export function TableSkeleton({ rows = 6 }: { rows?: number }) {
    return (
        <div className="card">
            <Skeleton className="h-3.5 w-40 mb-4" />
            <div className="space-y-2">
                <Skeleton className="h-7 w-full rounded" />
                {Array.from({ length: rows }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full" style={{ opacity: 1 - i * 0.09 }} />
                ))}
            </div>
        </div>
    )
}

export function InlineChartSkeleton({ height = 220 }: { height?: number }) {
    return <Skeleton style={{ height }} className="w-full" />
}
