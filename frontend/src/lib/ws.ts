/**
 * WebSocket 客户端 — 自动重连 + catchup (?since=last_event_id)。
 *
 * Plan 1 RedisStreamsBus 把事件推到后端 /ws；客户端订阅，断线重连时
 * 带上最后一个 event_id 让后端回放（GET /api/events/catchup?since=...）。
 */

export type EventEnvelope = {
  event_id: string
  account_id: number
  trading_mode: string
  occurred_at: string
  trace_id: string
  schema_version: number
  event_type: string
  payload: Record<string, unknown>
}

export type EventHandler = (envelope: EventEnvelope) => void

interface Options {
  url?: string
  token?: string
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectDelayMs?: number
}

const DEFAULT_RECONNECT_DELAY = 2_000

export class EventBusClient {
  private url: string
  private token?: string
  private socket: WebSocket | null = null
  private handlers: Map<string, Set<EventHandler>> = new Map()
  private lastEventId: string | null = null
  private opts: Required<Pick<Options, 'reconnectDelayMs'>>
  private onConnect?: () => void
  private onDisconnect?: () => void
  private intentionallyClosed = false

  constructor(options: Options = {}) {
    const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:'
    const proto = isHttps ? 'wss' : 'ws'
    const host = typeof window !== 'undefined' ? window.location.host : 'localhost:8000'
    this.url = options.url || `${proto}://${host}/ws`
    this.token = options.token
    this.onConnect = options.onConnect
    this.onDisconnect = options.onDisconnect
    this.opts = { reconnectDelayMs: options.reconnectDelayMs ?? DEFAULT_RECONNECT_DELAY }
  }

  connect() {
    this.intentionallyClosed = false
    const url = new URL(this.url)
    if (this.lastEventId) url.searchParams.set('since', this.lastEventId)
    if (this.token) url.searchParams.set('token', this.token)

    this.socket = new WebSocket(url.toString())
    this.socket.onopen = () => this.onConnect?.()
    this.socket.onmessage = (e) => this.dispatch(e.data)
    this.socket.onclose = () => {
      this.onDisconnect?.()
      if (!this.intentionallyClosed) {
        setTimeout(() => this.connect(), this.opts.reconnectDelayMs)
      }
    }
    this.socket.onerror = () => this.socket?.close()
  }

  disconnect() {
    this.intentionallyClosed = true
    this.socket?.close()
  }

  on(eventType: string, handler: EventHandler) {
    let set = this.handlers.get(eventType)
    if (!set) {
      set = new Set()
      this.handlers.set(eventType, set)
    }
    set.add(handler)
    return () => set!.delete(handler)
  }

  private dispatch(raw: string) {
    let env: EventEnvelope
    try {
      env = JSON.parse(raw)
    } catch {
      return
    }
    this.lastEventId = env.event_id
    this.handlers.get('*')?.forEach((h) => h(env))
    this.handlers.get(env.event_type)?.forEach((h) => h(env))
  }
}
