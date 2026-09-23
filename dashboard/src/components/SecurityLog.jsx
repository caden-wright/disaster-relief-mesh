import { useState } from "react";
import { ago, clockTime, nodeHex } from "../live.js";

const KIND = {
  unauthentic: "Forged signature",
  unknown_node: "Unknown Help Point",
  duplicate: "Duplicate or replay",
  malformed: "Unreadable frame",
  stale: "Old sequence number",
  rate_limited: "Over rate limit",
};

export default function SecurityLog({ events, now }) {
  const [showDuplicates, setShowDuplicates] = useState(true);
  const rows = showDuplicates ? events : events.filter((e) => e.kind !== "duplicate");

  return (
    <section className="panel security" aria-labelledby="sec-title">
      <h2 id="sec-title">
        Rejected at the gateway
        <label className="check small">
          <input type="checkbox" checked={showDuplicates} onChange={(e) => setShowDuplicates(e.target.checked)} />
          <span>Show duplicates</span>
        </label>
      </h2>
      {rows.length === 0 ? (
        <p className="panel-empty">
          Nothing rejected. Forged, replayed, or unreadable frames are blocked here and never reach the message log.
        </p>
      ) : (
        <ol className="events">
          {rows.slice(0, 200).map((e) => (
            <li key={e.id} className={`event sev-${e.severity}`}>
              <span className="event-kind">{KIND[e.kind] || e.kind}</span>
              <time className="event-time" title={ago(e.received_at, now)}>{clockTime(e.received_at)}</time>
              <span className="event-detail">
                {e.hp_id != null && <>Claimed Help Point {e.hp_id}{e.seq != null && `, #${e.seq}`}. </>}
                Via {nodeHex(e.from_node)}. {e.detail}
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
