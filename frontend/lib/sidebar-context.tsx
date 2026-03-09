'use client'

import { createContext, useContext, useState, useCallback, useEffect } from 'react'

interface SidebarCtx {
    collapsed: boolean
    toggle: () => void
}

const SidebarContext = createContext<SidebarCtx>({ collapsed: false, toggle: () => {} })

export function SidebarProvider({ children }: { children: React.ReactNode }) {
    const [collapsed, setCollapsed] = useState(false)

    const toggle = useCallback(() => {
        setCollapsed(prev => !prev)
    }, [])

    // Keep CSS custom property in sync so layout can use var(--sidebar-width)
    useEffect(() => {
        document.documentElement.style.setProperty(
            '--sidebar-width',
            collapsed ? 'var(--sidebar-collapsed-width)' : '240px'
        )
    }, [collapsed])

    return (
        <SidebarContext.Provider value={{ collapsed, toggle }}>
            {children}
        </SidebarContext.Provider>
    )
}

export function useSidebar() {
    return useContext(SidebarContext)
}
