'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Wheat } from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/leads', label: 'Leads', icon: Users },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/80 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-9 w-9 items-center justify-center bg-[var(--accent-primary)] transition-all group-hover:shadow-[var(--glow-amber)]">
              <Wheat className="h-5 w-5 text-[var(--bg-base)]" />
            </div>
            <div className="flex flex-col">
              <span className="font-mono text-sm font-semibold tracking-tight text-[var(--text-primary)]">
                FOOD_FINDER
              </span>
              <span className="font-mono text-[10px] text-[var(--text-muted)] tracking-widest">
                LEAD MONITOR v1.0
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== '/' && pathname.startsWith(item.href));
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 font-mono text-sm transition-all',
                    isActive
                      ? 'bg-[var(--bg-elevated)] text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Status indicator */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-[var(--success)] animate-pulse" />
              <span className="font-mono text-xs text-[var(--text-tertiary)]">
                SYSTEM ONLINE
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
