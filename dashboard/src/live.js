import { useCallback, useEffect, useReducer, useRef } from "react";

// Talks to the gateway (IF-15): REST snapshot on connect, then WebSocket pushes.

async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} returned ${r.status}`);
  return r.json();
}

export async function setAckState(id, state, note) {
  const r = await fetch(`/api/messages/${id}/ack`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, note: note || null }),
  });
  if (!r.ok) throw new Error(`Couldn't update message ${id} (${r.status})`);
  return r.json();
}

const initial = {
  link: "connecting", // connecting | live | offline
  meta: null,
  health: null,
  messages: {}, // id -> message
  events: [], // newest first
  nodes: {}, // node_num -> node
  arrivals: {}, // id -> ms timestamp, for the new-message highlight
};

function reducer(state, action) {
  switch (action.type) {
    case "link":
      return { ...state, link: action.link };
    case "snapshot": {
      const messages = {};
      for (const m of action.messages) messages[m.id] = m;
      const nodes = {};
      for (const n of action.nodes) nodes[n.node_num] = n;
      return { ...state, meta: action.meta, health: action.health, messages, nodes, events: action.events };
    }
    case "health":
      return { ...state, health: action.health };
    case "message":
      return {
        ...state,
        messages: { ...state.messages, [action.data.id]: action.data },
        arrivals: { ...state.arrivals, [action.data.id]: Date.now() },
      };
    case "message_update":
      return { ...state, messages: { ...state.messages, [action.data.id]: action.data } };
    case "security_event":
      return { ...state, events: [action.data, ...state.events].slice(0, 500) };
    case "node":
      return { ...state, nodes: { ...state.nodes, [action.data.node_num]: action.data } };
    default:
      return state;
  }
}

export function useGateway() {
  const [state, dispatch] = useReducer(reducer, initial);
  const wsRef = useRef(null);

  const loadSnapshot = useCallback(async () => {
    const [meta, health, messages, events, nodes] = await Promise.all([
      getJSON("/api/meta"),
      getJSON("/api/health"),
      getJSON("/api/messages?limit=2000"),
      getJSON("/api/security-events?limit=500"),
      getJSON("/api/nodes"),
    ]);
    dispatch({ type: "snapshot", meta, health, messages, events, nodes });
  }, []);

  useEffect(() => {
    let closed = false;
    let retry = null;

    function connect() {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${proto}://${location.host}/ws`);
      wsRef.current = ws;
      ws.onopen = async () => {
        try {
          await loadSnapshot(); // resync anything missed while disconnected
          dispatch({ type: "link", link: "live" });
        } catch {
          ws.close();
        }
      };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        dispatch({ type: msg.type, data: msg.data });
      };
      ws.onclose = () => {
        if (closed) return;
        dispatch({ type: "link", link: "offline" });
        retry = setTimeout(connect, 2000);
      };
    }
    connect();

    const poll = setInterval(async () => {
      try {
        dispatch({ type: "health", health: await getJSON("/api/health") });
      } catch {
        /* link state already shows the socket is down */
      }
    }, 5000);

    return () => {
      closed = true;
      clearTimeout(retry);
      clearInterval(poll);
      wsRef.current?.close();
    };
  }, [loadSnapshot]);

  const applyUpdate = useCallback((data) => dispatch({ type: "message_update", data }), []);
  return { ...state, applyUpdate };
}

// ---- shared helpers ----------------------------------------------------

export const BANDS = {
  MEDICAL_URGENT: { name: "Medical", tone: "red" },
  RESOURCE_REQUEST: { name: "Resources", tone: "amber" },
  CHECKIN: { name: "Check-ins", tone: "green" },
  ACK: { name: "Acks", tone: "ink" },
};

export function isUrgent(m) {
  // Top level within each band: critical medical, high-urgency request, "not safe" check-in.
  return m.priority % 100 >= 30;
}

export function clockTime(epochSeconds) {
  return new Date(epochSeconds * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

export function ago(epochSeconds, nowMs = Date.now()) {
  if (epochSeconds == null) return "never";
  const s = Math.max(0, Math.round(nowMs / 1000 - epochSeconds));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function nodeHex(n) {
  return n == null ? "unknown" : `!${n.toString(16).padStart(8, "0")}`;
}
