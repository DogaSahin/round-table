// frontend/src/modules/maps/ws.ts
//
// This is the first frontend WS client in the repo, so there is no existing
// shared core WS composable/wrapper to extend. This helper is deliberately
// small and scoped to the maps module only -- if a future module needs a WS
// connection too, a shared abstraction should be extracted then, not now.
//
// Protocol (see backend/app/core/realtime/routes.py): connect to `/ws?topic=<t>`
// to subscribe to the initial topic, then send `{"action":"subscribe","topic":<t>}`
// text frames to add more topics on the same socket. Messages arrive as the raw
// dict passed to manager.publish(topic, payload) -- no envelope wrapper.

export interface MapSocketHandlers {
  onMapChanged: () => void
  onTokenMove: (tokenId: number, x: number, y: number) => void
}

function wsUrl(topic: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws?topic=${encodeURIComponent(topic)}`
}

/** Connects to a map's public topic (`map:{id}`) and, since this view is
 * DM-only, also subscribes to its DM-only topic (`map:{id}:dm`) on the same
 * socket. Returns a disconnect function. */
export function connectMapSocket(mapId: number, handlers: MapSocketHandlers): () => void {
  const socket = new WebSocket(wsUrl(`map:${mapId}`))

  socket.addEventListener('open', () => {
    socket.send(JSON.stringify({ action: 'subscribe', topic: `map:${mapId}:dm` }))
  })

  socket.addEventListener('message', (event) => {
    let message: unknown
    try {
      message = JSON.parse(event.data as string)
    } catch {
      return
    }
    if (typeof message !== 'object' || message === null) return
    const record = message as Record<string, unknown>

    if (record.action === 'map_changed') {
      handlers.onMapChanged()
      return
    }
    if (
      record.action === 'token.move' &&
      typeof record.token_id === 'number' &&
      typeof record.x === 'number' &&
      typeof record.y === 'number'
    ) {
      handlers.onTokenMove(record.token_id, record.x, record.y)
    }
  })

  return () => socket.close()
}
