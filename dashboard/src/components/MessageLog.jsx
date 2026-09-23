import { BANDS, ago, clockTime, isUrgent } from "../live.js";

const HIGHLIGHT_MS = 8000;
const ACK_LABEL = { new: "New", acknowledged: "Acknowledged", resolved: "Resolved" };

export default function MessageLog({ rows, now, arrivals, selectedId, onSelect, loading, anyMessages }) {
  if (loading) {
    return <p className="log-empty">Connecting to the gateway…</p>;
  }
  if (!rows.length) {
    return (
      <p className="log-empty">
        {anyMessages
          ? "No messages match these filters."
          : "No messages yet. Check-ins and requests from Help Points will appear here as they arrive over the mesh."}
      </p>
    );
  }

  return (
    <ol className="log" aria-label="Messages">
      {rows.map((m) => {
        const band = BANDS[m.msg_type] || BANDS.ACK;
        const fresh = arrivals[m.id] && now - arrivals[m.id] < HIGHLIGHT_MS && m.ack_state === "new";
        const cls = [
          "log-row",
          `tone-${band.tone}`,
          `ack-${m.ack_state}`,
          isUrgent(m) ? "urgent" : "",
          fresh && m.msg_type === "MEDICAL_URGENT" ? "fresh" : "",
          selectedId === m.id ? "selected" : "",
        ].join(" ");
        return (
          <li key={m.id}>
            <button type="button" className={cls} onClick={() => onSelect(m.id)} aria-current={selectedId === m.id}>
              <span className="stripe" aria-hidden="true" />
              <span className="row-time">
                <span className="t-abs">{clockTime(m.received_at)}</span>
                <span className="t-rel">{ago(m.received_at, now)}</span>
              </span>
              <span className="row-body">
                <span className="row-band">{band.name}</span>
                <span className="row-summary">
                  {m.summary}
                  {m.verify_status === "flagged_stale" && <span className="flag">Check with shelter</span>}
                </span>
              </span>
              <span className="row-shelter">{m.shelter}</span>
              <span className={`row-ack ack-pill-${m.ack_state}`}>{ACK_LABEL[m.ack_state]}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
