/**
 * Debug Logger System
 * Provides comprehensive logging for authentication and navigation debugging
 */

export interface DebugLogEntry {
  timestamp: number;
  component: string;
  event: string;
  data?: any;
  level: 'info' | 'warn' | 'error';
}

class DebugLogger {
  private logs: DebugLogEntry[] = [];
  private maxLogs = 1000;
  private enabled = process.env.NODE_ENV === 'development';

  constructor() {
    if (this.enabled) {
      (window as any).__DEBUG_LOGGER__ = this;
      this.log('DebugLogger', 'INITIALIZED', { enabled: this.enabled });
    }
  }

  public log(component: string, event: string, data?: any, level: 'info' | 'warn' | 'error' = 'info'): void {
    if (!this.enabled) return;

    const entry: DebugLogEntry = {
      timestamp: Date.now(),
      component,
      event,
      data,
      level
    };

    this.logs.push(entry);

    // Keep only recent logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Console output with colors
    const colors = {
      info: '#2196F3',
      warn: '#FF9800', 
      error: '#F44336'
    };

    const timestamp = new Date(entry.timestamp).toLocaleTimeString();
    console.log(
      `%c[${timestamp}] [${component}] ${event}`,
      `color: ${colors[level]}; font-weight: bold`,
      data || ''
    );

    // Store in localStorage for persistence
    try {
      const recentLogs = this.logs.slice(-100); // Keep last 100 logs
      localStorage.setItem('debug_logs', JSON.stringify(recentLogs));
    } catch (error) {
      // Ignore localStorage errors
    }

    // Check for potential infinite loops
    this.detectInfiniteLoops(component, event);
  }

  public warn(component: string, event: string, data?: any): void {
    this.log(component, event, data, 'warn');
  }

  public error(component: string, event: string, data?: any): void {
    this.log(component, event, data, 'error');
  }

  public getLogs(component?: string, since?: number): DebugLogEntry[] {
    let filteredLogs = this.logs;

    if (component) {
      filteredLogs = filteredLogs.filter(log => log.component === component);
    }

    if (since) {
      filteredLogs = filteredLogs.filter(log => log.timestamp >= since);
    }

    return filteredLogs;
  }

  public getRecentLogs(minutes: number = 5): DebugLogEntry[] {
    const since = Date.now() - (minutes * 60 * 1000);
    return this.getLogs(undefined, since);
  }

  public clear(): void {
    this.logs = [];
    localStorage.removeItem('debug_logs');
    console.clear();
    this.log('DebugLogger', 'CLEARED');
  }

  public exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  public getStats(): { totalLogs: number; byComponent: Record<string, number>; byLevel: Record<string, number> } {
    const byComponent: Record<string, number> = {};
    const byLevel: Record<string, number> = {};

    this.logs.forEach(log => {
      byComponent[log.component] = (byComponent[log.component] || 0) + 1;
      byLevel[log.level] = (byLevel[log.level] || 0) + 1;
    });

    return {
      totalLogs: this.logs.length,
      byComponent,
      byLevel
    };
  }

  private detectInfiniteLoops(component: string, event: string): void {
    const recentLogs = this.getLogs(component, Date.now() - 5000); // Last 5 seconds
    const sameEventLogs = recentLogs.filter(log => log.event === event);

    if (sameEventLogs.length > 10) {
      this.error('DebugLogger', 'POTENTIAL_INFINITE_LOOP_DETECTED', {
        component,
        event,
        occurrences: sameEventLogs.length,
        timespan: '5 seconds'
      });

      // Show alert in development
      if (this.enabled) {
        console.warn(
          `🚨 POTENTIAL INFINITE LOOP DETECTED!\n` +
          `Component: ${component}\n` +
          `Event: ${event}\n` +
          `Occurrences: ${sameEventLogs.length} in 5 seconds`
        );
      }
    }
  }

  public reset(): void {
    this.clear();
    this.log('DebugLogger', 'RESET');
  }
}

// Create singleton instance
export const debugLogger = new DebugLogger();

// Navigation-specific logging helpers
export const logNavigation = (from: string, to: string, reason: string, data?: any) => {
  debugLogger.log('Navigation', 'ROUTE_CHANGE', { from, to, reason, ...data });
};

export const logAuthEvent = (event: string, data?: any) => {
  debugLogger.log('Auth', event, data);
};

export const logComponentMount = (component: string, props?: any) => {
  debugLogger.log(component, 'MOUNT', props);
};

export const logComponentUnmount = (component: string) => {
  debugLogger.log(component, 'UNMOUNT');
};

export const logStateChange = (component: string, oldState: any, newState: any) => {
  debugLogger.log(component, 'STATE_CHANGE', { oldState, newState });
};

// Export for global access in development
if (process.env.NODE_ENV === 'development') {
  (window as any).__DEBUG_LOGGER__ = debugLogger;
  (window as any).debugLogger = debugLogger;
  (window as any).logNavigation = logNavigation;
  (window as any).logAuthEvent = logAuthEvent;
}