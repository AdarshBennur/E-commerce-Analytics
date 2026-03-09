'use client'

import { useState, useEffect, useCallback } from 'react'
import { useFilters } from '@/lib/filter-context'
import { fetchOverview } from '@/lib/api'
import type { OverviewData } from '@/lib/types'
import { KpiCard } from '@/components/ui/KpiCard'
import { KpiSkeleton, InlineChartSkeleton } from '@/components/ui/Skeleton'
import { ChartCard, ToggleGroup } from '@/components/ui/ChartCard'
import { ChartTooltip } from '@/components/ui/ChartTooltip'
import { formatNumber, formatCurrency, formatPct, formatDate } from '@/lib/utils'
import {
    AreaChart, Area, LineChart, Line,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Users, ShoppingCart, DollarSign, TrendingUp, Package, Activity } from 'lucide-react'

const C = {
    dau:       '#4F46E5',   /* indigo      */
    sessions:  '#2563EB',   /* royal blue  */
    purchases: '#10B981',   /* emerald     */
    revenue:   '#F59E0B',   /* amber       */
    views:     '#4F46E5',
    carts:     '#14B8A6',   /* teal        */
}

const AXIS_TICK = { fontSize: 10, fill: '#94A3B8', fontWeight: 500 }

export default function OverviewPage() {
    const { filters } = useFilters()
    const [data, setData]       = useState<OverviewData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError]     = useState<string | null>(null)
    const [chartMode, setChartMode] = useState<'area' | 'line'>('area')

    const load = useCallback(async () => {
        setLoading(true); setError(null)
        try {
            setData(await fetchOverview({
                start_date: filters.startDate || undefined,
                end_date:   filters.endDate   || undefined,
            }))
        } catch (e: any) { setError(e.message) }
        finally { setLoading(false) }
    }, [filters.startDate, filters.endDate])

    useEffect(() => { load() }, [load])

    const kpis = data?.kpis
    const ts   = data?.timeseries ?? []

    if (error) return (
        <div className="flex items-center justify-center h-64">
            <div className="glass-card text-center px-8 py-10 max-w-sm">
                <p className="text-slate-400 text-sm">{error}</p>
            </div>
        </div>
    )

    return (
        <div className="space-y-5 animate-fade-in">

            {/* KPI Row */}
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-4">
                {loading
                    ? Array.from({ length: 6 }).map((_, i) => <KpiSkeleton key={i} />)
                    : <>
                        <KpiCard label="Total Users"     value={formatNumber(kpis?.total_users_approx)} sub="Unique visitors"    icon={<Users        className="w-4 h-4" />} accent="blue"   />
                        <KpiCard label="Sessions"        value={formatNumber(kpis?.total_sessions)}     sub="All user sessions"  icon={<Activity     className="w-4 h-4" />} accent="purple" />
                        <KpiCard label="Purchases"       value={formatNumber(kpis?.total_purchases)}    sub="Completed orders"   icon={<ShoppingCart className="w-4 h-4" />} accent="green"  />
                        <KpiCard label="Revenue"         value={formatCurrency(kpis?.total_revenue)}    sub="Total GMV"          icon={<DollarSign   className="w-4 h-4" />} accent="orange" />
                        <KpiCard label="Conversion Rate" value={formatPct(kpis?.conversion_rate)}       sub="Session → Purchase" icon={<TrendingUp   className="w-4 h-4" />} accent="green"  />
                        <KpiCard label="Avg Order Value" value={formatCurrency(kpis?.avg_order_value)}  sub="Per transaction"    icon={<Package      className="w-4 h-4" />} accent="blue"   />
                    </>
                }
            </div>

            {/* Row 1: DAU/Sessions + Purchases/Revenue */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">

                <ChartCard title="Daily Active Users & Sessions" subtitle="Unique visitors and total sessions per day">
                    {loading ? <InlineChartSkeleton height={240} /> : (
                        <ResponsiveContainer width="100%" height={240}>
                            <AreaChart data={ts} margin={{ top: 4, right: 4, bottom: 0, left: -12 }}>
                                <defs>
                                    <linearGradient id="gDau" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%"  stopColor={C.dau}      stopOpacity={0.20} />
                                        <stop offset="95%" stopColor={C.dau}      stopOpacity={0.01} />
                                    </linearGradient>
                                    <linearGradient id="gSess" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%"  stopColor={C.sessions} stopOpacity={0.16} />
                                        <stop offset="95%" stopColor={C.sessions} stopOpacity={0.01} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.55)" vertical={false} />
                                <XAxis dataKey="date"  tick={AXIS_TICK} tickFormatter={formatDate} axisLine={false} tickLine={false} />
                                <YAxis                 tick={AXIS_TICK} tickFormatter={formatNumber} width={44}     axisLine={false} tickLine={false} />
                                <Tooltip content={<ChartTooltip />} />
                                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                                <Area type="monotone" dataKey="dau"      name="DAU"      stroke={C.dau}      fill="url(#gDau)"  strokeWidth={2.5} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                                <Area type="monotone" dataKey="sessions" name="Sessions" stroke={C.sessions} fill="url(#gSess)" strokeWidth={2}   dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                            </AreaChart>
                        </ResponsiveContainer>
                    )}
                </ChartCard>

                <ChartCard title="Purchase Volume & Revenue" subtitle="Orders completed and GMV generated daily">
                    {loading ? <InlineChartSkeleton height={240} /> : (
                        <ResponsiveContainer width="100%" height={240}>
                            <LineChart data={ts} margin={{ top: 4, right: 4, bottom: 0, left: -12 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.55)" vertical={false} />
                                <XAxis dataKey="date" tick={AXIS_TICK} tickFormatter={formatDate} axisLine={false} tickLine={false} />
                                <YAxis yAxisId="left"  tick={AXIS_TICK} tickFormatter={formatNumber}                             width={44} axisLine={false} tickLine={false} />
                                <YAxis yAxisId="right" orientation="right" tick={AXIS_TICK} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} width={46} axisLine={false} tickLine={false} />
                                <Tooltip content={<ChartTooltip />} />
                                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                                <Line yAxisId="left"  type="monotone" dataKey="purchases" name="Purchases" stroke={C.purchases} strokeWidth={2.5} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                                <Line yAxisId="right" type="monotone" dataKey="revenue"   name="Revenue"   stroke={C.revenue}   strokeWidth={2}   dot={false} activeDot={{ r: 4, strokeWidth: 0 }} strokeDasharray="5 3" />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </ChartCard>
            </div>

            {/* Row 2: Event Volume */}
            <ChartCard
                title="Event Volume — Views · Carts · Purchases"
                subtitle="Full funnel event volume trend over time"
                action={
                    <ToggleGroup
                        options={[{ label: 'Area', value: 'area' }, { label: 'Line', value: 'line' }]}
                        value={chartMode}
                        onChange={v => setChartMode(v as 'area' | 'line')}
                    />
                }
            >
                {loading ? <InlineChartSkeleton height={196} /> : (
                    <ResponsiveContainer width="100%" height={196}>
                        <AreaChart data={ts} margin={{ top: 4, right: 4, bottom: 0, left: -12 }}>
                            <defs>
                                <linearGradient id="gViews" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%"  stopColor={C.views} stopOpacity={0.18} />
                                    <stop offset="95%" stopColor={C.views} stopOpacity={0.01} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.55)" vertical={false} />
                            <XAxis dataKey="date"  tick={AXIS_TICK} tickFormatter={formatDate} axisLine={false} tickLine={false} />
                            <YAxis                 tick={AXIS_TICK} tickFormatter={formatNumber} width={44}     axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTooltip />} />
                            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                            <Area type="monotone" dataKey="views"     name="Views"     stroke={C.views}     fill="url(#gViews)" strokeWidth={2}   dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                            <Area type="monotone" dataKey="carts"     name="Carts"     stroke={C.carts}     fill="none"         strokeWidth={1.5} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                            <Area type="monotone" dataKey="purchases" name="Purchases" stroke={C.purchases} fill="none"         strokeWidth={1.5} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </ChartCard>
        </div>
    )
}
