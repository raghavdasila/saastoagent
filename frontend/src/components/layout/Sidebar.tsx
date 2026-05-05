import { NavLink, useParams } from 'react-router-dom'

const navItems = [
  { label: 'Overview', path: '' },
  { label: 'Connections', path: '/connections' },
  { label: 'Chat', path: '/chat' },
]

export function Sidebar() {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const basePath = `/w/${workspaceId}`

  return (
    <aside className="w-full border-b bg-sidebar text-sidebar-foreground md:min-h-[calc(100vh-3.5rem)] md:w-64 md:border-b-0 md:border-r">
      <div className="border-b border-sidebar-accent px-4 py-4">
        <p className="text-sm font-semibold">Workspace Agent</p>
        <p className="mt-1 text-xs text-sidebar-foreground/70">Slice 1 shell</p>
      </div>
      <nav className="flex gap-2 overflow-x-auto px-3 py-3 md:flex-col">
        {navItems.map((item) => (
          <NavLink
            key={item.label}
            to={`${basePath}${item.path}`}
            end={item.path === ''}
            className={({ isActive }) =>
              [
                'rounded-md px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors',
                isActive
                  ? 'bg-sidebar-accent text-sidebar-foreground'
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground',
              ].join(' ')
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
