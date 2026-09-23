import { useEffect, useState } from "react";
import { BANDS, ago, clockTime, nodeHex, setAckState } from "../live.js";

const FIELD_NAMES = {
  status: "Status",
  group_size: "Group size",
  name: "Name",
  resource_type: "Resource",
  quantity: "Quantity",
  urgency: "Urgency",
  notes: "Notes",
  severity: "Severity",
  condition_code: "Condition",
  patient_name: "Patient name",
  patient_age: "Patient age",
  orig_seq: "Original sequence",
};

export default function MessageDetail({ message: m, now, onClose, onUpdated }) {
  const [note, setNote] = useState(m.ack_note || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const band = BANDS[m.msg_type] || BANDS.ACK;

  useEffect(() => {
    setNote(m.ack_note || "");
    setError(null);
  }, [m.id, m.ack_note]);

  async function update(state) {
    setBusy(true);
    setError(null);
    try {
      onUpdated(await setAckState(m.id, state, note.trim()));
    } catch (e) {
      setError(`${e.message}. Check that the gateway is running, then try again.`);
    } finally {
      setBusy(false);
    }
  }

  const fields = Object.entries(m.fields).filter(([, v]) => v !== "" && v !== null);
  const drift = m.hp_timestamp ? Math.round(m.received_at - m.hp_timestamp) : null;

  return (
    <section className={`detail tone-${band.tone}`} aria-labelledby="detail-title">
      <div className="detail-head">
        <div>
          <p className="detail-band">{band.name}</p>
          <h2 id="detail-title">{m.summary}</h2>
          <p className="detail-where">{m.shelter}</p>
        </div>
        <button type="button" className="close" onClick={onClose} aria-label="Close details">×</button>
      </div>

      {m.verify_status === "flagged_stale" && (
        <p className="detail-warning">
          This message arrived with a sequence number far older than the Help Point's recent traffic. It passed the
          signature check, but it could be a delayed copy or a replay. Confirm with the shelter before acting.
        </p>
      )}

      <dl className="detail-fields">
        {fields.map(([k, v]) => (
          <div key={k}>
            <dt>{FIELD_NAMES[k] || k}</dt>
            <dd>{m.labels[k] ?? String(v)}</dd>
          </div>
        ))}
      </dl>

      <div className="detail-actions">
        <label htmlFor="ack-note">Note for the log</label>
        <textarea
          id="ack-note"
          rows={2}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Who is handling it, what was sent"
        />
        <div className="buttons">
          {m.ack_state !== "acknowledged" && m.ack_state !== "resolved" && (
            <button type="button" className="primary" disabled={busy} onClick={() => update("acknowledged")}>
              Acknowledge
            </button>
          )}
          {m.ack_state !== "resolved" && (
            <button type="button" disabled={busy} onClick={() => update("resolved")}>Mark resolved</button>
          )}
          {m.ack_state !== "new" && (
            <button type="button" disabled={busy} onClick={() => update("new")}>Reopen</button>
          )}
        </div>
        {m.ack_at && (
          <p className="ack-meta">
            {m.ack_state === "resolved" ? "Resolved" : "Acknowledged"} at {clockTime(m.ack_at)}. This is recorded on
            the dashboard only; the shelter is not notified.
          </p>
        )}
        {error && <p className="error" role="alert">{error}</p>}
      </div>

      <h3>Delivery</h3>
      <dl className="detail-fields provenance">
        <div><dt>Received</dt><dd>{clockTime(m.received_at)} ({ago(m.received_at, now)})</dd></div>
        <div>
          <dt>Help Point clock</dt>
          <dd>
            {m.hp_timestamp ? clockTime(m.hp_timestamp) : "not set"}
            {drift != null && Math.abs(drift) > 120 && ` (${Math.abs(drift)}s ${drift > 0 ? "behind" : "ahead"})`}
          </dd>
        </div>
        <div><dt>Help Point</dt><dd>{m.hp_id}, message #{m.seq}</dd></div>
        <div><dt>Last hop from</dt><dd>{nodeHex(m.from_node)}</dd></div>
        <div><dt>Hops</dt><dd>{m.hops ?? "unknown"}</dd></div>
        <div><dt>Signal</dt><dd>{m.snr != null ? `${m.snr} dB SNR` : "unknown"}</dd></div>
        <div><dt>Signature</dt><dd>{m.verify_status === "accepted" ? "Verified" : "Verified, old sequence"}</dd></div>
      </dl>
    </section>
  );
}
