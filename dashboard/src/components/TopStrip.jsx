import { BANDS } from "../live.js";

const TALLY_TYPES = ["MEDICAL_URGENT", "RESOURCE_REQUEST", "CHECKIN"];
const ALERT_WINDOW_S = 3600;

export default function TopStrip({ messages, events, link, health, now, activeType, onType }) {
  const open = {};
  for (const m of messages) {
    if (m.ack_state === "new") open[m.msg_type] = (open[m.msg_type] || 0) + 1;
  }
  const recentAlerts = events.filter(
    (e) => e.severity === "alert" && now / 1000 - e.received_at < ALERT_WINDOW_S,
  ).length;

  const radioUp = health?.connected;
  const radioLabel = health ? (health.radio_kind === "sim" ? "Simulator" : `Radio ${health.radio}`) : "Radio";

  return (
    <header className="top-strip">
      <div className="brand">
        <h1>MeshAid</h1>
        <span className="brand-sub">Incident Command</span>
      </div>

      <nav className="tallies" aria-label="Unacknowledged messages by type">
        {TALLY_TYPES.map((t) => (
          <button
            key={t}
            type="button"
            className={`tally tone-${BANDS[t].tone}`}
            aria-pressed={activeType === t}
            onClick={() => onType(t)}
            title={`Show only ${BANDS[t].name.toLowerCase()}`}
          >
            <span className="tally-count">{open[t] || 0}</span>
            <span className="tally-name">{BANDS[t].name}</span>
          </button>
        ))}
        <div className={`tally tally-security ${recentAlerts ? "has-alerts" : ""}`} title="Forged or unknown-sender frames rejected in the last hour">
          <span className="tally-count">{recentAlerts}</span>
          <span className="tally-name">Rejected</span>
        </div>
      </nav>

      <div className="links">
        <span className={`link link-${link}`}>
          <span className="link-dot" aria-hidden="true" />
          {link === "live" ? "Live" : link === "connecting" ? "Connecting" : "Gateway unreachable"}
        </span>
        <span className={`link ${radioUp ? "link-live" : "link-offline"}`}>
          <span className="link-dot" aria-hidden="true" />
          {radioLabel}
          {!radioUp && health ? " disconnected" : ""}
        </span>
        <time className="clock">{new Date(now).toLocaleTimeString([], { hour12: false })}</time>
      </div>
    </header>
  );
}
