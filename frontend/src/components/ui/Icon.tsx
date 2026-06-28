/**
 * Icon — lucide-react 薄封装。沿用参考 UI Kit 的 `<Icon name="..." />` API，
 * 方便从设计稿移植；name 映射到 lucide 组件，未知名回退 Circle。
 */
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Bell,
  BookOpen,
  Brain,
  ChevronDown,
  ChevronRight,
  Circle,
  Clock,
  Coins,
  Gauge,
  Layers,
  LayoutDashboard,
  LineChart,
  List,
  LogOut,
  Menu,
  Pause,
  Play,
  RefreshCw,
  ScrollText,
  Search,
  Settings,
  Shield,
  ShieldAlert,
  Sliders,
  TrendingDown,
  TrendingUp,
  Wallet,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react'

const REGISTRY: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  brain: Brain,
  layers: Layers,
  chart: LineChart,
  shield: Shield,
  'shield-alert': ShieldAlert,
  list: List,
  'scroll-text': ScrollText,
  settings: Settings,
  sliders: Sliders,
  search: Search,
  bell: Bell,
  play: Play,
  pause: Pause,
  check: Circle,
  x: X,
  'arrow-up': ArrowUp,
  'arrow-down': ArrowDown,
  alert: AlertTriangle,
  bolt: Zap,
  clock: Clock,
  book: BookOpen,
  'chevron-right': ChevronRight,
  'chevron-down': ChevronDown,
  circle: Circle,
  wallet: Wallet,
  coins: Coins,
  activity: Activity,
  refresh: RefreshCw,
  logout: LogOut,
  menu: Menu,
  'trending-up': TrendingUp,
  'trending-down': TrendingDown,
  gauge: Gauge,
}

export interface IconProps {
  name: string
  size?: number
  color?: string
  strokeWidth?: number
  className?: string
}

export function Icon({ name, size = 16, color = 'currentColor', strokeWidth = 1.8, className }: IconProps) {
  const Cmp = REGISTRY[name] ?? Circle
  return <Cmp size={size} color={color} strokeWidth={strokeWidth} className={className} aria-hidden />
}
