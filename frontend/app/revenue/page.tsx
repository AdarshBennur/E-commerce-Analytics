'use client'

import { useState, useEffect, useCallback } from 'react'
import { useFilters } from '@/lib/filter-context'
import { fetchRevenue } from '@/lib/api'
import type { RevenueData } from '@/lib/types'
import { formatCurrency, formatNumber, formatDate } from '@/lib/utils'
import {
    AreaChart, Area, LineChart, Line, BarChart, Bar,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LabelList, Cell,
} from 'recharts'
import { KpiSkeleton, InlineChartSkeleton } from '@/components/ui/Skeleton'
import { ChartCard, ToggleGroup } from '@/components/ui/ChartCard'
import { KpiCard } from '@/components/ui/KpiCard'
import { ChartTooltip } from '@/components/ui/ChartTooltip'
import { DollarSign, ShoppingCart, Package, Users } from 'lucide-react'

const C = { revenue: '#4F46E5', orders: '#10B981', aov: '#F59E0B' }
const PALETTE = ['#4F46E5', '#2563EB', '#14B8A6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#06B6D4']
const AXIS_TICK = { fontSize: 10, fill: '#94A3B8', fontWeight: 500 }

export default function RevenuePage() {
    const { filters } = useFilters()
    const [data, setData]       = useState<RevenueData | null>(null)
    const [loading, setLoading] = useState(true)
    const [gran, setGran]       = useState<'daily' | 'weekly'>('daily')

    const load = useCallback(async () => {
        setLoading(true)
        try {
            setData(await fetchRevenue({
                start_date:  filters.startDate || undefined,
                end_date:    filters.endDate   || undefined,
                granularity: gran,
            }))
        } finally { setLoading(false) }
    }, [filters.startDate, filters.endDate, gran])

    useEffect(() => { load() }, [load])

    const kpis = data?.kpis
    const ts   = data?.timeseries  ?? []
    const cats = data?.by_category ?? []

    return (
        <div className="space-y-5 animate-fade-in">

            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {loading ? Array.from({ length: 4 }).map((_, i) => <KpiSkeleton key={i} />) : <>
                    <KpiCard label="Total Revenue"   value={formatCurrency(kpis?.total_revenue)}   sub="Total GMV"             icon={<DollarSign   className="w-4 h-4" />} accent="blue"   />
                    <KpiCard label="Total Orders"    value={formatNumber(kpis?.total_orders)}       sub="Completed purchases"   icon={<ShoppingCart className="w-4 h-4" />} accent="green"  />
                    <KpiCard label="Avg Order Value" value={formatCurrency(kpis?.avg_order_value)}  sub="Revenue per order"     icon={<Package      className="w-4 h-4" />} accent="orange" />
                    <KpiCard label="Unique Buyers"   value={formatNumber(kpis?.unique_buyers)}      sub="Distinct purchasers"   icon={<Users        className="w-4 h-4" />} accent="purple" />
                </>}
            </div>

            {/* Revenue over time */}
            <ChartCard
                title="Revenue & Orders over Time"
                subtitle="GMV and order count by day or week"
                action={
                    <ToggleGroup
                        options={[{ label: 'Daily', value: 'daily' }, { label: 'Weekly', value: 'weekly' }]}
                        value={gran}
                        onChange={v => setGran(v as 'daily' | 'weekly')}
                    />
                }
            >
                {loading ? <InlineChartSkeleton height={256} /> : (
                    <ResponsiveContainer width="100%" height={256}>
                        <AreaChart data={ts} margin={{ top: 4, right: 4, bottom: 0, left: -12 }}>
                            <defs>
                                <linearGradient id="gRev" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%"  stopColor={C.revenue} stopOpacity={0.22} />
                                    <stop offset="95%" stopColor={C.revenue} stopOpacity={0.01} />
                                </linearGradient>
                                <linearGradient id="gOrd" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%"  stopColor={C.orders} stopOpacity={0.16} />
                                    <stop offset="95%" stopColor={C.orders} stopOpacity={0.01} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.55)" vertical={false} />
                            <XAxis dataKey="date"  tick={AXIS_TICK} tickFormatter={formatDate} axisLine={false} tickLine={false} />
                            <YAxis yAxisId="left"  tick={AXIS_TICK} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} width={48} axisLine={false} tickLine={false} />
                            <YAxis yAxisId="right" orientation="right" tick={AXIS_TICK} tickFormatter={formatNumber} width={44} axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTooltip valueFormats={{ revenue: 'currency', orders: 'number' }} />} />
                            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                            <Area yAxisId="left"  type="monotone" dataKey="revenue" name="Revenue" stroke={C.revenue} fill="url(#gRev)" strokeWidth={2.5} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                            <Area yAxisId="right" type="monotone" dataKey="orders"  name="Orders"  stroke={C.orders}  fill="url(#gOrd)" strokeWidth={2}   dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </ChartCard>

            {/* AOV + by_category */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">

                <ChartCard title="Average Order Value Trend" subtitle="AOV fluctuation over time">
                    {loading ? <InlineChartSkeleton height={220} /> : (
                        <ResponsiveContainer width="100%" height={220}>
                            <LineChart data={ts} margin={{ top: 4, right: 4, bottom: 0, left: -12 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.55)" vertical={false} />
                                <XAxis dataKey="date" tick={AXIS_TICK} tickFormatter={formatDate} axisLine={false} tickLine={false} />
                                <YAxis tick={AXIS_TICK} tickFormatter={v => `$${Number(v).toFixed(0)}`} width={44} axisLine={false} tickLine={false} />
                                <Tooltip content={<ChartTooltip valueFormats={{ aov: 'currency' }} />} />
                                <Line type="monotone" dataKey="aov" name="AOV" stroke={C.aov} strokeWidth={2.5} dot={false} activeDot={{ r: 5, strokeWidth: 0 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    )}
                </ChartCard>

                <ChartCard title="Revenue by Category" subtitle="GMV contribution from top categories">
                    {loading ? <InlineChartSkeleton height={220} /> : (
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={cats.slice(0, 8)} layout="vertical" margin={{ left: 0, right: 56, top: 4, bottom: 4 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(226,232,240,0.55)" horizontal={false} />
                                <XAxis type="number" tick={AXIS_TICK} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} axisLine={false} tickLine={false} />
                                <YAxis type="category" dataKey="category" tick={{ ...AXIS_TICK, fill: '#64748b', fontSize: 9.5 }} width={92} axisLine={false} tickLine={false} />
                                <Tooltip formatter={(v: any) => [formatCurrency(v), 'Revenue']} contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #E2E8F0', background: '#FFFFFF', boxShadow: '0 8px 24px rgba(15,23,42,0.10)' }} />
                                <Bar dataKey="revenue" radius={[0, 8, 8, 0]}>
                                    <LabelList dataKey="revenue" position="right" formatter={(v: any) => `$${(v/1000).toFixed(0)}K`} style={{ fontSize: 9.5, fontWeight: 700, fill: '#475569' }} />
                                    {cats.slice(0, 8).map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    )}
                </ChartCard>
            </div>
        </div>
    )
}
